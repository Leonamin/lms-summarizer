"""
Google Gemini AI Provider
"""

from .base import AIProvider


class GeminiProvider(AIProvider):
    """Google Gemini API를 사용한 요약 엔진"""

    def __init__(self, api_key: str, model_name: str = None):
        from google import genai
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name or self.default_model()

    def summarize(self, text: str, prompt: str) -> str:
        full_prompt = f"{prompt}\n\n다음은 전체 텍스트입니다:\n{text}"
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=full_prompt,
        )
        return response.text

    @staticmethod
    def default_model() -> str:
        return "gemini-2.5-flash"

    @staticmethod
    def available_models() -> list[tuple[str, str]]:
        return [
            ("gemini-2.5-flash", "Gemini 2.5 Flash (추천)"),
            ("gemini-2.5-pro", "Gemini 2.5 Pro"),
            ("gemini-2.5-flash-lite", "Gemini 2.5 Flash Lite"),
        ]
