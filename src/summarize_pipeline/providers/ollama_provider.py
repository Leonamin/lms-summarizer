"""
Ollama 로컬 LLM Provider (OpenAI SDK 호환)

Ollama가 로컬에서 실행 중일 때 http://localhost:11434/v1 엔드포인트를 통해
OpenAI SDK로 요약 요청을 보냅니다. API 키 불필요.
"""

from .base import AIProvider


class OllamaProvider(AIProvider):
    """Ollama 로컬 LLM을 사용한 요약 엔진 (API 키 불필요)"""

    DEFAULT_BASE_URL = "http://localhost:11434/v1"

    def __init__(self, api_key: str = None, model_name: str = None,
                 base_url: str = None):
        from openai import OpenAI
        self._base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.client = OpenAI(
            api_key="ollama",  # Ollama는 API 키 미사용, 더미값 필요
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
        return "qwen2.5:7b"

    @staticmethod
    def available_models() -> list[tuple[str, str]]:
        return [
            ("qwen2.5:7b", "Qwen 2.5 7B (추천)"),
            ("qwen2.5:14b", "Qwen 2.5 14B"),
            ("llama3.1:8b", "Llama 3.1 8B"),
            ("gemma3:4b", "Gemma 3 4B (경량)"),
            ("exaone3.5:7.8b", "EXAONE 3.5 7.8B (한국어 특화)"),
        ]
