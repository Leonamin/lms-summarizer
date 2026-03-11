"""
Anthropic Claude AI Provider
"""

from .base import AIProvider


class ClaudeProvider(AIProvider):
    """Anthropic Claude API를 사용한 요약 엔진"""

    def __init__(self, api_key: str, model_name: str = None):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
        self.model_name = model_name or self.default_model()

    def summarize(self, text: str, prompt: str) -> str:
        full_prompt = f"{prompt}\n\n다음은 전체 텍스트입니다:\n{text}"
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=8192,
            messages=[{"role": "user", "content": full_prompt}],
        )
        return message.content[0].text

    @staticmethod
    def default_model() -> str:
        return "claude-sonnet-4-20250514"

    @staticmethod
    def available_models() -> list[tuple[str, str]]:
        return [
            ("claude-sonnet-4-20250514", "Claude Sonnet 4 (추천)"),
            ("claude-haiku-4-5-20241022", "Claude Haiku 4.5"),
        ]
