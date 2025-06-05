import asyncio
from playwright.sync_api import Page


async def on_request(event, shared_state: dict):
    url = event["request"]["url"]
    print(f"[CDP] 요청 감지: {url}")
    if "ssmovie.mp4" in url and shared_state["video_url"] is None:
        print(f"[CDP] ssmovie.mp4 요청 감지: {url}")
        shared_state["video_url"] = url


async def register_cdp_video_sniffer(page: Page, shared_state: dict):
    client = await page.context.new_cdp_session(page)
    await client.send("Network.enable")
    client.on("Network.requestWillBeSent",
              lambda e: asyncio.create_task(on_request(e, shared_state)))


async def find_canvas_video_frame(page: Page, shared_state: dict):
    for _ in range(10):
        outer = page.frame(name="tool_content")
        if outer:
            print(f"[DEBUG] outer iframe 찾음 - URL: {outer.url}")
            try:
                title_element = await outer.wait_for_selector(".xnlailct-title", timeout=5000)
                if title_element:
                    shared_state["title"] = await title_element.text_content()
                    print(f"[DEBUG] 제목 찾음: {shared_state['title']}")
            except:
                print("[WARN] 제목을 찾을 수 없음")
            for frame in page.frames:
                if frame.parent_frame == outer and "commons.ssu.ac.kr" in frame.url:
                    print(f"[DEBUG] inner iframe 찾음 - URL: {frame.url}")
                    return frame
        await asyncio.sleep(1)
    print("[ERROR] iframe 탐색 실패")
    return None


async def trigger_video_play(frame):
    try:
        play_btn = await frame.wait_for_selector(".vc-front-screen-play-btn", timeout=5000)
        await play_btn.click()
        print("[INFO] 재생 버튼 클릭됨.")
    except:
        print("[WARN] 재생 버튼을 찾을 수 없음.")
        return

    try:
        confirm_dialog = await frame.wait_for_selector("#confirm-dialog", timeout=2000)
        cancel_btn = await confirm_dialog.query_selector(".confirm-cancel-btn.confirm-btn")
        if cancel_btn:
            await cancel_btn.click()
            print("[INFO] 확인창 닫음.")
    except:
        pass


async def extract_video_url(page: Page) -> tuple[str, str]:
    shared_state = {"video_url": None, "title": None}
    await register_cdp_video_sniffer(page, shared_state)

    video_frame = await find_canvas_video_frame(page, shared_state)
    if not video_frame:
        return None

    await trigger_video_play(video_frame)

    print("[DEBUG] 비디오 URL 대기 시작")
    for _ in range(100):  # 최대 10초 대기 (0.1초 간격)
        if shared_state["video_url"]:
            print(f"[DEBUG] 비디오 URL 찾음: {shared_state['video_url']}")
            return shared_state["video_url"], shared_state["title"]
        await asyncio.sleep(0.1)

    print("[DEBUG] 비디오 URL을 찾지 못했습니다.")
    return None
