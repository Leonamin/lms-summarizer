"""
사용자 입력 검증 로직
"""

import re
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from config.constants import Messages


class InputValidator:
    """입력값 검증을 담당하는 클래스"""

    @staticmethod
    def validate_student_id(student_id: str) -> Tuple[bool, str]:
        """학번 유효성 검사"""
        if not student_id.strip():
            return False, Messages.STUDENT_ID_REQUIRED

        # 학번은 일반적으로 숫자로 구성
        if not re.match(r'^\d{8}$', student_id.strip()):
            return False, "학번은 8자리 숫자여야 합니다."

        return True, ""

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """비밀번호 유효성 검사"""
        if not password.strip():
            return False, Messages.PASSWORD_REQUIRED

        if len(password) < 4:
            return False, "비밀번호는 최소 4자리 이상이어야 합니다."

        return True, ""

    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, str]:
        """API 키 유효성 검사"""
        if not api_key.strip():
            return False, Messages.API_KEY_REQUIRED

        # API 키는 일반적으로 특정 길이 이상
        if len(api_key.strip()) < 10:
            return False, "API 키가 너무 짧습니다."

        return True, ""

    @staticmethod
    def validate_urls(urls_text: str) -> Tuple[bool, str, List[str]]:
        """URL 목록 유효성 검사"""
        if not urls_text.strip():
            return False, Messages.URLS_REQUIRED, []

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
    def validate_all_inputs(inputs: Dict[str, str]) -> Tuple[bool, str]:
        """모든 입력값 종합 검증"""
        # 학번 검증
        valid, error = InputValidator.validate_student_id(inputs.get('student_id', ''))
        if not valid:
            return False, error

        # 비밀번호 검증
        valid, error = InputValidator.validate_password(inputs.get('password', ''))
        if not valid:
            return False, error

        # API 키 검증
        valid, error = InputValidator.validate_api_key(inputs.get('api_key', ''))
        if not valid:
            return False, error

        # URL 검증
        valid, error, urls = InputValidator.validate_urls(inputs.get('urls', ''))
        if not valid:
            return False, error

        return True, ""