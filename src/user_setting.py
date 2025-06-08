import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class UserSetting:
    def __init__(self, gui_inputs: Optional[dict] = None):
        self.gui_inputs = gui_inputs or {}
        
        # GUI 입력값이 있으면 사용, 없으면 .env 파일에서 로드
        if self.gui_inputs:
            self.user_id = self.gui_inputs.get('student_id')
            self.password = self.gui_inputs.get('password')
            self.RETURNZERO_CLIENT_ID = self.gui_inputs.get('returnzero_client_id')
            self.RETURNZERO_CLIENT_SECRET = self.gui_inputs.get('returnzero_client_secret')
            self.GOOGLE_API_KEY = self.gui_inputs.get('api_key')
        else:
            env_path = Path('.env')
            if env_path.exists():
                load_dotenv()
            self.user_id = os.getenv("USERID")
            self.password = os.getenv("PASSWORD")
            self.RETURNZERO_CLIENT_ID = os.getenv("RETURNZERO_CLIENT_ID")
            self.RETURNZERO_CLIENT_SECRET = os.getenv("RETURNZERO_CLIENT_SECRET")
            self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    def get_video_urls(self) -> list[str]:
        # GUI 입력값이 있으면 사용
        if self.gui_inputs.get('urls'):
            return [url.strip() for url in self.gui_inputs['urls'].split('\n') if url.strip()]
            
        # 없으면 user_settings.json에서 로드
        try:
            with open("user_settings.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return data["video"]
        except FileNotFoundError:
            print("[INFO] user_settings.json 파일을 찾을 수 없습니다.")
            return []
        except json.JSONDecodeError:
            print("[ERROR] user_settings.json 파일이 올바른 JSON 형식이 아닙니다.")
            return []
        except KeyError:
            print("[ERROR] user_settings.json 파일에 'video' 키가 없습니다.")
            return []

    def input_video_urls(self) -> list[str]:
        print("다운로드할 링크를 입력하세요. 0 또는 빈 줄을 입력하면 종료됩니다.")
        urls = []
        while True:
            url = input("링크: ")
            if url == "0" or url == "":
                break
            error = self.validate_url(url)
            if error:
                print(error)
                continue
            urls.append(url)
        return urls

    def validate_url(self, url: str) -> str:
        # return type: 빈문자열인 경우 통과
        # 아닌 경우 오류 메시지 반환
        if not url.strip().startswith("https://canvas.ssu.ac.kr/courses/"):
            return "올바른 링크가 아닙니다. 다시 입력해주세요."
        return ""

    def get_user_account(self) -> tuple[str, str]:
        return self.user_id, self.password


if __name__ == "__main__":
    result = UserSetting().get_video_urls()
    if result:
        print(f"Found {len(result)} video URLs")
    else:
        print("No video URLs found")

    for url in result:
        print(url)
