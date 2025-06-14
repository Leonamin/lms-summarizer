import os
import random
import string
import requests
from src.gui.core.file_manager import get_downloads_dir


def download_video(url: str, filename: str = None) -> str:
    if filename is None:
        # 랜덤 알파벳 8자리
        filename = ''.join(random.choices(
            string.ascii_letters + string.digits, k=8))

    # 파일 확장자 추가
    if not filename.endswith('.mp4'):
        filename += '.mp4'

    try:
        save_dir = get_downloads_dir()
        filepath = os.path.join(save_dir, filename)

        print(f"[INFO] 동영상 다운로드 중...: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"[SUCCESS] 다운로드 완료: {filepath}")
        return os.path.abspath(filepath)
    except Exception as e:
        print(f"[ERROR] 다운로드 실패: {e}")
        raise e
