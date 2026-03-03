"""
애플리케이션에서 사용하는 상수들
"""

from dataclasses import dataclass

# 앱 기본 정보
APP_TITLE = "LMS 강의 다운로드 & 요약"
APP_VERSION = "v1.0"
WINDOW_WIDTH = 660
WINDOW_HEIGHT = 600
MIN_WINDOW_WIDTH = 580
MIN_WINDOW_HEIGHT = 450

# 로그 메시지에 사용할 이모지
EMOJI_START = "🚀"
EMOJI_SUCCESS = "✅"
EMOJI_ERROR = "❌"
EMOJI_WARNING = "⚠️"
EMOJI_INFO = "📋"
EMOJI_PROCESSING = "⏳"
EMOJI_STOP = "⏹"


@dataclass(frozen=True)
class Colors:
    """UI에서 사용하는 색상 정의 (밝은 테마)"""
    PRIMARY = "#1976D2"
    PRIMARY_HOVER = "#1565C0"
    PRIMARY_PRESSED = "#0D47A1"
    BACKGROUND = "#F5F5F5"
    CARD_BG = "#FFFFFF"
    TEXT_DARK = "#212121"
    TEXT_SECONDARY = "#424242"
    TEXT_LIGHT = "#757575"
    LOG_BG = "#F8F9FA"
    LOG_TEXT = "#333333"
    SUCCESS = "#388E3C"
    WARNING = "#F57C00"
    ERROR = "#D32F2F"
    WHITE = "#FFFFFF"
    BORDER = "#E0E0E0"
    BORDER_FOCUS = "#1976D2"
    DISABLED_BG = "#BDBDBD"


@dataclass(frozen=True)
class Messages:
    """애플리케이션에서 사용하는 메시지들"""
    # 처리 상태 메시지
    PROCESSING_START = f"{EMOJI_START} LMS 요약 작업을 시작합니다..."
    PROCESSING_COMPLETE = f"{EMOJI_SUCCESS} 모든 작업이 완료되었습니다!"

    # 에러 메시지
    MODULE_LOAD_ERROR = f"{EMOJI_ERROR} 필수 모듈들이 로드되지 않았습니다"
    INSTALL_REQUIREMENTS = "uv sync 실행 후 재시작하세요."

    # 입력 검증 메시지
    STUDENT_ID_REQUIRED = "학번을 입력해주세요."
    PASSWORD_REQUIRED = "비밀번호를 입력해주세요."
    API_KEY_REQUIRED = "Gemini API 키를 입력해주세요."
    URLS_REQUIRED = "강의 URL을 입력해주세요."

    # 진행 상태 메시지
    CONFIG_CREATING = f"{EMOJI_INFO} 설정 파일 생성 중..."
    VIDEO_DOWNLOADING = f"{EMOJI_INFO} 비디오 다운로드 시작..."
    AUDIO_CONVERTING = f"{EMOJI_INFO} 음성을 텍스트로 변환 중..."
    TEXT_SUMMARIZING = f"{EMOJI_INFO} AI 요약 생성 중..."

    # 완료 메시지
    DOWNLOAD_COMPLETE = f"{EMOJI_SUCCESS} 다운로드 완료"
    CONVERSION_COMPLETE = f"{EMOJI_SUCCESS} 변환 완료"
    SUMMARY_COMPLETE = f"{EMOJI_SUCCESS} 요약 완료"

    # 실패 메시지
    DOWNLOAD_FAILED = f"{EMOJI_ERROR} 다운로드 실패"
    CONVERSION_FAILED = f"{EMOJI_ERROR} 변환 실패"
    SUMMARY_FAILED = f"{EMOJI_ERROR} 요약 실패"


@dataclass(frozen=True)
class FileExtensions:
    """파일 확장자 정의"""
    VIDEO = ['.mp4', '.avi', '.mkv', '.mov']
    AUDIO = ['.mp3', '.wav', '.m4a']
    TEXT = ['.txt', '.md']


@dataclass(frozen=True)
class Limits:
    """제한값들"""
    MAX_TEXT_LENGTH = 8000
    LOG_AREA_MIN_HEIGHT = 80
    URL_INPUT_MIN_HEIGHT = 80
    MIN_INPUT_WIDTH = 400
    MIN_INPUT_HEIGHT = 80
