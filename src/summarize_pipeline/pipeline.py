import time
import sys
import os
from src.summarize_pipeline.summarizer import summarize_text
from pathlib import Path


class SummarizePipeline:
    def __init__(self):
        self.downloads_dir = None  # 다운로드 경로는 나중에 설정됨

    def process(self, text_path: str) -> str:
        """텍스트 요약"""
        # 파일명 추출
        filename = Path(text_path).stem
        output_path = os.path.join(self.downloads_dir, f"{filename}_summarized.txt")

        print(f"[INFO] 요약 시작: {text_path}")
        start_time = time.time()
        summary = summarize_text(text_path, "다음 강의 내용을 한국어로 자세히 요약해주세요.")

        end_time = time.time()
        print(f"[INFO] 요약 완료: {summary}")
        print(f"[INFO] 총 소요 시간: {end_time - start_time}초")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)

        print(f"[INFO] 요약 저장 완료: {output_path}")

        return output_path


if __name__ == "__main__":
    pipeline = SummarizePipeline()
    pipeline.process("downloads/037_7장_5_PEP8_3.txt")
