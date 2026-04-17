import os
import time
from pathlib import Path

from src.audio_pipeline.transcriber import transcribe_audio_to_text


class AudioToTextPipeline:
    def __init__(self, sample_rate=16000, engine="faster-whisper", model_name="large-v3-turbo", stt_params=None, on_log=None):
        self.sample_rate = sample_rate
        self.engine = engine
        self.model_name = model_name
        self.stt_params = stt_params or {}
        self.on_log = on_log
        self.downloads_dir = None  # 다운로드 경로는 나중에 설정됨
        self._cached_transcriber = None  # 모델 로드 캐싱 (다중 파일 처리 시 재사용)

    def convert_to_wav(self, input_path: str) -> str:
        """오디오/비디오 파일을 WAV로 변환하고 WAV 경로를 반환"""
        from src.audio_pipeline.converter import convert_audio_to_wav

        filename = Path(input_path).stem
        wav_path = os.path.join(self.downloads_dir, f"{filename}.wav")
        os.makedirs(self.downloads_dir, exist_ok=True)

        print(f"[INFO] WAV 변환 시작: {input_path}")
        start_time = time.time()
        convert_audio_to_wav(input_path, wav_path, self.sample_rate)
        elapsed = time.time() - start_time
        print(f"[DONE] WAV 변환 완료: {wav_path} ({elapsed:.1f}초)")

        if not os.path.exists(wav_path):
            raise RuntimeError(f"WAV 파일 생성 실패: {wav_path}")

        return wav_path

    def transcribe(self, wav_path: str, remove_wav: bool = True) -> str:
        """WAV 파일을 텍스트로 변환하고 텍스트 파일 경로를 반환"""
        filename = Path(wav_path).stem
        txt_path = os.path.join(self.downloads_dir, f"{filename}.txt")
        os.makedirs(self.downloads_dir, exist_ok=True)

        print(f"[INFO] STT 변환 시작: {wav_path}")
        start_time = time.time()
        self._cached_transcriber = transcribe_audio_to_text(
            wav_path, txt_path,
            engine=self.engine, model_name=self.model_name,
            params=self.stt_params, on_log=self.on_log,
            _reuse_transcriber=self._cached_transcriber,
        )
        elapsed = time.time() - start_time
        print(f"[DONE] 텍스트 저장 완료: {txt_path} ({elapsed:.1f}초)")

        if not os.path.exists(txt_path):
            raise RuntimeError(f"텍스트 파일 생성 실패: {txt_path}")

        if remove_wav:
            os.remove(wav_path)
            print(f"[INFO] 임시 파일 삭제됨: {wav_path}")

        return txt_path

    def process(self, input_path: str, remove_wav: bool = True) -> str:
        """오디오/비디오 → WAV → 텍스트 전체 파이프라인 (하위 호환성 유지)"""
        print(f"[INFO] 변환 시작: {input_path}")
        start_time = time.time()

        wav_path = self.convert_to_wav(input_path)
        txt_path = self.transcribe(wav_path, remove_wav=remove_wav)

        end_time = time.time()
        print(f"[INFO] 총 소요 시간: {end_time - start_time:.1f}초")

        return txt_path
