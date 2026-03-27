import asyncio
from abc import ABC, abstractmethod
from playwright.sync_api import Page


# ==============================================================
# 공통 헬퍼
# ==============================================================

async def find_canvas_video_frame(page: Page, shared_state: dict, log=None):
    """LMS 페이지의 중첩 iframe 구조에서 비디오 플레이어가 있는 inner iframe을 찾는다.

    iframe 구조:
    1. outer iframe (name="tool_content")
    2. inner iframe (class="xnlailvc-commons-frame", src에 "commons.ssu.ac.kr" 포함)
    """
    _log = log or print
    for _ in range(10):
        outer = page.frame(name="tool_content")
        if outer:
            _log(f"[DEBUG] outer iframe 찾음 - URL: {outer.url}")

            # 부모 페이지에서 iframe을 뷰포트로 스크롤
            iframe_el = await page.query_selector("iframe#tool_content")
            if iframe_el:
                await iframe_el.scroll_into_view_if_needed()

            try:
                title_element = await outer.wait_for_selector(".xnlailct-title", timeout=5000)
                if title_element:
                    shared_state["title"] = await title_element.text_content()
                    _log(f"[DEBUG] 제목 찾음: {shared_state['title']}")
            except Exception:
                _log("[WARN] 제목을 찾을 수 없음")
            for frame in page.frames:
                if frame.parent_frame == outer and "commons.ssu.ac.kr" in frame.url:
                    _log(f"[DEBUG] inner iframe 찾음 - URL: {frame.url}")
                    return frame
        await asyncio.sleep(1)
    _log("[ERROR] iframe 탐색 실패")
    return None


async def trigger_video_play(frame, log=None):
    """재생 버튼을 클릭한다."""
    _log = log or print
    try:
        play_btn = await frame.wait_for_selector(".vc-front-screen-play-btn", timeout=5000)
        await play_btn.click()
        _log("[INFO] 재생 버튼 클릭됨.")
    except Exception:
        _log("[WARN] 재생 버튼을 찾을 수 없음.")


async def try_dismiss_confirm_dialog(frame, resume: bool = True) -> bool:
    """이어보기 다이얼로그가 보이면 클릭한다. 클릭했으면 True.

    매 폴링마다 호출되므로 query_selector(비대기)를 사용한다.
    """
    try:
        dialog = await frame.query_selector(".confirm-msg-box")
        if not dialog:
            return False
        if not await dialog.is_visible():
            return False

        if resume:
            btn = await frame.query_selector(".confirm-ok-btn")
        else:
            btn = await frame.query_selector(".confirm-cancel-btn")

        if btn:
            await btn.click()
            label = "이어보기(예)" if resume else "처음부터(아니오)"
            print(f"[INFO] {label} 클릭됨.")
            return True
    except Exception as e:
        print(f"[DEBUG] 다이얼로그 처리 중 오류: {e}")

    return False


# ==============================================================
# 추상 베이스 클래스
# ==============================================================

class VideoUrlExtractor(ABC):
    """비디오 URL 추출 전략의 베이스 클래스."""

    @abstractmethod
    async def extract(self, page: Page, timeout: float = 60) -> tuple[str, str]:
        """페이지에서 비디오 URL과 제목을 추출한다.

        Returns:
            (video_url, title) 튜플. 실패 시 (None, None).
        """
        pass


# ==============================================================
# DOM 기반 추출 (기본 방식)
# ==============================================================

class DomVideoExtractor(VideoUrlExtractor):
    """재생 후 video/audio 요소에서 미디어 URL을 추출한다.

    LMS 콘텐츠 유형별 미디어 소스:
    - movie/mp4: video.vc-vplay-video1 (직접 .mp4 src)
    - readystream (SyncDoc): audio.vc-sdaudio-audio (슬라이드+오디오 동기화)
    """

    VIDEO_SELECTOR = "video.vc-vplay-video1"
    SYNCDOC_AUDIO_SELECTOR = "audio.vc-sdaudio-audio"
    VIDEO_URL_PATTERN = ".mp4"
    _IGNORE_PATTERNS = ("intro.mp4", "uniplayer/")

    def __init__(self, log=None):
        self._log = log or print

    def _is_valid_video_url(self, url: str) -> bool:
        """실제 강의 영상 URL인지 검증 (플레이스홀더 제외)"""
        if not url or not url.startswith("http"):
            return False
        if self.VIDEO_URL_PATTERN not in url:
            return False
        for ignore in self._IGNORE_PATTERNS:
            if ignore in url:
                return False
        return True

    async def extract(self, page: Page, timeout: float = 60) -> tuple[str, str]:
        shared_state = {"video_url": None, "title": None}

        video_frame = await find_canvas_video_frame(page, shared_state, log=self._log)
        if not video_frame:
            return None, None

        await trigger_video_play(video_frame, log=self._log)

        self._log("[DEBUG] DOM에서 비디오 URL 대기 시작")
        poll_interval = 0.5
        max_polls = int(timeout / poll_interval)
        dialog_dismissed = False
        logged_src = False
        logged_fallback = False

        for _ in range(max_polls):
            # 매 폴링마다 이어보기 다이얼로그 체크
            if not dialog_dismissed:
                dialog_dismissed = await try_dismiss_confirm_dialog(video_frame, resume=True)

            try:
                video_el = await video_frame.query_selector(self.VIDEO_SELECTOR)
                if video_el:
                    # 1) src 속성 체크 (직접 .mp4 링크)
                    src = await video_el.get_attribute("src")
                    if self._is_valid_video_url(src):
                        self._log(f"[DEBUG] DOM에서 비디오 URL 찾음: {src}")
                        shared_state["video_url"] = src
                        return src, shared_state["title"]

                    # 2) currentSrc 체크 (MediaSource/blob 또는 <source> 태그 반영)
                    current_src = await video_frame.evaluate(
                        "(sel) => { const v = document.querySelector(sel); return v ? v.currentSrc : ''; }",
                        self.VIDEO_SELECTOR,
                    )
                    if self._is_valid_video_url(current_src):
                        self._log(f"[DEBUG] currentSrc에서 비디오 URL 찾음: {current_src}")
                        shared_state["video_url"] = current_src
                        return current_src, shared_state["title"]

                    # 3) <source> 태그 체크
                    source_src = await video_frame.evaluate(
                        "(sel) => { const v = document.querySelector(sel); const s = v && v.querySelector('source'); return s ? s.src : ''; }",
                        self.VIDEO_SELECTOR,
                    )
                    if self._is_valid_video_url(source_src):
                        self._log(f"[DEBUG] <source> 태그에서 비디오 URL 찾음: {source_src}")
                        shared_state["video_url"] = source_src
                        return source_src, shared_state["title"]

                    # 진단 로그 (한번만)
                    if not logged_src:
                        self._log(f"[DEBUG] video.src={src or '(없음)'}, currentSrc={current_src or '(없음)'}, source={source_src or '(없음)'}")
                        logged_src = True

                # 4) SyncDoc(readystream) 오디오 폴백 — 슬라이드+오디오 강의
                audio_el = await video_frame.query_selector(self.SYNCDOC_AUDIO_SELECTOR)
                if audio_el:
                    audio_src = await audio_el.get_attribute("src")
                    if self._is_valid_video_url(audio_src):
                        self._log(f"[DEBUG] SyncDoc 오디오에서 URL 찾음: {audio_src}")
                        shared_state["video_url"] = audio_src
                        return audio_src, shared_state["title"]

                if not video_el and not audio_el:
                    if not logged_fallback:
                        any_video = await video_frame.query_selector("video")
                        if any_video:
                            any_src = await any_video.get_attribute("src") or "(src 없음)"
                            any_class = await any_video.get_attribute("class") or "(class 없음)"
                            self._log(f"[DEBUG] '{self.VIDEO_SELECTOR}' 없음, 다른 video 요소: class={any_class}, src={any_src[:120]}")
                            logged_fallback = True
            except Exception as e:
                self._log(f"[WARN] DOM 폴링 중 오류: {e}")

            await asyncio.sleep(poll_interval)

        self._log("[DEBUG] DOM에서 비디오 URL을 찾지 못했습니다.")
        return None, None


# ==============================================================
# CDP 기반 추출 (기본 방식)
# ==============================================================

class CdpVideoExtractor(VideoUrlExtractor):
    """CDP Network.requestWillBeSent로 .mp4 네트워크 요청을 가로채서 URL을 추출한다.

    LMS 영상 로딩 순서:
    1. HTML 요소 로드
    2. intro.mp4 다수 요청 (무시)
    3. intro 재생 (~5초) 동안 기타 리소스
    4. intro 종료 후 실제 강의 영상 .mp4 요청 → 이것을 캡처
    """

    _IGNORE_PATTERNS = ("intro.mp4", "uniplayer/")

    def __init__(self, log=None):
        self._log = log or print

    def _is_target_video(self, url: str) -> bool:
        """실제 강의 영상 URL인지 판별 (intro.mp4 등 제외)"""
        if not url or ".mp4" not in url:
            return False
        for pattern in self._IGNORE_PATTERNS:
            if pattern in url:
                return False
        return True

    async def _on_request(self, event, shared_state: dict):
        url = event["request"]["url"]
        if self._is_target_video(url) and shared_state["video_url"] is None:
            self._log(f"[CDP] 강의 영상 요청 감지: {url}")
            shared_state["video_url"] = url

    async def _register_sniffer(self, page: Page, shared_state: dict):
        client = await page.context.new_cdp_session(page)
        await client.send("Network.enable")
        client.on(
            "Network.requestWillBeSent",
            lambda e: asyncio.create_task(self._on_request(e, shared_state)),
        )

    async def extract(self, page: Page, timeout: float = 60) -> tuple[str, str]:
        shared_state = {"video_url": None, "title": None}
        await self._register_sniffer(page, shared_state)

        video_frame = await find_canvas_video_frame(page, shared_state, log=self._log)
        if not video_frame:
            return None, None

        await trigger_video_play(video_frame, log=self._log)

        self._log("[DEBUG] CDP 비디오 URL 대기 시작 (intro.mp4 이후 실제 영상 대기)")
        poll_interval = 0.5
        max_polls = int(timeout / poll_interval)
        dialog_dismissed = False

        for _ in range(max_polls):
            if not dialog_dismissed:
                dialog_dismissed = await try_dismiss_confirm_dialog(video_frame, resume=True)

            if shared_state["video_url"]:
                self._log(f"[DEBUG] CDP 비디오 URL 찾음: {shared_state['video_url']}")
                return shared_state["video_url"], shared_state["title"]
            await asyncio.sleep(poll_interval)

        self._log("[DEBUG] CDP 비디오 URL을 찾지 못했습니다.")
        return None, None


# ==============================================================
# 팩토리 함수 (진입점)
# ==============================================================

_EXTRACTORS = {
    "dom": DomVideoExtractor,
    "cdp": CdpVideoExtractor,
}


async def extract_video_url(
    page: Page,
    method: str = "cdp",
    timeout: float = 60,
    log=None,
) -> tuple[str, str]:
    """LMS 페이지에서 비디오 URL을 추출한다.

    Args:
        page: LMS 콘텐츠가 로드된 Playwright 페이지.
        method: "cdp" (기본, 권장) 또는 "dom" (fallback).
        timeout: 최대 대기 시간(초). 기본 60초.
        log: 로그 콜백 함수. 기본 print.

    Returns:
        (video_url, title) 튜플. 실패 시 (None, None).
    """
    extractor_cls = _EXTRACTORS.get(method)
    if extractor_cls is None:
        raise ValueError(
            f"Unknown extraction method '{method}'. "
            f"Supported: {list(_EXTRACTORS.keys())}"
        )

    extractor = extractor_cls(log=log)
    return await extractor.extract(page, timeout=timeout)
