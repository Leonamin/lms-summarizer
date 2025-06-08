"""
파일 관리 유틸리티
"""

import sys
import os
import json
from typing import Dict, List
from pathlib import Path


def get_app_data_dir() -> str:
    """애플리케이션 데이터 디렉토리 경로 반환"""
    if getattr(sys, 'frozen', False):
        # .app 번들 내부
        base_path = os.path.dirname(sys.executable)
    else:
        # 개발 환경
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return base_path


def get_user_home_dir() -> str:
    """사용자 홈 디렉토리 경로 반환"""
    return os.path.expanduser("~")


def get_default_downloads_dir() -> str:
    """기본 다운로드 디렉토리 경로 반환"""
    return os.path.join(get_user_home_dir(), "Documents", "LMS-Summarizer")


def get_settings_path() -> str:
    """설정 파일 경로 반환"""
    return os.path.join(get_app_data_dir(), "settings.json")


def load_settings() -> Dict:
    """설정 파일 로드"""
    settings_path = get_settings_path()
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"downloads_dir": get_default_downloads_dir()}


def save_settings(settings: Dict) -> None:
    """설정 파일 저장"""
    settings_path = get_settings_path()
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def get_resource_path(relative_path: str) -> str:
    """PyInstaller 환경에서도 작동하는 리소스 경로 반환"""
    if getattr(sys, 'frozen', False):
        # PyInstaller로 번들된 환경
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller 임시 디렉토리
            base_path = sys._MEIPASS
        else:
            # .app 번들 내부
            base_path = os.path.dirname(sys.executable)
        return os.path.join(base_path, relative_path)
    # 개발 환경
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), relative_path)


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
    settings = load_settings()
    downloads_dir = settings.get("downloads_dir", get_default_downloads_dir())
    Path(downloads_dir).mkdir(parents=True, exist_ok=True)
    return downloads_dir


def set_downloads_directory(path: str) -> None:
    """다운로드 디렉토리 설정"""
    settings = load_settings()
    settings["downloads_dir"] = path
    save_settings(settings)


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