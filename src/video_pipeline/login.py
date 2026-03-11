from typing import Callable, Optional

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError


class LoginFailedError(Exception):
    """로그인 실패 시 발생하는 예외"""
    def __init__(self, reason: str, detail: str):
        self.reason = reason  # "invalid_credentials", "sso_page_failed", "navigation_timeout", "unknown"
        self.detail = detail  # Human-readable Korean message
        super().__init__(detail)


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
        login_button = page.locator(".login_btn a")
        if await login_button.count() > 0:
            _log("[LOGIN] SSO 로그인 버튼 클릭")
            await login_button.click()
            await page.wait_for_load_state("networkidle")
            _log(f"[LOGIN] SSO 페이지 로드됨. URL: {page.url}")
        else:
            _log("[LOGIN] SSO 로그인 버튼 없음, 직접 폼 입력 시도")

        _log("[LOGIN] 로그인 폼 입력 중...")
        await page.locator("input#userid").fill(username)
        await page.locator("input#pwd").fill(password)

        _log("[LOGIN] 로그인 버튼 클릭")
        try:
            async with page.expect_navigation(wait_until="networkidle"):
                await page.locator("a.btn_login").click()
        except PlaywrightTimeoutError:
            raise LoginFailedError("navigation_timeout", "로그인 서버 응답 시간이 초과되었습니다.")

        _log(f"[LOGIN] 리디렉션 완료. URL: {page.url}")

        # DOM 기반 에러 감지
        error_el = await page.query_selector(
            ".error-message, .msg_error, .alert-danger, .login_error, #login_error_msg"
        )
        if error_el:
            error_text = (await error_el.inner_text()).strip()
            _log(f"[LOGIN] 로그인 실패 (DOM 에러): {error_text}")
            raise LoginFailedError("invalid_credentials", error_text or "아이디 또는 비밀번호가 올바르지 않습니다.")

        # URL 기반 에러 감지
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
