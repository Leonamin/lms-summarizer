"""
OpenAI 호환 엔드포인트 Provider

OpenAI 공식 API, OpenRouter, OpenCode GO 등 OpenAI API 호환 레이어를
제공하는 임의의 서버에 연결하여 요약을 수행합니다.

- api_mode로 호출 방식을 정합니다.
  · auto(기본): /v1/responses 를 먼저 시도하고, 지원하지 않는 서버면
    /v1/chat/completions로 자동 폴백합니다. (폴백 결과는 인스턴스에 캐시)
  · chat: /v1/chat/completions 만 사용합니다.
  · responses: /v1/responses 만 사용합니다.
- base_url과 model_name을 사용자가 직접 설정합니다.
  예: OpenRouter → https://openrouter.ai/api/v1
"""

from .base import AIProvider


class CustomProvider(AIProvider):
    """OpenAI 호환 커스텀 엔드포인트를 사용한 요약 엔진"""

    def __init__(self, api_key: str = None, model_name: str = None,
                 base_url: str = None, request_timeout: float = 120,
                 api_mode: str = 'auto', extra_headers: dict = None):
        import httpx
        from openai import OpenAI
        self._base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        headers = self._default_headers(self._base_url, extra_headers)
        self.client = OpenAI(
            api_key=api_key or "not-needed",
            base_url=self._base_url,
            max_retries=3, timeout=httpx.Timeout(request_timeout, connect=10),
            default_headers=headers or None,
        )
        self.model_name = model_name or self.default_model()
        self.api_mode = api_mode if api_mode in ('auto', 'chat', 'responses') else 'auto'
        self._use_responses: bool | None = None  # auto에서 감지 결과 캐시

    @staticmethod
    def _default_headers(base_url: str, extra_headers: dict = None) -> dict:
        """엔드포인트별 필수 헤더를 만든다.

        OpenCode Go는 대화별 라우팅/프롬프트 캐시를 위해 x-opencode-session
        헤더를 요구하며, 없으면 400 MissingSessionID로 거부한다.
        사용자가 extra_headers로 같은 이름을 주면 그 값을 우선한다.
        """
        from urllib.parse import urlsplit
        from uuid import uuid4
        headers: dict[str, str] = {}
        host = (urlsplit(base_url).hostname or '').lower()
        if host == 'opencode.ai' or host.endswith('.opencode.ai'):
            headers['x-opencode-session'] = str(uuid4())
        if extra_headers:
            headers.update({str(k): str(v) for k, v in extra_headers.items()})
        return headers

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

        if self.api_mode == 'chat':
            return self._summarize_via_chat_completions(full_prompt)
        if self.api_mode == 'responses':
            return self._summarize_via_responses(full_prompt)

        # auto: 이미 감지됐으면 그 경로만 사용한다.
        if self._use_responses is True:
            return self._summarize_via_responses(full_prompt)
        if self._use_responses is False:
            return self._summarize_via_chat_completions(full_prompt)

        # 첫 호출: responses를 시도하고, 미지원 라우트일 때만 chat으로 폴백한다.
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
        return self._summarize_via_chat_completions(full_prompt)

    @staticmethod
    def default_model() -> str:
        return "default"

    @staticmethod
    def available_models() -> list[tuple[str, str]]:
        return [
            ("default", "직접 입력 (예: anthropic/claude-sonnet-5)"),
        ]
