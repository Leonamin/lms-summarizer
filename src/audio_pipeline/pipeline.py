import os
import time
from pathlib import Path

from src.audio_pipeline.transcriber import transcribe_audio_to_text


class AudioToTextPipeline:
    def __init__(self, sample_rate=16000, engine="whisper-cpp", model_name="base", stt_params=None, on_log=None):
        self.sample_rate = sample_rate
        self.engine = engine
        self.model_name = model_name
        self.stt_params = stt_params or {}
        self.on_log = on_log
        self.downloads_dir = None  # 다운로드 경로는 나중에 설정됨

    def convert_to_wav(self, mp4_path: str) -> str:
        """MP4 파일을 WAV로 변환하고 WAV 경로를 반환"""
        from src.audio_pipeline.converter import convert_mp4_to_wav

        filename = Path(mp4_path).stem
        wav_path = os.path.join(self.downloads_dir, f"{filename}.wav")

        print(f"[INFO] WAV 변환 시작: {mp4_path}")
        start_time = time.time()
        convert_mp4_to_wav(mp4_path, wav_path, self.sample_rate)
        elapsed = time.time() - start_time
        print(f"[DONE] WAV 변환 완료: {wav_path} ({elapsed:.1f}초)")

        return wav_path

    def transcribe(self, wav_path: str, remove_wav: bool = True) -> str:
        """WAV 파일을 텍스트로 변환하고 텍스트 파일 경로를 반환"""
        filename = Path(wav_path).stem
        txt_path = os.path.join(self.downloads_dir, f"{filename}.txt")

        print(f"[INFO] STT 변환 시작: {wav_path}")
        start_time = time.time()
        transcribe_audio_to_text(wav_path, txt_path, engine=self.engine, model_name=self.model_name, params=self.stt_params, on_log=self.on_log)
        elapsed = time.time() - start_time
        print(f"[DONE] 텍스트 저장 완료: {txt_path} ({elapsed:.1f}초)")

        if remove_wav:
            os.remove(wav_path)
            print(f"[INFO] 임시 파일 삭제됨: {wav_path}")

        return txt_path

    def process(self, mp4_path: str, remove_wav: bool = True) -> str:
        """MP4 → WAV → 텍스트 전체 파이프라인 (하위 호환성 유지)"""
        if not mp4_path.endswith(".mp4"):
            raise ValueError("mp4 파일만 처리 가능합니다.")

        print(f"[INFO] 변환 시작: {mp4_path}")
        start_time = time.time()

        wav_path = self.convert_to_wav(mp4_path)
        txt_path = self.transcribe(wav_path, remove_wav=remove_wav)

        end_time = time.time()
        print(f"[INFO] 총 소요 시간: {end_time - start_time:.1f}초")

        return txt_path
