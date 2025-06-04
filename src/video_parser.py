import os
from urllib.parse import urlparse
from playwright.sync_api import Page
import time
import requests


def on_request(event, shared_state: dict[str, any]):
    # ssmovie.mp4 요청 감지
    url = event["request"]["url"]
    print(f"[CDP] 요청 감지: {url}")
    global found_video_url
    if "ssmovie.mp4" in url:
        print(f"[CDP] ssmovie.mp4 요청 감지: {url}")
        shared_state["video_url"] = url


def register_cdp_video_sniffer(page: Page, shared_state: dict[str, any]):
    # CDP 핸들러 등록
    client = page.context.new_cdp_session(page)
    client.send("Network.enable")

    client.on("Network.requestWillBeSent", lambda event: on_request(event, shared_state))


def find_canvas_video_frame(page: Page):
    # iframe 탐색
    outer = None
    for _ in range(10):
        outer = page.frame(name="tool_content")
        if outer:
            print(f"[DEBUG] outer iframe 찾음 - URL: {outer.url}")
            break
        time.sleep(1)
    if not outer:
        print("[ERROR] 1단계 iframe(tool_content) 없음")
        return None

    for frame in page.frames:
        if frame.parent_frame == outer and "commons.ssu.ac.kr" in frame.url:
            print(f"[DEBUG] inner iframe 찾음 - URL: {frame.url}")
            return frame

    print("[ERROR] 2단계 iframe(commons) 없음")
    return None


def trigger_video_play(frame):
    # 버튼 클릭 및 이전 재생 위치 확인창 닫기
    play_btn = frame.wait_for_selector(
        ".vc-front-screen-play-btn", timeout=5000)
    if play_btn:
        play_btn.click()
        print("[INFO] 재생 버튼 클릭됨.")
    else:
        print("[WARN] 재생 버튼을 찾을 수 없음.")
        return

    try:
        confirm_dialog = frame.wait_for_selector(
            "#confirm-dialog", timeout=2000)
        if confirm_dialog:
            cancel_btn = confirm_dialog.query_selector(
                ".confirm-cancel-btn.confirm-btn"
            )
            if cancel_btn:
                cancel_btn.click()
                print("[INFO] 확인창 닫음.")
    except:
        pass


def extract_video_url(page: Page) -> str:
    # 페이지 진입 -> 크롬 개발자 콘솔 등록 -> iframe 진입 -> 재생 버튼 클릭 -> 이전 재생 위치 확인창 닫기 -> 비디오 URL 추출
    print(f"[DEBUG] 현재 페이지 URL: {page.url}")
    shared_state = {"video_url": None}

    register_cdp_video_sniffer(page, shared_state)
    video_frame = find_canvas_video_frame(page)
    if not video_frame:
        return None

    trigger_video_play(video_frame)

    print("[DEBUG] 비디오 URL 대기 시작")
    timeout = time.time() + 10
    while time.time() < timeout:
        result = shared_state.get("video_url")
        if result:
            print(f"[DEBUG] 비디오 URL 찾음: {result}")
            return result
        time.sleep(0.1)

    print("[DEBUG] 비디오 URL을 찾지 못했습니다.")
    return None


# ------------------------------------------------------------


def download_video(url: str, save_dir: str = "downloads"):
    try:
        os.makedirs(save_dir, exist_ok=True)
        filename = os.path.basename(urlparse(url).path)
        filepath = os.path.join(save_dir, filename)

        print(f"[INFO] 동영상 다운로드 중...: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"[SUCCESS] 다운로드 완료: {filepath}")
    except Exception as e:
        print(f"[ERROR] 다운로드 실패: {e}")
