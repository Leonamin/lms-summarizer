import time
import sys
import os
from .summarizer import summarize_text


class SummarizePipeline:
    def __init__(self):
        pass

    def process(self, txt_path: str) -> str:

        summarized_txt_path = txt_path.replace(".txt", "_summarized.txt")

        print(f"[INFO] 요약 시작: {txt_path}")
        start_time = time.time()
        # todo 프롬프트 수정 필요
        result = summarize_text(txt_path, "다음 강의 내용을 한국어로 자세히 요약해주세요.", "gemini")
        end_time = time.time()
        print(f"[INFO] 요약 완료: {result}")
        print(f"[INFO] 총 소요 시간: {end_time - start_time}초")

        with open(summarized_txt_path, "w", encoding="utf-8") as f:
            f.write(result)

        print(f"[INFO] 요약 저장 완료: {summarized_txt_path}")

        return summarized_txt_path


if __name__ == "__main__":
    pipeline = SummarizePipeline()
    pipeline.process("downloads/037_7장_5_PEP8_3.txt")
