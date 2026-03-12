"""
파일 관리 유틸리티
"""

import sys
import os
import json
from typing import Dict, List
from pathlib import Path


def get_app_data_dir() -> str:
    """애플리케이션 데이터 디렉토리 경로 반환 (항상 쓰기 가능한 경로)"""
    if sys.platform == 'darwin':
        base_path = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'LMS-Summarizer')
    elif sys.platform == 'win32':
        base_path = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'LMS-Summarizer')
    else:
        base_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'LMS-Summarizer')
    os.makedirs(base_path, exist_ok=True)
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


def save_settings(settings: Dict) -> bool:
    """설정 파일 저장. 성공 시 True, 실패 시 False 반환."""
    settings_path = get_settings_path()
    try:
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except OSError as e:
        print(f"[WARNING] 설정 파일 저장 실패 ({settings_path}): {e}")
        return False


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
    with open(os.path.join(get_app_data_dir(), '.env'), 'w', encoding='utf-8') as f:
        f.write(env_content)


def create_user_settings_file(urls: List[str]) -> None:
    """사용자 설정 파일 생성"""
    settings = {"video": urls}
    with open(os.path.join(get_app_data_dir(), 'user_settings.json'), 'w', encoding='utf-8') as f:
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


_PERSISTABLE_FIELDS = ['student_id', 'api_key', 'ai_model', 'ai_engine']


def save_user_inputs(inputs: Dict[str, str]) -> None:
    """사용자 입력값을 설정 파일에 저장 (비밀번호 제외)

    API 키는 엔진별로 분리하여 저장합니다.
    예: api_keys = {"gemini": "...", "openai": "...", ...}
    """
    settings = load_settings()
    saved = {k: inputs[k] for k in _PERSISTABLE_FIELDS if k in inputs}

    # 엔진별 API 키 저장
    engine = inputs.get('ai_engine', 'gemini')
    api_key = inputs.get('api_key', '')
    api_keys = settings.get('api_keys', {})
    if api_key:
        api_keys[engine] = api_key
    saved['api_keys'] = api_keys

    settings['user_inputs'] = saved
    settings['api_keys'] = api_keys
    save_settings(settings)


def load_user_inputs() -> Dict[str, str]:
    """저장된 사용자 입력값 로드

    마이그레이션: 기존 api_key만 저장된 경우 gemini 키로 처리합니다.
    """
    settings = load_settings()
    saved = settings.get('user_inputs', {})

    # 마이그레이션: 기존 api_key가 있고 api_keys가 없으면 gemini 키로 간주
    api_keys = settings.get('api_keys', saved.get('api_keys', {}))
    if not api_keys and saved.get('api_key'):
        api_keys = {"gemini": saved['api_key']}

    # 현재 엔진에 맞는 API 키 복원
    engine = saved.get('ai_engine', 'gemini')
    if api_keys.get(engine):
        saved['api_key'] = api_keys[engine]

    saved['api_keys'] = api_keys
    return saved


def get_api_key_for_engine(engine: str) -> str:
    """특정 엔진의 저장된 API 키 반환"""
    settings = load_settings()
    api_keys = settings.get('api_keys', {})
    return api_keys.get(engine, '')


def get_downloads_dir() -> str:
    """다운로드 디렉토리 경로 반환 (사용자 설정 경로 사용)"""
    return ensure_downloads_directory()


# ── 요약 프롬프트 ──────────────────────────────────────────

from src.summarize_pipeline.prompts import (
    DEFAULT_PROMPT,
    build_prompt as _build_prompt,
    SummaryMode,
)

_LEGACY_DEFAULT_PROMPT = """당신은 대학 강의 노트 정리 전문가입니다. 아래는 한국어 강의를 STT(음성→텍스트)로 변환한 원문입니다.

## 주의사항
- STT 변환 과정에서 부정확한 단어가 포함될 수 있습니다. 문맥을 고려하여 올바른 용어로 교정해주세요.
- IT/컴퓨터공학 전공 강의인 경우: 프로그래밍 언어, 알고리즘, 자료구조, 네트워크, 데이터베이스 등 관련 전문 용어를 정확히 유추해주세요.
- 기독교 관련 교양 강의인 경우: 신학, 성경, 교회사 등 관련 용어를 정확히 유추해주세요.

## 요약 형식
다음 형식으로 정리해주세요:

### 📚 강의 제목
(내용에서 유추한 강의 주제)

### 📝 핵심 내용 요약
- 주요 개념과 핵심 내용을 글머리 기호로 정리

### 📖 상세 내용
강의 흐름에 따라 내용을 소주제별로 구분하여 정리

### 💡 주요 키워드
쉼표로 구분된 핵심 키워드 목록

### ⚠️ STT 보정 사항
교정한 주요 용어가 있다면 간단히 기록 (예: "파이선" → "파이썬")"""


def get_summary_prompt() -> str:
    """저장된 요약 프롬프트 반환. 구조화 모드가 있으면 build_prompt 사용."""
    settings = load_settings()
    mode = settings.get("summary_mode")
    if mode:
        return _build_prompt(
            mode=mode,
            subject_category=settings.get("subject_category", "자동 감지"),
            subject_custom=settings.get("subject_custom", ""),
        )
    # 레거시 호환: 기존 raw prompt 문자열
    return settings.get("summary_prompt", DEFAULT_PROMPT)


def set_summary_prompt(prompt: str) -> None:
    """요약 프롬프트를 settings.json에 저장"""
    settings = load_settings()
    settings["summary_prompt"] = prompt
    save_settings(settings)


# ── 요약 모드 / 과목 설정 ─────────────────────────────────

def get_summary_mode() -> str:
    """요약 모드 반환. 기본값: normal."""
    return load_settings().get("summary_mode", SummaryMode.NORMAL)


def set_summary_mode(mode: str) -> None:
    """요약 모드를 settings.json에 저장"""
    settings = load_settings()
    settings["summary_mode"] = mode
    save_settings(settings)


def get_subject_category() -> str:
    """강의 분야 카테고리 반환. 기본값: 자동 감지."""
    return load_settings().get("subject_category", "자동 감지")


def set_subject_category(category: str) -> None:
    """강의 분야 카테고리를 settings.json에 저장"""
    settings = load_settings()
    settings["subject_category"] = category
    save_settings(settings)


def get_subject_custom() -> str:
    """사용자 직접 입력 과목명 반환."""
    return load_settings().get("subject_custom", "")


def set_subject_custom(text: str) -> None:
    """사용자 직접 입력 과목명을 settings.json에 저장"""
    settings = load_settings()
    settings["subject_custom"] = text
    save_settings(settings)


# ── STT 엔진 ──────────────────────────────────────────────

def get_stt_engine() -> str:
    """STT 엔진 반환. 기본값: whisper-cpp."""
    return load_settings().get("stt_engine", "whisper-cpp")


def set_stt_engine(engine: str) -> None:
    """STT 엔진을 settings.json에 저장"""
    settings = load_settings()
    settings["stt_engine"] = engine
    save_settings(settings)


def get_stt_model() -> str:
    """whisper-cpp 모델명 반환. 기본값: base."""
    return load_settings().get("stt_model", "base")


def set_stt_model(model: str) -> None:
    """whisper-cpp 모델명을 settings.json에 저장"""
    settings = load_settings()
    settings["stt_model"] = model
    save_settings(settings)


def get_stt_params() -> dict:
    """whisper-cpp 고급 파라미터 반환. 기본값: 한국어 최적화 설정."""
    defaults = {
        "no_speech_thold": 0.4,
        "suppress_non_speech_tokens": True,
        "initial_prompt": "한국어 강의입니다.",
    }
    stored = load_settings().get("stt_params", {})
    return {**defaults, **stored}


def set_stt_params(params: dict) -> None:
    """whisper-cpp 고급 파라미터를 settings.json에 저장"""
    settings = load_settings()
    settings["stt_params"] = params
    save_settings(settings)


def get_stt_api_key() -> str:
    """ReturnZero STT API 키(client_id:client_secret 형식) 반환"""
    return load_settings().get("stt_api_key", "")


def set_stt_api_key(api_key: str) -> None:
    """ReturnZero STT API 키를 settings.json에 저장"""
    settings = load_settings()
    settings["stt_api_key"] = api_key
    save_settings(settings)


# ── Chrome 경로 ────────────────────────────────────────────

_CHROME_PATHS = {
    'darwin': [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ],
    'win32': [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    'linux': [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
    ],
}


def detect_chrome_paths() -> List[str]:
    """현재 OS에서 Chrome 설치 경로 후보를 반환 (존재하는 경로만)"""
    candidates = _CHROME_PATHS.get(sys.platform, _CHROME_PATHS.get('linux', []))
    return [p for p in candidates if os.path.exists(p)]


def get_chrome_path() -> str:
    """저장된 Chrome 경로 반환. 없으면 자동 감지된 첫 번째 경로."""
    settings = load_settings()
    saved = settings.get("chrome_path", "")
    if saved and os.path.exists(saved):
        return saved
    detected = detect_chrome_paths()
    return detected[0] if detected else ""


def set_chrome_path(path: str) -> None:
    """Chrome 경로를 settings.json에 저장"""
    settings = load_settings()
    settings["chrome_path"] = path
    save_settings(settings)


# ── 디버그 모드 (headless off) ─────────────────────────────

def get_debug_mode() -> bool:
    """디버그 모드 반환. True이면 브라우저 창이 표시됨 (headless=False)."""
    return load_settings().get("debug_mode", False)


def set_debug_mode(enabled: bool) -> None:
    """디버그 모드를 settings.json에 저장"""
    settings = load_settings()
    settings["debug_mode"] = enabled
    save_settings(settings)


# ── 과목 캐시 ─────────────────────────────────────────────

def save_course_cache(courses_data: list) -> None:
    """과목 목록 캐시를 settings.json에 저장"""
    from datetime import datetime
    settings = load_settings()
    settings["course_cache"] = {
        "courses": courses_data,
        "cached_at": datetime.now().isoformat(),
    }
    save_settings(settings)


def load_course_cache(max_age_hours: int = 24) -> list:
    """캐시된 과목 목록 반환. 만료 시 빈 리스트."""
    from datetime import datetime
    settings = load_settings()
    cache = settings.get("course_cache")
    if not cache:
        return []
    try:
        cached_at = datetime.fromisoformat(cache["cached_at"])
        if (datetime.now() - cached_at).total_seconds() > max_age_hours * 3600:
            return []
    except (KeyError, ValueError):
        return []
    return cache.get("courses", [])


def clear_course_cache() -> None:
    """과목 목록 캐시 삭제"""
    settings = load_settings()
    settings.pop("course_cache", None)
    save_settings(settings)


# ── 처리 히스토리 ────────────────────────────────────────

def add_history_entry(entry: Dict) -> None:
    """처리 히스토리 항목 추가.

    entry 구조:
        url (str): 강의 URL
        lecture_name (str): 강의 파일명
        file_size_mb (float): 원본 영상 크기 (MB)
        duration_sec (float): 처리 소요 시간 (초)
        summary_path (str): 요약 파일 경로
        processed_at (str): ISO 형식 타임스탬프
    """
    settings = load_settings()
    history = settings.get("history", [])
    history.append(entry)
    settings["history"] = history
    save_settings(settings)


def load_history() -> List[Dict]:
    """저장된 히스토리 목록 반환"""
    return load_settings().get("history", [])


def clear_history() -> None:
    """히스토리 전체 삭제"""
    settings = load_settings()
    settings.pop("history", None)
    save_settings(settings)


# ── 파일 탐색기 / 자동 열기 ─────────────────────────────

def open_in_file_explorer(path: str) -> None:
    """플랫폼별 파일 탐색기로 경로 열기"""
    import subprocess, sys
    if sys.platform == 'darwin':
        subprocess.Popen(['open', path])
    elif sys.platform == 'win32':
        subprocess.Popen(['explorer', path])
    else:
        subprocess.Popen(['xdg-open', path])


def get_auto_open_folder() -> bool:
    return load_settings().get("auto_open_folder", False)


def set_auto_open_folder(enabled: bool) -> None:
    settings = load_settings()
    settings["auto_open_folder"] = enabled
    save_settings(settings)