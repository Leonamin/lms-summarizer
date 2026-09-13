"""
브라우저 관련 공용 유틸리티: Chrome 기본 경로, User-Agent
"""

import sys

if sys.platform == "win32":
    DEFAULT_CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
elif sys.platform == "darwin":
    DEFAULT_CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
else:
    DEFAULT_CHROME_PATH = "/usr/bin/google-chrome"


def default_user_agent() -> str:
    """OS에 맞는 Chrome User-Agent 반환"""
    if sys.platform == "win32":
        platform = "Windows NT 10.0; Win64; x64"
    elif sys.platform == "darwin":
        platform = "Macintosh; Intel Mac OS X 10_15_7"
    else:
        platform = "X11; Linux x86_64"
    return (
        f"Mozilla/5.0 ({platform}) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
