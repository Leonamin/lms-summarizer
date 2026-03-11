"""
백그라운드에서 LMS 처리 작업을 수행하는 워커 스레드
"""

import logging
import os
import sys
import threading
import traceback
from pathlib import Path
from typing import Dict, List, Callable, Optional

from src.gui.config.constants import Messages
from src.gui.core.file_manager import (
    create_config_files, extract_urls_from_input, ensure_downloads_directory,
    get_summary_prompt, get_chrome_path, get_debug_mode, get_stt_engine,
    add_history_entry, get_app_data_dir,
)
from src.gui.core.module_loader import check_required_modules


def _setup_file_logger() -> logging.Logger:
    """디버그 파일 로거 설정 (PyInstaller 환경에서 에러 추적용)"""
    logger = logging.getLogger("lms_worker")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    log_path = os.path.join(get_app_data_dir(), "debug.log")
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    return logger


class CancelledException(Exception):
    """사용자가 작업을 취소했을 때 발생하는 예외"""
    pass


class ProcessingWorker:
    """백그라운드에서 LMS 처리 작업을 수행하는 워커"""

    def __init__(
        self,
        user_inputs: Dict[str, str],
        modules: Dict,
        save_video_dir: str = None,
        model_name: str = "gemini-2.5-flash",
        engine: str = "gemini",
        on_log: Optional[Callable[[str], None]] = None,
        on_finished: Optional[Callable[[bool, str], None]] = None,
        on_step_changed: Optional[Callable[[int, str], None]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ):
        self.user_inputs = user_inputs
        self.modules = modules
        self.save_video_dir = save_video_dir
        self.model_name = model_name
        self.engine = engine
        self.summary_prompt = get_summary_prompt()
        self.chrome_path = get_chrome_path()
        self.debug_mode = get_debug_mode()
        self.stt_engine = get_stt_engine()
        self._cancel_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # 콜백
        self._on_log = on_log or (lambda msg: None)
        self._on_finished = on_finished or (lambda success, msg: None)
        self._on_step_changed = on_step_changed or (lambda step, name: None)
        self._on_progress = on_progress or (lambda cur, total: None)

    def start(self):
        """워커 스레드 시작"""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def request_cancel(self):
        """취소 요청 (메인 스레드에서 호출)"""
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def join(self, timeout: float = None):
        if self._thread:
            self._thread.join(timeout=timeout)

    def _check_cancelled(self):
        if self._cancel_event.is_set():
            raise CancelledException("사용자가 작업을 취소했습니다.")

    def _emit_log(self, message: str):
        self._file_logger.info(message)
        self._on_log(message)

    def _run(self):
        """실제 처리 작업 실행"""
        self._file_logger = _setup_file_logger()
        self._file_logger.info("=" * 60)
        self._file_logger.info(f"frozen={getattr(sys, 'frozen', False)}, "
                               f"platform={sys.platform}, "
                               f"chrome_path={self.chrome_path}")
        try:
            self._emit_log(Messages.PROCESSING_START)

            if not self._validate_modules():
                return

            self._check_cancelled()
            self._create_configuration()
            self._check_cancelled()
            self._execute_processing_pipeline()

            self._emit_log(Messages.PROCESSING_COMPLETE)
            self._on_finished(True, "작업이 성공적으로 완료되었습니다.")

        except CancelledException:
            self._emit_log("⚠️ 사용자에 의해 작업이 취소되었습니다.")
            self._on_finished(False, "작업이 취소되었습니다.")

        except Exception as e:
            error_msg = f"작업 중 오류 발생: {str(e)}"
            self._emit_log(f"❌ {error_msg}")
            self._emit_log(f"상세 오류:\n{traceback.format_exc()}")
            self._on_finished(False, error_msg)

    def _validate_modules(self) -> bool:
        all_loaded, missing_modules = check_required_modules(self.modules)
        if not all_loaded:
            self._emit_log(f"{Messages.MODULE_LOAD_ERROR}: {', '.join(missing_modules)}")
            self._emit_log(Messages.INSTALL_REQUIREMENTS)
            self._on_finished(False, f"필수 모듈 누락: {', '.join(missing_modules)}")
            return False
        return True

    def _create_configuration(self):
        self._emit_log(Messages.CONFIG_CREATING)
        create_config_files(self.user_inputs)

    def _execute_processing_pipeline(self):
        import time as _time
        urls = extract_urls_from_input(self.user_inputs.get('urls', ''))
        if not urls:
            raise ValueError("처리할 URL이 없습니다.")

        user_setting = self.modules['UserSetting'](self.user_inputs)
        pipeline_start = _time.time()

        # 단계별 성능 측정
        step_timings = {}

        # 1. 비디오 다운로드
        self._check_cancelled()
        self._on_step_changed(1, "영상 다운로드")
        step_start = _time.time()
        video_paths = self._download_videos(urls, user_setting)
        step_timings["download_sec"] = round(_time.time() - step_start, 1)

        if not video_paths:
            raise ValueError(f"다운로드된 영상이 없습니다. ({len(urls)}개 URL 중 0개 성공)")

        # 영상 파일 크기 기록 (삭제 전)
        video_sizes = {}
        for vp in video_paths:
            try:
                video_sizes[vp] = os.path.getsize(vp) / (1024 * 1024)
            except OSError:
                video_sizes[vp] = 0.0

        # 2. 오디오 → 텍스트
        self._check_cancelled()
        self._on_step_changed(2, "음성 → 텍스트 변환")
        step_start = _time.time()
        text_paths = self._convert_audio_to_text(video_paths)
        step_timings["stt_sec"] = round(_time.time() - step_start, 1)

        # 3. AI 요약
        self._check_cancelled()
        self._on_step_changed(3, "AI 요약 생성")
        step_start = _time.time()
        summary_paths = self._summarize_texts(text_paths)
        step_timings["summary_sec"] = round(_time.time() - step_start, 1)

        # 히스토리 저장
        duration_sec = _time.time() - pipeline_start
        step_timings["total_sec"] = round(duration_sec, 1)
        self._emit_log(f"⏱ 성능: 다운로드 {step_timings['download_sec']}초 | STT {step_timings['stt_sec']}초 | 요약 {step_timings['summary_sec']}초 | 전체 {step_timings['total_sec']}초")
        self._save_processing_history(urls, video_paths, video_sizes, summary_paths, duration_sec, step_timings)

        if not self.save_video_dir:
            self._delete_video_files(video_paths)

        self._display_results(video_paths, text_paths)

    def _download_videos(self, urls: List[str], user_setting) -> List[str]:
        self._emit_log(Messages.VIDEO_DOWNLOADING)
        self._emit_log(f"다운로드할 링크: {len(urls)}개")

        self._last_progress_pct = -1

        def on_progress(downloaded, total):
            self._on_progress(downloaded, total)
            pct = int(downloaded / total * 100)
            if pct != self._last_progress_pct and pct % 10 == 0:
                self._last_progress_pct = pct
                mb_down = downloaded / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                self._emit_log(f"   다운로드 진행: {pct}% ({mb_down:.1f}/{mb_total:.1f} MB)")

        video_pipeline = self.modules['VideoPipeline'](
            user_setting, progress_callback=on_progress,
            chrome_path=self.chrome_path,
            log_callback=self._emit_log,
            headless=not self.debug_mode,
        )
        video_pipeline.downloads_dir = ensure_downloads_directory()

        self._check_cancelled()
        video_paths = video_pipeline.process_sync(urls)

        failed_count = len(urls) - len(video_paths)
        if failed_count > 0:
            self._emit_log(f"⚠️ {failed_count}개 영상 다운로드 실패 (건너뜀)")
        self._emit_log(f"{Messages.DOWNLOAD_COMPLETE}: {len(video_paths)}개 파일")

        self._emit_log("다운로드된 파일들:")
        for i, filepath in enumerate(video_paths, 1):
            self._emit_log(f"   ({i}) {filepath}")

        return video_paths

    def _delete_video_files(self, video_paths: List[str]):
        import os
        for filepath in video_paths:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    self._emit_log(f"원본 영상 삭제됨: {Path(filepath).name}")
            except Exception as e:
                self._emit_log(f"⚠️ 영상 삭제 실패 ({Path(filepath).name}): {e}")

    def _convert_audio_to_text(self, video_paths: List[str]) -> List[str]:
        self._emit_log(Messages.AUDIO_CONVERTING)

        audio_pipeline = self.modules['AudioToTextPipeline'](engine=self.stt_engine)
        self._emit_log(f"STT 엔진: {self.stt_engine}")
        text_paths = []

        for i, video_path in enumerate(video_paths, 1):
            self._check_cancelled()
            try:
                audio_pipeline.downloads_dir = str(Path(video_path).parent)
                self._emit_log(f"({i}/{len(video_paths)}) 텍스트 변환 중: {Path(video_path).name}")

                text_path = audio_pipeline.process(video_path)
                text_paths.append(text_path)
                self._emit_log(f"{Messages.CONVERSION_COMPLETE}: {text_path}")

            except CancelledException:
                raise
            except Exception as e:
                self._emit_log(f"{Messages.CONVERSION_FAILED} ({Path(video_path).name}): {e}")

        if text_paths:
            self._emit_log("변환된 텍스트 파일들:")
            for i, text_path in enumerate(text_paths, 1):
                self._emit_log(f"   ({i}) {text_path}")

        return text_paths

    def _summarize_texts(self, text_paths: List[str]) -> List[str]:
        self._emit_log(Messages.TEXT_SUMMARIZING)
        self._emit_log(f"AI 엔진: {self.engine} / 모델: {self.model_name}")

        is_clipboard = self.engine == "clipboard"
        if is_clipboard:
            self._emit_log("클립보드 모드: 프롬프트가 클립보드에 복사되고 외부 챗봇이 열립니다.")

        api_key = self.user_inputs.get('api_key', '')
        summarize_pipeline = self.modules['SummarizePipeline'](
            self.model_name,
            prompt=self.summary_prompt,
            engine=self.engine,
            api_key=api_key,
        )
        summary_paths = []

        for i, text_path in enumerate(text_paths, 1):
            self._check_cancelled()
            try:
                summarize_pipeline.downloads_dir = str(Path(text_path).parent)
                self._emit_log(f"({i}/{len(text_paths)}) 요약 생성 중: {Path(text_path).name}")

                # 클립보드 모드: 챗봇용 텍스트 파일도 생성
                if is_clipboard:
                    self._write_chatbot_text(text_path)

                summary_path = summarize_pipeline.process(text_path)
                summary_paths.append(summary_path)
                self._emit_log(f"{Messages.SUMMARY_COMPLETE}: {summary_path}")

            except CancelledException:
                raise
            except Exception as e:
                self._emit_log(f"{Messages.SUMMARY_FAILED} ({Path(text_path).name}): {e}")

        return summary_paths

    def _write_chatbot_text(self, text_path: str):
        """클립보드 모드에서 챗봇에 붙여넣기용 텍스트 파일 생성"""
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                content = f.read()
            chatbot_path = text_path.replace('.txt', '_for_chatbot.txt')
            chatbot_content = f"{self.summary_prompt}\n\n다음 텍스트를 요약해줘:\n\n{content}"
            with open(chatbot_path, 'w', encoding='utf-8') as f:
                f.write(chatbot_content)
            self._emit_log(f"챗봇용 텍스트 저장: {Path(chatbot_path).name}")
        except Exception as e:
            self._emit_log(f"⚠️ 챗봇용 텍스트 생성 실패: {e}")


    def _save_processing_history(
        self, urls: List[str], video_paths: List[str],
        video_sizes: Dict[str, float], summary_paths: List[str],
        duration_sec: float, step_timings: Dict[str, float] = None,
    ):
        """처리 완료된 강의 히스토리를 저장"""
        from datetime import datetime
        timestamp = datetime.now().isoformat()

        for i, url in enumerate(urls):
            video_path = video_paths[i] if i < len(video_paths) else None
            summary_path = summary_paths[i] if i < len(summary_paths) else None

            entry = {
                "url": url,
                "lecture_name": Path(video_path).stem if video_path else "",
                "file_size_mb": round(video_sizes.get(video_path, 0.0), 2),
                "duration_sec": round(duration_sec, 1),
                "summary_path": summary_path or "",
                "processed_at": timestamp,
                "step_timings": step_timings or {},
            }
            try:
                add_history_entry(entry)
            except Exception as e:
                self._emit_log(f"⚠️ 히스토리 저장 실패: {e}")

    def _display_results(self, video_paths: List[str], text_paths: List[str]):
        self._emit_log("\n" + "=" * 50)

        if video_paths:
            self._emit_log("다운로드된 동영상:")
            for path in video_paths:
                self._emit_log(f"   {path}")

        if text_paths:
            self._emit_log("변환된 텍스트:")
            for path in text_paths:
                self._emit_log(f"   {path}")

        if video_paths or text_paths:
            downloads_dir = ensure_downloads_directory()
            self._emit_log(f"\n모든 파일이 저장된 위치: {downloads_dir}")

        self._emit_log("=" * 50)
