"""
OpenAI AI Provider
"""

from .base import AIProvider


class OpenAIProvider(AIProvider):
    """OpenAI API를 사용한 요약 엔진"""

    def __init__(self, api_key: str, model_name: str = None, request_timeout: float = 120):
        import httpx
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, max_retries=0, timeout=httpx.Timeout(request_timeout, connect=10))
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
        return "gpt-5.6-luna"

    @staticmethod
    def available_models() -> list[tuple[str, str]]:
        return [
            ("gpt-5.6-luna", "GPT-5.6 Luna (추천, 경량)"),
            ("gpt-5.6-terra", "GPT-5.6 Terra"),
            ("gpt-5.6-sol", "GPT-5.6 Sol"),
        ]
