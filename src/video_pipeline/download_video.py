import os
import random
import string
import sys
import time
from http.client import IncompleteRead
from typing import Callable, Optional

import requests

from src.gui.core.file_manager import get_downloads_dir


def _get_ssl_verify():
    """PyInstaller 번들 환경에서 SSL 인증서 경로 반환"""
    if getattr(sys, 'frozen', False):
        try:
            import certifi
            return certifi.where()
        except ImportError:
            pass
    return True

_MAX_RETRIES = 3
_TIMEOUT = (10, 60)  # (connect timeout, read timeout) in seconds
_CHUNK_SIZE = 65536   # 64KB chunks (더 빠른 대용량 파일 다운로드)

# LMS 영상 서버가 Referer 검증을 하므로 브라우저 요청과 동일한 헤더 필요
_DOWNLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Referer": "https://commons.ssu.ac.kr/",
    "Accept-Encoding": "identity;q=1, *;q=0",
    "Range": "bytes=0-",
    "Sec-Ch-Ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
}


def download_video(
    url: str,
    filename: str = None,
    save_dir: str = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> str:
    if filename is None:
        filename = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    if not filename.endswith('.mp4'):
        filename += '.mp4'

    if save_dir is None:
        save_dir = get_downloads_dir()
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, filename)

    last_error = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            _download_with_progress(url, filepath, progress_callback, attempt)
            print(f"[SUCCESS] 다운로드 완료: {filepath}")
            return os.path.abspath(filepath)

        except (IncompleteRead, requests.exceptions.ChunkedEncodingError) as e:
            last_error = e
            _remove_partial_file(filepath)
            if attempt < _MAX_RETRIES:
                wait = 2 ** attempt  # 2, 4, 8초 지수 백오프
                print(f"[WARN] 연결 끊김, {wait}초 후 재시도 ({attempt}/{_MAX_RETRIES}): {e}")
                time.sleep(wait)
            else:
                print(f"[ERROR] {_MAX_RETRIES}회 재시도 후 다운로드 실패: {e}")

        except Exception as e:
            last_error = e
            _remove_partial_file(filepath)
            print(f"[ERROR] 다운로드 실패: {e}")
            break  # 네트워크 끊김이 아닌 오류는 재시도 안 함

    raise last_error


def _download_with_progress(
    url: str,
    filepath: str,
    progress_callback: Optional[Callable[[int, int], None]],
    attempt: int,
):
    print(f"[INFO] 동영상 다운로드 중... (시도 {attempt}/{_MAX_RETRIES}): {url}")
    response = requests.get(url, headers=_DOWNLOAD_HEADERS, stream=True,
                            timeout=_TIMEOUT, verify=_get_ssl_verify())
    response.raise_for_status()

    # Range 헤더 사용 시 content-range에서 전체 크기 추출
    content_range = response.headers.get('content-range', '')
    if '/' in content_range:
        total_size = int(content_range.split('/')[-1])
    else:
        total_size = int(response.headers.get('content-length', 0))
    downloaded = 0

    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=_CHUNK_SIZE):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total_size > 0:
                    progress_callback(downloaded, total_size)


def _remove_partial_file(filepath: str):
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"[INFO] 부분 다운로드 파일 삭제: {filepath}")
        except OSError:
            pass
