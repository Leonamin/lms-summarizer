"""
GitHub 릴리즈 기반 업데이트 확인 유틸리티
"""

import threading
from typing import Callable

import requests
from packaging.version import Version

GITHUB_API_URL = "https://api.github.com/repos/Leonamin/lms-summarizer/releases/latest"


def check_for_update(
    current_version: str,
    on_result: Callable[[str, str, bool], None],
    timeout: int = 5,
):
    """백그라운드 스레드에서 GitHub 최신 릴리즈를 확인한다.

    Args:
        current_version: 현재 앱 버전 (e.g. "v1.7.0")
        on_result: 결과 콜백 (latest_tag, download_url, is_newer)
        timeout: HTTP 타임아웃 (초)
    """

    def _check():
        try:
            resp = requests.get(GITHUB_API_URL, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            latest_tag = data.get("tag_name", "")
            download_url = data.get("html_url", "")

            current = Version(current_version.lstrip("v"))
            latest = Version(latest_tag.lstrip("v"))
            on_result(latest_tag, download_url, latest > current)
        except Exception:
            pass  # 네트워크 오류 시 조용히 무시

    threading.Thread(target=_check, daemon=True).start()
