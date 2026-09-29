"""
OpenAI 호환 엔드포인트 Provider

OpenAI 공식 API, OpenRouter, OpenCode GO 등 OpenAI API 호환 레이어를
제공하는 임의의 서버에 연결하여 요약을 수행합니다.

- /v1/responses 를 먼저 시도하고, 지원하지 않는 서버면 /v1/chat/completions로 자동 폴백합니다.
  (폴백 결과는 인스턴스에 캐시되어 이후 호출에서 재시도하지 않음)
- base_url과 model_name을 사용자가 직접 설정합니다.
  예: OpenRouter → https://openrouter.ai/api/v1
"""

from .base import AIProvider


class CustomProvider(AIProvider):
    """OpenAI 호환 커스텀 엔드포인트를 사용한 요약 엔진"""

    def __init__(self, api_key: str = None, model_name: str = None,
                 base_url: str = None, request_timeout: float = 120):
        import httpx
        from openai import OpenAI
        self._base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.client = OpenAI(
            api_key=api_key or "not-needed",
            base_url=self._base_url,
            max_retries=3, timeout=httpx.Timeout(request_timeout, connect=10),
        )
        self.model_name = model_name or self.default_model()
        self._use_responses: bool | None = None  # None = 아직 감지 안 함

    def _summarize_via_responses(self, full_prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model_name,
            input=full_prompt,
        )
        return response.output_text

    def _summarize_via_chat_completions(self, full_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": full_prompt}],
        )
        return response.choices[0].message.content

    def summarize(self, text: str, prompt: str) -> str:
        full_prompt = f"{prompt}\n\n다음은 전체 텍스트입니다:\n{text}"

        if self._use_responses is None:
            try:
                result = self._summarize_via_responses(full_prompt)
                self._use_responses = True
                return result
            except Exception as exc:
                # A timeout, auth/rate-limit/server/model error can represent a paid
                # request. Only an unsupported route permits a second API call.
                if getattr(exc, "status_code", None) not in (404, 405, 501) or getattr(exc, "code", None) == "model_not_found":
                    raise
                self._use_responses = False

        if self._use_responses:
            return self._summarize_via_responses(full_prompt)
        return self._summarize_via_chat_completions(full_prompt)

    @staticmethod
    def default_model() -> str:
        return "default"

    @staticmethod
    def available_models() -> list[tuple[str, str]]:
        return [
            ("default", "직접 입력 (예: anthropic/claude-sonnet-5)"),
        ]
