"""
Google Gemini AI Provider
"""

from .base import AIProvider


class GeminiProvider(AIProvider):
    """Google Gemini API를 사용한 요약 엔진"""

    def __init__(self, api_key: str, model_name: str = None):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name or self.default_model())

    def summarize(self, text: str, prompt: str) -> str:
        full_prompt = f"{prompt}\n\n다음은 전체 텍스트입니다:\n{text}"
        response = self.model.generate_content(full_prompt)
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
            ("gemini-2.0-flash", "Gemini 2.0 Flash"),
        ]
