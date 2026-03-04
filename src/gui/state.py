"""
앱 상태 관리
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class AppState:
    """앱 전체 상태"""
    # 모듈
    modules: Dict[str, Any] = field(default_factory=dict)
    module_errors: List[str] = field(default_factory=list)

    # 처리 상태
    is_processing: bool = False
    current_step: int = 0
    current_step_name: str = ""

    # 입력값
    student_id: str = ""
    password: str = ""
    api_key: str = ""
    urls: str = ""
    ai_model: str = "gemini-2.5-flash"
    save_video: bool = False

    # 경로
    downloads_dir: str = ""

    # 워커 참조 (Optional)
    worker: Optional[Any] = None
