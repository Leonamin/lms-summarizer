"""
xAI Grok AI Provider (OpenAI SDK 호환 API)
"""

from .base import AIProvider


class GrokProvider(AIProvider):
    """xAI Grok API를 사용한 요약 엔진 (OpenAI SDK 호환)"""

    def __init__(self, api_key: str, model_name: str = None):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
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
        return "grok-3"

    @staticmethod
    def available_models() -> list[tuple[str, str]]:
        return [
            ("grok-3", "Grok 3 (추천)"),
            ("grok-3-mini", "Grok 3 Mini"),
        ]
