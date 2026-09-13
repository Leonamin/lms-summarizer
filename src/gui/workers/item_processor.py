"""
큐 워커용 항목 단위 처리기

단일 영상 파일에 대해 WAV 변환 → STT → AI 요약을 수행한다.
QueueManager의 처리 스레드에서 사용하며, ProcessingWorker의
단계별 일괄 처리 로직을 항목 단위로 재구성한 것이다.
"""

import os
import threading
import time as _time
from pathlib import Path
from typing import Callable, Dict, Optional


class CancelledException(Exception):
    """사용자가 작업을 취소했을 때 발생하는 예외"""
    pass


class ItemProcessor:
    """단일 영상 항목을 변환→STT→요약 처리하는 워커"""

    def __init__(
        self,
        modules: Dict,
        settings: Dict,
        on_log: Callable[[str], None],
        cancel_check: Optional[Callable[[], bool]] = None,
    ):
        self.modules = modules
        self.settings = settings
        self._on_log = on_log
        self._cancel_check = cancel_check or (lambda: False)

        self.user_inputs = settings['user_inputs']
        self.save_video_dir = settings.get('save_video_dir')
        self.model_name = settings['model_name']
        self.engine = settings['engine']
        self.base_url = settings.get('base_url', '')
        self.summary_prompt = settings['summary_prompt']
        self.stt_engine = settings['stt_engine']
        self.stt_model = settings['stt_model']
        self.stt_params = dict(settings.get('stt_params') or {})
        self._inject_stt_credentials()

    def _inject_stt_credentials(self):
        """클라우드 STT 엔진일 때 자격 증명을 파라미터에 주입"""
        from src.gui.core.file_manager import get_stt_api_key
        if self.stt_engine == "openai-whisper":
            self.stt_params["api_key"] = get_stt_api_key(engine="openai-whisper")
        elif self.stt_engine == "openai-compatible":
            self.stt_params["base_url"] = get_stt_api_key(engine="openai-compatible-base-url")
            self.stt_params["api_key"] = get_stt_api_key(engine="openai-compatible")
            compat_model = get_stt_api_key(engine="openai-compatible-model")
            if compat_model:
                self.stt_model = compat_model

    def _log(self, msg: str):
        try:
            self._on_log(msg)
        except Exception:
            pass  # 로그 콜백 실패가 처리 스레드를 죽이지 않도록 방어

    def _check_cancelled(self):
        if self._cancel_check():
            raise CancelledException("사용자가 작업을 취소했습니다.")

    def _interruptible(self, fn, *args, timeout=None, **kwargs):
        """블로킹 작업을 별도 스레드에서 실행하고 취소 신호 시 즉시 중단"""
        result, error = [None], [None]

        def _run():
            try:
                result[0] = fn(*args, **kwargs)
            except Exception as e:
                error[0] = e

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        start_time = _time.time() if timeout else None

        while t.is_alive():
            self._check_cancelled()
            t.join(timeout=0.5)
            if timeout and (_time.time() - start_time) > timeout:
                raise RuntimeError(
                    f"작업이 {timeout}초 내에 완료되지 않았습니다. "
                    f"GPU 메모리 부족 또는 CUDA 오류일 수 있습니다."
                )

        if error[0]:
            raise error[0]
        return result[0]

    # ── 단계별 처리 ──────────────────────────────────────

    def convert(self, video_path: str) -> str:
        """MP4 → WAV 변환"""
        audio_pipeline = self.modules['AudioToTextPipeline'](
            engine=self.stt_engine, model_name=self.stt_model,
            stt_params=self.stt_params,
        )
        audio_pipeline.downloads_dir = str(Path(video_path).parent)
        wav_path = audio_pipeline.convert_to_wav(video_path)
        if not os.path.exists(wav_path):
            raise RuntimeError(f"WAV 파일이 생성되지 않았습니다: {wav_path}")
        return wav_path

    def transcribe(self, wav_path: str) -> str:
        """WAV → 텍스트 (30분 타임아웃)"""
        audio_pipeline = self.modules['AudioToTextPipeline'](
            engine=self.stt_engine, model_name=self.stt_model,
            stt_params=self.stt_params, on_log=self._on_log,
        )
        audio_pipeline.downloads_dir = str(Path(wav_path).parent)
        text_path = self._interruptible(
            audio_pipeline.transcribe, wav_path, remove_wav=True,
            timeout=1800,
        )
        if not os.path.exists(text_path):
            raise RuntimeError(f"텍스트 파일이 생성되지 않았습니다: {text_path}")
        return text_path

    def summarize(self, text_path: str) -> str:
        """텍스트 → AI 요약"""
        is_clipboard = self.engine == "clipboard"
        if is_clipboard:
            self._write_chatbot_text(text_path)

        summarize_pipeline = self.modules['SummarizePipeline'](
            self.model_name,
            prompt=self.summary_prompt,
            engine=self.engine,
            api_key=self.user_inputs.get('api_key', ''),
            base_url=self.base_url,
        )
        summarize_pipeline.downloads_dir = str(Path(text_path).parent)
        summary_path = self._interruptible(summarize_pipeline.process, text_path)
        if not os.path.exists(summary_path):
            raise RuntimeError(f"요약 파일이 생성되지 않았습니다: {summary_path}")
        return summary_path

    def process_full(self, video_path: str,
                     on_stage: Callable[[str], None],
                     start_stage: str = "변환") -> str:
        """항목 처리: start_stage 이후 단계만 실행 (변환 → STT → 요약)

        on_stage에는 표시용 상태 문자열("변환", "STT", "요약")이 전달된다.
        start_stage: "변환" | "STT" | "요약"
        """
        stages = ["변환", "STT", "요약"]
        idx = stages.index(start_stage) if start_stage in stages else 0

        wav_path = text_path = None
        if idx <= 0:
            self._log(f"📋 WAV 변환 시작: {Path(video_path).name}")
            on_stage("변환")
            wav_path = self.convert(video_path)
            self._log(f"✅ WAV 변환 완료: {Path(wav_path).name}")
        else:
            wav_path = video_path  # 시작 파일이 이미 WAV/MP3

        self._check_cancelled()
        if idx <= 1:
            self._log(f"🎙 텍스트 변환 시작: {Path(wav_path).name}")
            on_stage("STT")
            text_path = self.transcribe(wav_path)
            self._log(f"✅ 텍스트 변환 완료: {Path(text_path).name}")
        else:
            text_path = video_path  # 시작 파일이 이미 TXT

        self._check_cancelled()
        self._log(f"🤖 요약 생성 시작: {Path(text_path).name}")
        on_stage("요약")
        summary_path = self.summarize(text_path)
        self._log(f"✅ 요약 생성 완료: {Path(summary_path).name}")

        return summary_path

    # ── 후처리 ───────────────────────────────────────────

    def finalize(self, video_path: str, url: str, summary_path: str,
                 duration_sec: float, delete_source: bool = True):
        """히스토리 저장 + 원본 영상 삭제 (옵션에 따라)

        delete_source가 False면 사용자가 직접 선택한 파일이므로 삭제하지 않는다.
        """
        from src.gui.core.file_manager import add_history_entry
        from datetime import datetime

        entry = {
            "url": url,
            "lecture_name": Path(video_path).stem,
            "file_size_mb": round(self._file_size_mb(video_path), 2),
            "duration_sec": round(duration_sec, 1),
            "summary_path": summary_path,
            "processed_at": datetime.now().isoformat(),
        }
        try:
            add_history_entry(entry)
        except Exception as e:
            self._log(f"⚠️ 히스토리 저장 실패: {e}")

        if delete_source and not self.save_video_dir:
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
                    self._log(f"원본 영상 삭제됨: {Path(video_path).name}")
            except Exception as e:
                self._log(f"⚠️ 영상 삭제 실패 ({Path(video_path).name}): {e}")

    def _write_chatbot_text(self, text_path: str):
        """클립보드 모드용 챗봇 텍스트 생성"""
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                content = f.read()
            chatbot_path = text_path.replace('.txt', '_for_chatbot.txt')
            chatbot_content = f"{self.summary_prompt}\n\n다음 텍스트를 요약해줘:\n\n{content}"
            with open(chatbot_path, 'w', encoding='utf-8') as f:
                f.write(chatbot_content)
            self._log(f"챗봇용 텍스트 저장: {Path(chatbot_path).name}")
        except Exception as e:
            self._log(f"⚠️ 챗봇용 텍스트 생성 실패: {e}")

    @staticmethod
    def _file_size_mb(path: str) -> float:
        try:
            return os.path.getsize(path) / (1024 * 1024)
        except OSError:
            return 0.0
