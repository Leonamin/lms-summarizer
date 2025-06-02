import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page

from config import load_config, config
from login import perform_login_if_needed
from video_parser import download_video, extract_video_url

# from login import perform_login_if_needed
# from video_parser import extract_video_url
# from downloader import download_video


def get_video_urls() -> list[str]:
    print("다운로드할 링크를 입력하세요. 0 또는 빈 줄을 입력하면 종료됩니다.")
    urls = []
    while True:
        url = input("링크: ")
        if url == "0" or url == "":
            break
        error = validate_url(url)
        if error:
            print(error)
            continue
        urls.append(url)
    return urls


def validate_url(url: str) -> str:
    # return type: 빈문자열인 경우 통과
    # 아닌 경우 오류 메시지 반환
    if not url.startswith("https://canvas.ssu.ac.kr/courses/"):
        return "올바른 링크가 아닙니다. 다시 입력해주세요."
    return ""


def main():
    load_config()
    urls = get_video_urls()
    print(urls)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        for url in urls:
            print(f"\n[INFO] 처리 중: {url}")
            page.goto(url)
            time.sleep(2)  # 네트워크 안정화를 위한 대기

            # 로그인 필요 여부 판단 및 처리
            if perform_login_if_needed(page, config["USERNAME"], config["PASSWORD"]):
                print("[INFO] 로그인 완료 또는 유지됨.")
            else:
                print("[INFO] 로그인 불필요.")

            # 동영상 URL 추출 시도
            video_url = extract_video_url(page)

            if video_url:
                print(f"[SUCCESS] 동영상 링크 추출됨: {video_url}")
                download_video(video_url)
            else:
                print("[WARN] 동영상 링크를 찾지 못했습니다.")

            time.sleep(1000000)
        # browser.close()


if __name__ == "__main__":
    main()
