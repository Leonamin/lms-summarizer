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
        return "gemini-3.8-flash"

    @staticmethod
    def available_models() -> list[tuple[str, str]]:
        return [
            ("gemini-3.8-flash", "Gemini 3.8 Flash (추천)"),
            ("gemini-3.6-flash", "Gemini 3.6 Flash"),
            ("gemini-3.1-pro-preview", "Gemini 3.1 Pro"),
        ]
