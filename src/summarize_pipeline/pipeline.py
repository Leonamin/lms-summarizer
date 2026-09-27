import os
import time
from pathlib import Path

from src.summarize_pipeline.providers import create_provider

from src.core.prompts import DEFAULT_PROMPT as _DEFAULT_PROMPT

class SummarizePipeline:
    def __init__(
        self,
        model_name: str = "gemini-3.8-flash",
        prompt: str = None,
        engine: str = "gemini",
        api_key: str = None,
        base_url: str = None,
        output_dir: str = None,
        manual_action=None,
    ):
        self.downloads_dir = output_dir
        self.manual_action = manual_action
        self.model_name = model_name
        self.prompt = prompt or _DEFAULT_PROMPT
        self.engine = engine
        self.api_key = api_key
        self.base_url = base_url

    def process(self, text_path: str) -> str:
        """텍스트 요약"""
        # 파일명 추출
        if not self.downloads_dir:
            raise ValueError("output_dir must be explicitly supplied")
        filename = Path(text_path).stem
        output_path = os.path.join(self.downloads_dir, f"{filename}_summarized.txt")
        os.makedirs(self.downloads_dir, exist_ok=True)

        print(f"[INFO] 요약 시작: {text_path}")
        start_time = time.time()

        # 텍스트 파일 읽기
        with open(text_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Provider를 통해 요약 생성
        provider = create_provider(self.engine, api_key=self.api_key, model_name=self.model_name, base_url=self.base_url, manual_action=self.manual_action)
        summary = provider.summarize(content, self.prompt)

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
