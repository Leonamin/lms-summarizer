import os
import random
import string
import time
from http.client import IncompleteRead
from typing import Callable, Optional

import requests

from src.gui.core.file_manager import get_downloads_dir

_MAX_RETRIES = 3
_TIMEOUT = (10, 60)  # (connect timeout, read timeout) in seconds
_CHUNK_SIZE = 65536   # 64KB chunks (더 빠른 대용량 파일 다운로드)


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
    response = requests.get(url, stream=True, timeout=_TIMEOUT)
    response.raise_for_status()

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
