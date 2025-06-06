from abc import ABC, abstractmethod
import google.generativeai as genai
import webbrowser
from openai import OpenAI
import pyperclip
import sys
import os

from user_setting import UserSetting


# def resource_path(relative_path):
#     if hasattr(sys, '_MEIPASS'):
#         return os.path.join(sys._MEIPASS, relative_path)
#     return os.path.join(os.path.abspath("."), relative_path)


def summarize_text(txt_path: str, prompt: str, engine: str = "gemini"):
    if engine == "openai":
        summarizer = OpenAISummarizer(model_name="gpt-4o")
    elif engine == "gemini":
        summarizer = GeminiSummarizer()
    elif engine == "chatgpt":
        summarizer = ChatGPTSummarizer()
    else:
        raise ValueError("지원하지 않는 엔진입니다. 'openai', 'gemini', 'chatgpt'를 지원합니다.")
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
        print(f"[DEBUG] 텍스트 파일 읽는 중: {txt_path}")
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"[DEBUG] 텍스트 길이: {len(content)}자")

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

        print("[DEBUG] OpenAI API 호출 시작...")
        try:
            response = self.client.chat.completions.create( model=self.model_name, messages=messages, temperature=0.7, max_tokens=1024 )

            print("[DEBUG] OpenAI API 응답 받음")
            summary = response.choices[0].message.content
            print(f"[DEBUG] 요약 길이: {len(summary)}자")
            return summary

        except Exception as e:
            print(f"[ERROR] OpenAI API 호출 실패: {e}")
            print(f"[ERROR] 오류 타입: {type(e).__name__}")
            return f"요약 생성 실패: {str(e)}"


class GeminiSummarizer(Summarizer):
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        user_setting = UserSetting()
        self.model_name = model_name
        genai.configure(api_key=user_setting.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(model_name)

    def summarize(self, txt_path: str, prompt: str) -> str:
        print(f"[DEBUG] 텍스트 파일 읽는 중: {txt_path}")
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"[DEBUG] 텍스트 길이: {len(content)}자")

        # 텍스트가 너무 길면 자르기 (Gemini 토큰 제한 고려)
        if len(content) > 8000:
            print(f"[WARNING] 텍스트가 너무 깁니다 ({len(content)}자). 8000자로 제한합니다.")
            content = content[:8000] + "..."

        full_prompt = f"{prompt}\n\n다음은 전체 텍스트입니다:\n{content}"

        print("[DEBUG] Google Gemini API 호출 시작...")
        try:
            response = self.model.generate_content(full_prompt)
            print("[DEBUG] Google Gemini API 응답 받음")

            summary = response.text
            print(f"[DEBUG] 요약 길이: {len(summary)}자")
            return summary

        except Exception as e:
            print(f"[ERROR] Google Gemini API 호출 실패: {e}")
            print(f"[ERROR] 오류 타입: {type(e).__name__}")
            # 오류 발생 시 기본 메시지 반환
            return f"요약 생성 실패: {str(e)}"


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
    # 기본값은 Gemini
    result = summarize_text("downloads/037_7장_5_PEP8_3.txt", "test", "gemini")
    print(result)

    # OpenAI
    # result = summarize_text("downloads/037_7장_5_PEP8_3.txt", "test", "openai")
    # print(result)

    # ChatGPT 브라우저 버전
    # summarize_text("downloads/037_7장_5_PEP8_3.txt", "test", "chatgpt")