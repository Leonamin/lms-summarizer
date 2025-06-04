import json
import os

from dotenv import load_dotenv


class UserSetting:
    def __init__(self):
        load_dotenv()
        self.user_id = os.getenv("USERID")
        self.password = os.getenv("PASSWORD")
        self.RETURNZERO_CLIENT_ID = os.getenv("RETURNZERO_CLIENT_ID")
        self.RETURNZERO_CLIENT_SECRET = os.getenv("RETURNZERO_CLIENT_SECRET")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    def get_video_urls(self) -> list[str]:
        # user_settings.json 파일에서 'video' 블록의 리스트 가져오기
        # 파일이 없으면 빈 리스트 반환
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
        if not url.startswith("https://canvas.ssu.ac.kr/courses/"):
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
