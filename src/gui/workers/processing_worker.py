"""
백그라운드에서 LMS 처리 작업을 수행하는 워커 스레드
"""

import threading
import traceback
from pathlib import Path
from typing import Dict, List
from PyQt5.QtCore import QThread, pyqtSignal

from src.gui.config.constants import Messages
from src.gui.core.file_manager import create_config_files, extract_urls_from_input, ensure_downloads_directory
from src.gui.core.module_loader import check_required_modules


class CancelledException(Exception):
    """사용자가 작업을 취소했을 때 발생하는 예외"""
    pass


class ProcessingWorker(QThread):
    """백그라운드에서 LMS 처리 작업을 수행하는 워커 스레드"""

    # 시그널 정의
    log_message = pyqtSignal(str)
    processing_finished = pyqtSignal(bool, str)
    step_changed = pyqtSignal(int, str)      # (단계번호 1~3, 단계명)
    progress_updated = pyqtSignal(int, int)  # (현재 bytes, 전체 bytes)

    def __init__(self, user_inputs: Dict[str, str], modules: Dict, save_video_dir: str = None,
                 model_name: str = "gemini-2.5-flash"):
        super().__init__()
        self.user_inputs = user_inputs
        self.modules = modules
        self.save_video_dir = save_video_dir
        self.model_name = model_name
        self._cancel_event = threading.Event()

    def request_cancel(self):
        """취소 요청 (메인 스레드에서 호출)"""
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        """취소 요청 여부 확인"""
        return self._cancel_event.is_set()

    def _check_cancelled(self):
        """취소 요청 시 CancelledException 발생"""
        if self._cancel_event.is_set():
            raise CancelledException("사용자가 작업을 취소했습니다.")

    def run(self):
        """실제 처리 작업 실행"""
        try:
            self._emit_log(Messages.PROCESSING_START)

            # 모듈 검증
            if not self._validate_modules():
                return

            self._check_cancelled()

            # 설정 파일 생성
            self._create_configuration()

            self._check_cancelled()

            # 메인 처리 파이프라인 실행
            self._execute_processing_pipeline()

            # 완료 메시지
            self._emit_log(Messages.PROCESSING_COMPLETE)
            self.processing_finished.emit(True, "작업이 성공적으로 완료되었습니다.")

        except CancelledException:
            self._emit_log("⚠️ 사용자에 의해 작업이 취소되었습니다.")
            self.processing_finished.emit(False, "작업이 취소되었습니다.")

        except Exception as e:
            error_msg = f"작업 중 오류 발생: {str(e)}"
            self._emit_log(f"{Messages.MODULE_LOAD_ERROR.split()[0]} {error_msg}")
            self._emit_log(f"상세 오류:\n{traceback.format_exc()}")
            self.processing_finished.emit(False, error_msg)

    def _emit_log(self, message: str):
        """로그 메시지 출력"""
        self.log_message.emit(message)

    def _validate_modules(self) -> bool:
        """필수 모듈들이 모두 로드되었는지 확인"""
        all_loaded, missing_modules = check_required_modules(self.modules)

        if not all_loaded:
            self._emit_log(f"{Messages.MODULE_LOAD_ERROR}: {', '.join(missing_modules)}")
            self._emit_log(Messages.INSTALL_REQUIREMENTS)
            self.processing_finished.emit(False, f"필수 모듈 누락: {', '.join(missing_modules)}")
            return False

        return True

    def _create_configuration(self):
        """설정 파일들 생성"""
        self._emit_log(Messages.CONFIG_CREATING)
        create_config_files(self.user_inputs)

    def _execute_processing_pipeline(self):
        """메인 처리 파이프라인 실행"""
        # URL 목록 추출
        urls = extract_urls_from_input(self.user_inputs.get('urls', ''))

        if not urls:
            raise ValueError("처리할 URL이 없습니다.")

        # 사용자 설정 초기화 (GUI 입력값 전달)
        user_setting = self.modules['UserSetting'](self.user_inputs)

        # 1. 비디오 다운로드 파이프라인
        self._check_cancelled()
        self.step_changed.emit(1, "영상 다운로드")
        video_paths = self._download_videos(urls, user_setting)

        if not video_paths:
            raise ValueError(f"다운로드된 영상이 없습니다. ({len(urls)}개 URL 중 0개 성공)")

        # 2. 오디오를 텍스트로 변환
        self._check_cancelled()
        self.step_changed.emit(2, "음성 → 텍스트 변환")
        text_paths = self._convert_audio_to_text(video_paths)

        # 3. 텍스트 요약
        self._check_cancelled()
        self.step_changed.emit(3, "AI 요약 생성")
        self._summarize_texts(text_paths)

        # 체크박스 미선택 시 원본 영상 삭제 (강의 폴더 내 mp4만 제거)
        if not self.save_video_dir:
            self._delete_video_files(video_paths)

        # 결과 정리
        self._display_results(video_paths, text_paths)

    def _download_videos(self, urls: List[str], user_setting) -> List[str]:
        """비디오 다운로드"""
        self._emit_log(f"{Messages.VIDEO_DOWNLOADING}")
        self._emit_log(f"📋 다운로드할 링크: {len(urls)}개")

        self._last_progress_pct = -1

        def on_progress(downloaded, total):
            self.progress_updated.emit(downloaded, total)
            pct = int(downloaded / total * 100)
            if pct != self._last_progress_pct and pct % 10 == 0:
                self._last_progress_pct = pct
                mb_down = downloaded / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                self._emit_log(f"   📊 다운로드 진행: {pct}% ({mb_down:.1f}/{mb_total:.1f} MB)")

        video_pipeline = self.modules['VideoPipeline'](user_setting, progress_callback=on_progress)
        video_pipeline.downloads_dir = ensure_downloads_directory()

        self._check_cancelled()
        video_paths = video_pipeline.process_sync(urls)
        self._emit_log(f"{Messages.DOWNLOAD_COMPLETE}: {len(video_paths)}개 파일")

        # 다운로드된 파일 목록 출력
        self._emit_log("📁 다운로드된 파일들:")
        for i, filepath in enumerate(video_paths, 1):
            self._emit_log(f"   📹 ({i}) {filepath}")

        return video_paths

    def _delete_video_files(self, video_paths: List[str]):
        """처리 완료 후 원본 영상 삭제 (원본 보관 옵션 미선택 시)"""
        import os
        for filepath in video_paths:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    self._emit_log(f"🗑️ 원본 영상 삭제됨: {Path(filepath).name}")
            except Exception as e:
                self._emit_log(f"⚠️ 영상 삭제 실패 ({Path(filepath).name}): {e}")

    def _convert_audio_to_text(self, video_paths: List[str]) -> List[str]:
        """오디오를 텍스트로 변환"""
        self._emit_log(Messages.AUDIO_CONVERTING)

        # ffmpeg 경로 확인
        self._check_ffmpeg()

        audio_pipeline = self.modules['AudioToTextPipeline']()
        text_paths = []

        for i, video_path in enumerate(video_paths, 1):
            self._check_cancelled()
            try:
                # 각 비디오 파일의 디렉토리에 텍스트 저장
                audio_pipeline.downloads_dir = str(Path(video_path).parent)
                self._emit_log(f"🎤 ({i}/{len(video_paths)}) 텍스트 변환 중: {Path(video_path).name}")
                self._emit_log(f"📄 원본 파일: {video_path}")

                text_path = audio_pipeline.process(video_path)
                text_paths.append(text_path)

                self._emit_log(f"{Messages.CONVERSION_COMPLETE}: {text_path}")

            except CancelledException:
                raise
            except Exception as e:
                self._emit_log(f"{Messages.CONVERSION_FAILED} ({Path(video_path).name}): {e}")
                self._emit_log(f"[DEBUG] 오류 상세: {str(e)}")

        # 변환된 텍스트 파일 목록
        if text_paths:
            self._emit_log("📄 변환된 텍스트 파일들:")
            for i, text_path in enumerate(text_paths, 1):
                self._emit_log(f"   📝 ({i}) {text_path}")

        return text_paths

    def _summarize_texts(self, text_paths: List[str]) -> List[str]:
        """텍스트 요약"""
        self._emit_log(Messages.TEXT_SUMMARIZING)

        summarize_pipeline = self.modules['SummarizePipeline'](self.model_name)
        summary_paths = []

        for i, text_path in enumerate(text_paths, 1):
            self._check_cancelled()
            try:
                # 각 텍스트 파일의 디렉토리에 요약 저장
                summarize_pipeline.downloads_dir = str(Path(text_path).parent)
                self._emit_log(f"📝 ({i}/{len(text_paths)}) 요약 생성 중: {Path(text_path).name}")
                self._emit_log(f"📄 입력 파일: {text_path}")

                summary_path = summarize_pipeline.process(text_path)
                summary_paths.append(summary_path)

                self._emit_log(f"{Messages.SUMMARY_COMPLETE}: {summary_path}")

            except CancelledException:
                raise
            except Exception as e:
                self._emit_log(f"{Messages.SUMMARY_FAILED} ({Path(text_path).name}): {e}")
                self._emit_log(f"[DEBUG] 오류 상세: {str(e)}")

        return summary_paths

    def _check_ffmpeg(self):
        """ffmpeg 설치 확인"""
        import shutil
        import sys
        import os

        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            self._emit_log(f"🔧 ffmpeg 찾음: {ffmpeg_path}")
            return

        # .app 번들 내부의 ffmpeg 확인
        if getattr(sys, 'frozen', False):
            bundle_ffmpeg = os.path.join(sys._MEIPASS, 'ffmpeg')
            if os.path.exists(bundle_ffmpeg):
                os.environ['PATH'] = f"{os.path.dirname(bundle_ffmpeg)}:{os.environ.get('PATH', '')}"
                self._emit_log(f"🔧 번들된 ffmpeg 사용: {bundle_ffmpeg}")
                return

        # 시스템 경로 확인
        possible_paths = ['/usr/local/bin', '/opt/homebrew/bin', '/usr/bin']
        for path in possible_paths:
            if os.path.exists(os.path.join(path, 'ffmpeg')):
                os.environ['PATH'] = f"{path}:{os.environ.get('PATH', '')}"
                self._emit_log(f"🔧 ffmpeg PATH 추가: {path}")
                return

        self._emit_log("❌ ffmpeg를 찾을 수 없습니다. 설치가 필요합니다.")
        raise RuntimeError("ffmpeg가 설치되어 있지 않습니다.")

    def _display_results(self, video_paths: List[str], text_paths: List[str]):
        """결과 요약 표시"""
        self._emit_log("\n" + "="*50)

        if video_paths:
            self._emit_log("📹 다운로드된 동영상:")
            for path in video_paths:
                self._emit_log(f"   📄 {path}")

        if text_paths:
            self._emit_log("📝 변환된 텍스트:")
            for path in text_paths:
                self._emit_log(f"   📄 {path}")

        # 저장 위치 안내
        if video_paths or text_paths:
            downloads_dir = ensure_downloads_directory()
            self._emit_log(f"\n📁 모든 파일이 저장된 위치: {downloads_dir}")

        self._emit_log("="*50)
