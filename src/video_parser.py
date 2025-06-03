import os
from urllib import request
from urllib.parse import urlparse
from playwright.sync_api import Page, Frame
import time


def extract_video_url(page: Page) -> str:
    # URL 디버깅
    print(f"[DEBUG] 현재 페이지 URL: {page.url}")

    video_url = None

    # Firefox에서 작동하는 네트워크 이벤트 핸들러
    def handle_request(route):
        print(f"[ROUTE] 요청 감지 - URL: {route.request.url}")
        print(f"[ROUTE] 요청 타입: {route.request.resource_type}")
        print(f"[ROUTE] 요청 헤더: {route.request.headers}")

        if "ssmovie.mp4" in route.request.url:
            print(f"[ROUTE] ssmovie.mp4 요청 감지!")
            print(f"[ROUTE] Method: {route.request.method}")
            nonlocal video_url
            video_url = route.request.url

        route.continue_()

    # 모든 요청을 가로채기 위한 라우트 핸들러 등록
    page.route("**/*", handle_request)

    try:
        # 1단계: outer iframe 진입 - 프레임이 로드될때까지 기다리기
        outer = None
        for _ in range(10):  # retry up to 10 times
            outer = page.frame(name="tool_content")
            if outer:
                print(f"[DEBUG] outer iframe 찾음 - URL: {outer.url}")
                break
            time.sleep(1)

        if not outer:
            print("[ERROR] 1단계 iframe(tool_content) 없음")
            return None

        # 2단계: inner iframe 진입
        inner = None
        all_frames = page.frames
        for frame in all_frames:
            if frame.parent_frame == outer and "commons.ssu.ac.kr" in frame.url:
                inner = frame
                print(f"[DEBUG] inner iframe 찾음 - URL: {frame.url}")
                break

        if not inner:
            print("[ERROR] 2단계 iframe(commons) 없음")
            return None

        # 2. 재생 버튼 클릭 - 재생버튼이 활성화될때까지 기다리기
        play_btn = inner.wait_for_selector(".vc-front-screen-play-btn", timeout=5000)
        if play_btn:
            play_btn.click()
            print("[INFO] 재생 버튼 클릭됨.")
        else:
            print("[WARN] 재생 버튼을 찾을 수 없음.")
            return None

        # 3. 대기 중 confirm-dialog가 나오면 확인 버튼 클릭
        try:
            confirm_dialog = inner.wait_for_selector("#confirm-dialog", timeout=2000)
            if confirm_dialog:
                cancel_btn = confirm_dialog.query_selector(
                    ".confirm-cancel-btn.confirm-btn"
                )
                if cancel_btn:
                    cancel_btn.click()
                    print("[INFO] 확인창 닫음.")
        except:
            # 확인창이 나오지 않으면 무시
            pass

        # 4. mp4 요청 기다리기 (최대 25초)
        print("[DEBUG] 비디오 URL 대기 시작")
        for i in range(50):
            if video_url:
                print(f"[DEBUG] 비디오 URL 찾음 (반복 {i}): {video_url}")
                break
            time.sleep(0.5)

        if not video_url:
            print("[DEBUG] 비디오 URL을 찾지 못했습니다.")

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


def print_frame_tree(page: Page):
    def print_frame(f: Frame, indent: int = 0):
        indent_str = "  " * indent
        print(f"{indent_str}- Frame | name: {f.name or 'None'}, url: {f.url}")
        for child in f.child_frames:
            print_frame(child, indent + 1)

    print("[DEBUG] 현재 프레임 구조:")

    root_frames = [f for f in page.frames if f.parent_frame is None]
    for frame in root_frames:
        print_frame(frame)
