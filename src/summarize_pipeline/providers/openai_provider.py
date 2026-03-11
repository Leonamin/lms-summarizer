"""
OpenAI AI Provider
"""

from .base import AIProvider


class OpenAIProvider(AIProvider):
    """OpenAI API를 사용한 요약 엔진"""

    def __init__(self, api_key: str, model_name: str = None):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name or self.default_model()

    def summarize(self, text: str, prompt: str) -> str:
        full_prompt = f"{prompt}\n\n다음은 전체 텍스트입니다:\n{text}"
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": full_prompt}],
        )
        return response.choices[0].message.content

    @staticmethod
    def default_model() -> str:
        return "gpt-5.4"

    @staticmethod
    def available_models() -> list[tuple[str, str]]:
        return [
            ("gpt-5.4", "GPT-5.4 (추천)"),
            ("gpt-5-mini-2025-08-07", "GPT-5 Mini"),
            ("gpt-4o", "GPT-4o"),
            ("gpt-4o-mini", "GPT-4o Mini"),
        ]
