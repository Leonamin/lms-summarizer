"""
Custom OpenAI 호환 엔드포인트 Provider

LM Studio, vLLM, text-generation-webui, 또는 임의의 OpenAI API 호환 서버에
연결하여 요약을 수행합니다. base_url과 model_name을 사용자가 직접 설정.
"""

from .base import AIProvider


class CustomProvider(AIProvider):
    """OpenAI 호환 커스텀 엔드포인트를 사용한 요약 엔진"""

    def __init__(self, api_key: str = None, model_name: str = None,
                 base_url: str = None):
        from openai import OpenAI
        self._base_url = (base_url or "http://localhost:8080/v1").rstrip("/")
        self.client = OpenAI(
            api_key=api_key or "not-needed",
            base_url=self._base_url,
        )
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
        return "default"

    @staticmethod
    def available_models() -> list[tuple[str, str]]:
        return [
            ("default", "기본 모델"),
        ]
