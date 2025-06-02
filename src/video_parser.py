import os
from urllib import request
from urllib.parse import urlparse
from playwright.sync_api import Page
import time


def extract_video_url(page: Page) -> str:
    video_url = None

    def handle_request(request):
        nonlocal video_url
        if "ssmovie.mp4" in request.url:
            video_url = request.url

    # 네트워크 요청 감지 등록
    page.on("request", handle_request)

    time.sleep(10)

    try:
        # 1. 재생 버튼 클릭
        play_btn = page.query_selector(".vc-front-screen-play-btn")
        if play_btn:
            play_btn.click()
            print("[INFO] 재생 버튼 클릭됨.")
        else:
            print("[WARN] 재생 버튼을 찾을 수 없음.")
            return None

        # 2. 대기 중 confirm-dialog가 나오면 확인 버튼 클릭
        time.sleep(2)
        confirm_dialog = page.query_selector("#confirm-dialog")
        if confirm_dialog:
            cancel_btn = confirm_dialog.query_selector(
                ".confirm-cancel-btn.confirm-btn"
            )
            if cancel_btn:
                cancel_btn.click()
                print("[INFO] 확인창 닫음.")

        # 3. mp4 요청 기다리기 (최대 5초)
        for _ in range(10):
            if video_url:
                break
            time.sleep(0.5)

    except Exception as e:
        print(f"[ERROR] 동영상 추출 중 예외 발생: {e}")

    return video_url


def download_video(url: str, save_dir: str = "downloads"):
    try:
        os.makedirs(save_dir, exist_ok=True)
        filename = os.path.basename(urlparse(url).path)
        filepath = os.path.join(save_dir, filename)

        print(f"[INFO] 동영상 다운로드 중...: {url}")
        response = request.get(url, stream=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"[SUCCESS] 다운로드 완료: {filepath}")
    except Exception as e:
        print(f"[ERROR] 다운로드 실패: {e}")
