from abc import ABC, abstractmethod
import webbrowser
from openai import OpenAI

import pyperclip

from user_setting import UserSetting


def summarize_text(txt_path: str, prompt: str, engine: str = "openai"):
    if engine == "openai":
        summarizer = OpenAISummarizer(model_name="gpt-4o")
    elif engine == "chatgpt":
        summarizer = ChatGPTSummarizer()
    else:
        raise ValueError("지원하지 않는 엔진입니다")
    return summarizer.summarize(txt_path, prompt)


class Summarizer(ABC):
    @abstractmethod
    def summarize(self, txt_path: str, prompt: str) -> str:
        pass


class OpenAISummarizer(Summarizer):
    def __init__(self, model_name: str = "gpt-4o"):
        user_setting = UserSetting()
        self.model_name = model_name
        self.client = OpenAI(api_key=user_setting.OPENAI_API_KEY)

    def summarize(self, txt_path: str, prompt: str) -> str:
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 길이에 따라 메시지를 조각낼 수도 있음 (지금은 단순 버전)
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes Korean transcripts.",
            },
            {
                "role": "user",
                "content": f"{prompt}\n\n다음은 전체 텍스트입니다:\n{content}",
            },
        ]

        response = self.client.chat.completions.create(
            model=self.model_name, messages=messages, temperature=0.7, max_tokens=1024
        )

        summary = response.choices[0].message.content
        return summary


class ChatGPTSummarizer(Summarizer):
    def __init__(self):
        self.chat_url = "https://chat.openai.com/chat"

    def summarize(self, txt_path: str, prompt: str):
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()

        final_prompt = f"{prompt}\n\n다음 텍스트를 요약해줘:\n\n{content}"

        pyperclip.copy(final_prompt)  # 클립보드에 복사
        print(
            "[INFO] 프롬프트가 클립보드에 복사되었습니다. 브라우저로 이동 후 붙여넣기 하세요."
        )
        webbrowser.open(self.chat_url)


if __name__ == "__main__":
    result = summarize_text("downloads/037_7장_5_PEP8_3.txt", "test", "openai")
    print(result)
    # summarize_text("downloads/037_7장_5_PEP8_3.txt", "test", "chatgpt")
