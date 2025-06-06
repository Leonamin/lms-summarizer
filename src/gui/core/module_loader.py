"""
필수 모듈들의 동적 로딩을 관리
"""

import sys
import os
from typing import Dict, List, Tuple, Optional, Any

from config.settings import MODULE_CONFIGS


def setup_python_path() -> Tuple[str, str]:
    """Python 경로 설정"""
    if getattr(sys, 'frozen', False):
        # PyInstaller로 번들된 환경
        application_path = sys._MEIPASS
        src_path = os.path.join(application_path, 'src')
    else:
        # 개발 환경
        application_path = os.path.dirname(os.path.dirname(__file__))
        src_path = os.path.join(application_path, 'src')

    # Python 경로에 추가
    for path in [src_path, application_path]:
        if path not in sys.path:
            sys.path.insert(0, path)

    print(f"[DEBUG] Application path: {application_path}")
    print(f"[DEBUG] Src path: {src_path}")
    print(f"[DEBUG] Python path: {sys.path[:3]}")

    return application_path, src_path


def load_required_modules() -> Tuple[Dict[str, Optional[Any]], List[str]]:
    """필수 모듈들을 로드하고 결과 반환"""
    modules = {}
    errors = []
    success_modules = []

    for name, config in MODULE_CONFIGS.items():
        try:
            module_parts = config.import_path.split('.')
            module = __import__('.'.join(module_parts[:-1]), fromlist=[module_parts[-1]])
            modules[name] = getattr(module, module_parts[-1])
            success_modules.append(name)
            print(f"[SUCCESS] {name} 모듈 로드 완료")
        except ImportError as e:
            modules[name] = None
            errors.append(f"{name}: {e}")
            print(f"[ERROR] {name} 로드 실패: {e}")

    print(f"[INFO] 성공적으로 로드된 모듈: {success_modules}")
    if errors:
        print(f"[WARNING] 로드 실패한 모듈: {errors}")

    return modules, errors


def check_required_modules(modules: Dict[str, Optional[Any]]) -> Tuple[bool, List[str]]:
    """필수 모듈들이 모두 로드되었는지 확인"""
    missing_modules = [name for name, module in modules.items() if module is None]
    return len(missing_modules) == 0, missing_modules