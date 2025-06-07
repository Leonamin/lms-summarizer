"""
파일 관리 유틸리티
"""

import sys
import os
import json
from typing import Dict, List
from pathlib import Path


def get_resource_path(relative_path: str) -> str:
    """PyInstaller 환경에서도 작동하는 리소스 경로 반환"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def create_env_file(user_inputs: Dict[str, str]) -> None:
    """환경변수 파일 생성"""
    env_content = f"""USERID={user_inputs.get('student_id', '')}
PASSWORD={user_inputs.get('password', '')}
GOOGLE_API_KEY={user_inputs.get('api_key', '')}
"""
    with open(get_resource_path('.env'), 'w', encoding='utf-8') as f:
        f.write(env_content)


def create_user_settings_file(urls: List[str]) -> None:
    """사용자 설정 파일 생성"""
    settings = {"video": urls}
    with open(get_resource_path('user_settings.json'), 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def create_config_files(user_inputs: Dict[str, str]) -> None:
    """모든 설정 파일들 생성"""
    create_env_file(user_inputs)

    # URL 목록 추출
    url_text = user_inputs.get('urls', '').strip()
    urls = [url.strip() for url in url_text.split('\n') if url.strip()] if url_text else []

    create_user_settings_file(urls)


def ensure_downloads_directory() -> str:
    """다운로드 디렉토리 생성 및 경로 반환"""
    downloads_dir = get_resource_path("downloads")
    Path(downloads_dir).mkdir(exist_ok=True)
    return downloads_dir


def extract_urls_from_input(url_input: str) -> List[str]:
    """입력 텍스트에서 URL 목록 추출"""
    if not url_input.strip():
        return []

    urls = []
    for line in url_input.split('\n'):
        url = line.strip()
        if url and (url.startswith('http://') or url.startswith('https://')):
            urls.append(url)

    return urls


def get_downloads_dir() -> str:
    """다운로드 디렉토리 경로 반환"""
    if getattr(sys, 'frozen', False):
        # .app 번들인 경우 사용자의 Downloads 폴더 사용
        downloads = os.path.expanduser('~/Downloads/LMS-Summarizer')
    else:
        # 개발 환경인 경우 현재 디렉토리의 downloads 폴더 사용
        downloads = 'downloads'

    Path(downloads).mkdir(parents=True, exist_ok=True)
    return downloads