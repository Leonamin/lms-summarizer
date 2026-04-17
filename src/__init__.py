# LMS Summarizer 패키지
"""
LMS 강의 다운로드 & 요약
숭실대학교 LMS 연동
"""

import os
import sys

def _detect_version():
    """버전 감지 — 다양한 실행 환경에서 안정적으로 버전을 반환.

    우선순위:
    1. pyproject.toml (개발 환경 + PyInstaller 빌드 모두)
    2. importlib.metadata (pip install 환경)
    3. 하드코딩 폴백 (절대 도달하면 안 됨)
    """
    # 1. pyproject.toml에서 읽기
    #    - 개발: src/../pyproject.toml
    #    - PyInstaller onedir: _internal/pyproject.toml (spec에서 datas에 포함)
    try:
        import tomllib
        _here = os.path.dirname(os.path.abspath(__file__))
        _candidates = [
            os.path.join(_here, "..", "pyproject.toml"),
        ]
        # PyInstaller: sys._MEIPASS는 _internal/ 디렉토리
        if hasattr(sys, "_MEIPASS"):
            _candidates.append(os.path.join(sys._MEIPASS, "pyproject.toml"))
        for _path in _candidates:
            _path = os.path.normpath(_path)
            if os.path.isfile(_path):
                with open(_path, "rb") as _f:
                    return tomllib.load(_f)["project"]["version"]
    except Exception:
        pass

    # 2. pip 설치 환경
    try:
        from importlib.metadata import version as _pkg_version
        return _pkg_version("lms-summarizer")
    except Exception:
        pass

    return "0.0.0"

__version__ = _detect_version()
__author__ = "LMS Summarizer Team"
