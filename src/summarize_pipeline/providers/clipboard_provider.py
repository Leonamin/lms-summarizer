"""
클립보드 기반 Provider (API 키 없이 사용)

기존 ChatGPTSummarizer의 클립보드 복사 + 브라우저 열기 패턴을 일반화합니다.
ChatGPT, Claude 웹, Grok 웹 등 다양한 챗봇으로 확장 가능합니다.
"""

import pyperclip
import webbrowser

from .base import AIProvider


CHATBOT_URLS = {
    "gemini-web": "https://gemini.google.com/app",
    "chatgpt": "https://chatgpt.com/",
    "claude-web": "https://claude.ai/",
    "grok-web": "https://grok.com/",
}


class ClipboardProvider(AIProvider):
    """클립보드 복사 + 외부 챗봇 브라우저 열기 방식의 Provider"""

    def __init__(self, target: str = "chatgpt", **kwargs):
        self.target = target
        self.chat_url = CHATBOT_URLS.get(target, CHATBOT_URLS["chatgpt"])

    def summarize(self, text: str, prompt: str) -> str:
        final_prompt = f"{prompt}\n\n다음 텍스트를 요약해줘:\n\n{text}"
        pyperclip.copy(final_prompt)
        webbrowser.open(self.chat_url)
        return (
            f"[클립보드 모드] 프롬프트가 클립보드에 복사되었습니다. "
            f"{self.chat_url} 에서 붙여넣기 하세요."
        )

    @staticmethod
    def default_model() -> str:
        return "chatgpt"

    @staticmethod
    def available_models() -> list[tuple[str, str]]:
        return [
            ("gemini-web", "Gemini (웹)"),
            ("chatgpt", "ChatGPT (웹)"),
            ("claude-web", "Claude (웹)"),
            ("grok-web", "Grok (웹)"),
        ]
