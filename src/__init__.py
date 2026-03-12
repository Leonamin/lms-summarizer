# LMS Summarizer 패키지
"""
LMS 강의 다운로드 & 요약
숭실대학교 LMS 연동
"""

try:
    from importlib.metadata import version as _pkg_version
    __version__ = _pkg_version("lms-summarizer")
except Exception:
    __version__ = "unknown"
__author__ = "LMS Summarizer Team" 