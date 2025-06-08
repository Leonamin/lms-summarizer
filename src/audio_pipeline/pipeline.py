import time
from src.audio_pipeline.converter import convert_mp4_to_wav
from src.audio_pipeline.transcriber import transcribe_wav_to_text
import os
from pathlib import Path


class AudioToTextPipeline:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.downloads_dir = None  # 다운로드 경로는 나중에 설정됨

    def process(self, mp4_path: str, remove_wav: bool = True) -> str:
        # return txt_path
        if not mp4_path.endswith(".mp4"):
            raise ValueError("mp4 파일만 처리 가능합니다.")

        # 파일명 추출
        filename = Path(mp4_path).stem
        txt_path = os.path.join(self.downloads_dir, f"{filename}.txt")

        print(f"[INFO] 변환 시작: {mp4_path}")
        start_time = time.time()
        wav_path = os.path.join(self.downloads_dir, f"{filename}.wav")
        convert_mp4_to_wav(mp4_path, wav_path, self.sample_rate)
        print(f"[INFO] 텍스트 변환 시작: {wav_path}")
        transcribe_wav_to_text(wav_path, txt_path)
        print(f"[DONE] 텍스트 저장 완료: {txt_path}")
        end_time = time.time()
        print(f"[INFO] 총 소요 시간: {end_time - start_time}초")

        # 중간 파일인 wav 삭제
        if remove_wav:
            os.remove(wav_path)
            print(f"[INFO] 임시 파일 삭제됨: {wav_path}")

        return txt_path
