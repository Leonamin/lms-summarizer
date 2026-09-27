"""
AI Provider 패키지

다양한 AI 엔진을 통합하는 Provider 인터페이스를 제공합니다.
"""

from .base import AIProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .claude_provider import ClaudeProvider
from .grok_provider import GrokProvider
from .clipboard_provider import ClipboardProvider
from .custom_provider import CustomProvider

# 엔진 이름 → Provider 클래스 매핑
ENGINE_REGISTRY: dict[str, type[AIProvider]] = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
    "grok": GrokProvider,
    "custom": CustomProvider,
}

# 엔진 이름 → API 키 설정 필드명 매핑
ENGINE_API_KEY_MAP: dict[str, str] = {
    "gemini": "GOOGLE_API_KEY",
    "openai": "OPENAI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "grok": "XAI_API_KEY",
    # custom: 키 선택사항 (서버에 따라 불필요)
}


def create_provider(engine: str, api_key: str = None, model_name: str = None,
                    base_url: str = None, manual_action=None) -> AIProvider:
    """엔진 이름으로 Provider 인스턴스를 생성하는 팩토리 함수

    Args:
        engine: 엔진 이름 ("gemini", "openai", "claude", "grok", "custom", "clipboard")
        api_key: API 키 (clipboard에서는 불필요, custom에서는 선택사항)
        model_name: 모델명 (None이면 기본 모델 사용)
        base_url: 엔드포인트 URL (custom에서 사용)

    Returns:
        AIProvider 인스턴스
    """
    if engine == "clipboard":
        return ClipboardProvider(target=model_name or "chatgpt", on_ready=manual_action)

    cls = ENGINE_REGISTRY.get(engine)
    if not cls:
        raise ValueError(f"지원하지 않는 엔진: {engine}")

    kwargs = {"api_key": api_key, "model_name": model_name or cls.default_model()}
    # custom에만 base_url 전달 (다른 Provider는 파라미터를 무시)
    if base_url and engine == "custom":
        kwargs["base_url"] = base_url
    return cls(**kwargs)


__all__ = [
    "AIProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "ClaudeProvider",
    "GrokProvider",
    "ClipboardProvider",
    "CustomProvider",
    "ENGINE_REGISTRY",
    "ENGINE_API_KEY_MAP",
    "create_provider",
]
