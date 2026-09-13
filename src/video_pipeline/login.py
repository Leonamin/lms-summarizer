from typing import Callable, Optional

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError


class LoginFailedError(Exception):
    """로그인 실패 시 발생하는 예외"""
    def __init__(self, reason: str, detail: str):
        self.reason = reason  # "invalid_credentials", "sso_page_failed", "navigation_timeout", "unknown"
        self.detail = detail  # Human-readable Korean message
        super().__init__(detail)


async def _navigate_and_wait(page: Page, click_coro, log: Callable[[str], None],
                             timeout: int = 30000):
    """클릭 후 네비게이션 대기 헬퍼"""
    try:
        async with page.expect_navigation(wait_until="networkidle", timeout=timeout):
            await click_coro
    except PlaywrightTimeoutError:
        # 네비게이션 이벤트를 놓쳤을 수 있으므로 상태 확인 후 재시도
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except PlaywrightTimeoutError:
            pass


async def perform_login_if_needed(
    page: Page, username: str, password: str,
    log: Optional[Callable[[str], None]] = None,
) -> bool:
    _log = log or (lambda msg: print(msg))

    _log(f"[LOGIN] 현재 URL: {page.url}")
    if "login" not in page.url:
        return False

    _log("[LOGIN] 로그인 페이지 감지됨. 로그인 시도 중...")

    try:
        # ── 1단계: 사이트 선택 (discovery 페이지) ──────────────
        # "로그인 할 사이트를 선택해 주세요" 페이지에서 숭실대학교 선택
        ssu_site_btn = page.locator(".btn-ssu-main")
        if await ssu_site_btn.count() > 0:
            _log("[LOGIN] 사이트 선택 페이지 감지. '숭실대학교' 클릭")
            await _navigate_and_wait(page, ssu_site_btn.click(), log)
            _log(f"[LOGIN] 이동 완료. URL: {page.url}")

        # ── 2단계: 로그인 방식 선택 (gw.php) ──────────────────
        # "통합 로그인" 버튼 클릭 → smartid.ssu.ac.kr 이동
        sso_btn = page.locator(".login_btn a")
        if await sso_btn.count() > 0:
            btn_text = (await sso_btn.first.inner_text()).strip()
            _log(f"[LOGIN] '{btn_text}' 클릭")
            await _navigate_and_wait(page, sso_btn.first.click(), log)
            _log(f"[LOGIN] 이동 완료. URL: {page.url}")

        # ── 3단계: 통합 로그인 폼 입력 (smartid.ssu.ac.kr) ────
        userid_input = page.locator("input#userid")
        if await userid_input.count() == 0:
            _log("[LOGIN] 로그인 폼을 찾을 수 없음")
            raise LoginFailedError("sso_page_failed", "로그인 페이지 구조가 예상과 다릅니다. 스크린샷과 로그를 확인해주세요.")

        _log("[LOGIN] 로그인 폼 입력 중...")
        await userid_input.fill(username)
        await page.locator("input#pwd").fill(password)

        _log("[LOGIN] 로그인 버튼 클릭")
        await _navigate_and_wait(page, page.locator("a.btn_login").click(), log,
                                 timeout=60000)

        _log(f"[LOGIN] 리디렉션 완료. URL: {page.url}")

        # DOM 기반 에러 감지
        error_el = await page.query_selector(
            ".error-message, .msg_error, .alert-danger, .login_error, #login_error_msg"
        )
        if error_el:
            error_text = (await error_el.inner_text()).strip()
            _log(f"[LOGIN] 로그인 실패 (DOM 에러): {error_text}")
            raise LoginFailedError("invalid_credentials", error_text or "아이디 또는 비밀번호가 올바르지 않습니다.")

        # URL 기반 에러 감지 — smartid/sso 페이지에 머물러 있으면 실패
        if "smartid.ssu.ac.kr" in page.url or "sso" in page.url.lower().split("/")[2]:
            _log("[LOGIN] 로그인 실패. 아이디/비밀번호 확인 필요.")
            raise LoginFailedError("invalid_credentials", "아이디 또는 비밀번호가 올바르지 않습니다.")

        if "login" in page.url:
            _log("[LOGIN] 로그인 실패. 아이디/비밀번호 확인 필요.")
            raise LoginFailedError("invalid_credentials", "아이디 또는 비밀번호가 올바르지 않습니다.")

        await page.wait_for_load_state("networkidle")
        _log(f"[LOGIN] 최종 페이지 로드 완료. URL: {page.url}")

        return True

    except LoginFailedError:
        raise

    except Exception as e:
        _log(f"[LOGIN] 예외 발생: {type(e).__name__}: {e}")
        raise LoginFailedError("unknown", f"로그인 중 예기치 않은 오류가 발생했습니다: {e}")
