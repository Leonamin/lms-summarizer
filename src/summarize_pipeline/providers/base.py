"""
AI Provider 추상 인터페이스
"""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """AI 요약 엔진의 공통 인터페이스"""

    @abstractmethod
    def summarize(self, text: str, prompt: str) -> str:
        """텍스트를 요약하여 반환"""
        pass

    @staticmethod
    @abstractmethod
    def default_model() -> str:
        """기본 모델명 반환"""
        pass

    @staticmethod
    @abstractmethod
    def available_models() -> list[tuple[str, str]]:
        """사용 가능한 모델 목록 반환: [(model_id, display_name), ...]"""
        pass
