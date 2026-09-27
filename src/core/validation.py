"""
사용자 입력 검증 로직
"""

import re
from typing import Dict, List, Tuple
from urllib.parse import urlparse




class InputValidator:
    """입력값 검증을 담당하는 클래스"""

    @staticmethod
    def validate_student_id(student_id: str) -> Tuple[bool, str]:
        """학번 유효성 검사"""
        if not student_id.strip():
            return False, '학번을 입력해주세요.'

        # 학번은 일반적으로 숫자로 구성
        if not re.match(r'^\d{8}$', student_id.strip()):
            return False, "학번은 8자리 숫자여야 합니다."

        return True, ""

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """비밀번호 유효성 검사"""
        if not password.strip():
            return False, '비밀번호를 입력해주세요.'

        if len(password) < 4:
            return False, "비밀번호는 최소 4자리 이상이어야 합니다."

        return True, ""

    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, str]:
        """API 키 유효성 검사"""
        if not api_key.strip():
            return False, 'API 키를 입력해주세요.'

        # API 키는 일반적으로 특정 길이 이상
        if len(api_key.strip()) < 10:
            return False, "API 키가 너무 짧습니다."

        return True, ""

    @staticmethod
    def validate_urls(urls_text: str) -> Tuple[bool, str, List[str]]:
        """URL 목록 유효성 검사"""
        if not urls_text.strip():
            return False, 'URL을 입력해주세요.', []

        urls = []
        invalid_urls = []

        for line in urls_text.split('\n'):
            url = line.strip()
            if not url:
                continue

            # URL 형식 검사
            if not InputValidator._is_valid_url(url):
                invalid_urls.append(url)
            else:
                urls.append(url)

        if not urls:
            return False, "유효한 URL이 없습니다.", []

        if invalid_urls:
            return False, f"유효하지 않은 URL: {', '.join(invalid_urls[:3])}", urls

        # 중복 URL 검사
        seen = set()
        duplicates = []
        unique_urls = []
        for url in urls:
            if url in seen:
                duplicates.append(url)
            else:
                seen.add(url)
                unique_urls.append(url)

        if duplicates:
            return False, f"중복된 URL이 {len(duplicates)}개 있습니다. 중복을 제거해주세요.", unique_urls

        return True, "", urls

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """URL 형식 유효성 검사"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    @staticmethod
    def validate_all_inputs(inputs: Dict[str, str], skip_api_key: bool = False,
                            skip_urls: bool = False,
                            require_credentials: bool = True,
                            require_chrome: bool = True, chrome_path: str = "") -> Tuple[bool, str]:
        """모든 입력값 종합 검증

        Args:
            inputs: 입력값 딕셔너리
            skip_api_key: True이면 API 키 검증을 건너뜀 (클립보드 모드 등)
            skip_urls: True이면 URL 검증을 건너뜀 (로컬 파일 소스)
            require_credentials: False이면 학번/비밀번호 검증을 건너뜀 (로컬 파일 소스)
            require_chrome: False이면 Chrome 경로 검증을 건너뜀 (로컬 파일 소스)
        """
        # 학번/비밀번호 검증 (LMS 다운로드에만 필요)
        if require_credentials:
            valid, error = InputValidator.validate_student_id(inputs.get('student_id', ''))
            if not valid:
                return False, error

            valid, error = InputValidator.validate_password(inputs.get('password', ''))
            if not valid:
                return False, error

        # API 키 검증 (클립보드 모드에서는 건너뜀)
        if not skip_api_key:
            valid, error = InputValidator.validate_api_key(inputs.get('api_key', ''))
            if not valid:
                return False, error

        # URL 검증 (로컬 파일 소스에서는 건너뜀)
        if not skip_urls:
            valid, error, urls = InputValidator.validate_urls(inputs.get('urls', ''))
            if not valid:
                return False, error

        # Chrome 경로 검증 (LMS 다운로드에만 필요)
        if require_chrome:
            valid, error = InputValidator.validate_chrome(chrome_path)
            if not valid:
                return False, error

        return True, ""

    @staticmethod
    def validate_chrome(chrome_path: str = "") -> Tuple[bool, str]:
        from pathlib import Path
        if not chrome_path or not Path(chrome_path).is_file():
            return False, "Chrome 실행 파일 경로를 지정해주세요."
        return True, ""


def initial_stage(filename: str):
    """File input has a defined entry point; unsupported extensions are errors."""
    from pathlib import Path
    from src.core.models.stages import PipelineStage
    stages = {".mp4": PipelineStage.CONVERT_AUDIO, ".ts": PipelineStage.CONVERT_AUDIO,
              ".wav": PipelineStage.STT, ".mp3": PipelineStage.STT,
              ".txt": PipelineStage.SUMMARIZE}
    try:
        return stages[Path(filename).suffix.lower()]
    except KeyError:
        raise ValueError("Unsupported input extension") from None


def validate_stage_range(start, end):
    from src.core.models.stages import PipelineStage
    start, end = PipelineStage(start), PipelineStage(end)
    if end < start:
        raise ValueError("End stage precedes input stage")
    return start, end
