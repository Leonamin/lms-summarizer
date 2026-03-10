# -*- mode: python ; coding: utf-8 -*-
#
# LMS Summarizer - PyInstaller spec file
#
# 빌드 명령:
#   Mac:     pyinstaller lms-summarizer.spec
#   Windows: pyinstaller lms-summarizer.spec
#
# 용량 최적화 참고:
#   - whisper.cpp (pywhispercpp): ~2MB (faster-whisper/CTranslate2 대비 대폭 절감)
#   - whisper base ggml 모델: ~142MB → 자동 다운로드 (번들 미포함)
#   - Flet: ~20MB
#   - 전체 예상: ~150-200MB (압축 전)

import sys
import os
from pathlib import Path

APP_NAME = "LMS-Summarizer"
APP_VERSION = "1.4.2"

# SSL 인증서 번들 경로 (PyInstaller에서 requests HTTPS 요청에 필요)
def find_certifi_cacert():
    try:
        import certifi
        return certifi.where()
    except ImportError:
        return None

certifi_cacert = find_certifi_cacert()

# pywhispercpp 네이티브 라이브러리 수집
def collect_pywhispercpp_libs():
    """pywhispercpp의 네이티브 바이너리를 수집"""
    binaries = []
    try:
        import pywhispercpp
        pwc_dir = os.path.dirname(pywhispercpp.__file__)
        for f in os.listdir(pwc_dir):
            full = os.path.join(pwc_dir, f)
            if os.path.isfile(full) and (
                f.endswith(".dll") or f.endswith(".pyd") or
                f.endswith(".so") or f.endswith(".dylib")
            ):
                binaries.append((full, "pywhispercpp"))
    except ImportError:
        print("[WARNING] pywhispercpp not found, skipping lib collection")
    return binaries

# 추가 데이터 파일
datas = [
    ("src", "src"),
    ("assets", "assets"),
]
if certifi_cacert:
    datas.append((certifi_cacert, "certifi"))

# 바이너리: pywhispercpp 네이티브 라이브러리
binaries = []
binaries.extend(collect_pywhispercpp_libs())

a = Analysis(
    ["src/gui/main.py"],
    pathex=[".", "src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        # Flet
        "flet", "flet_core", "flet_runtime",
        # 앱 모듈
        "src.user_setting",
        "src.video_pipeline.pipeline",
        "src.video_pipeline.login",
        "src.video_pipeline.video_parser",
        "src.video_pipeline.download_video",
        "src.video_pipeline.course_scraper",
        "src.audio_pipeline.pipeline",
        "src.audio_pipeline.converter",
        "src.audio_pipeline.transcriber",
        "src.summarize_pipeline.pipeline",
        "src.summarize_pipeline.summarizer",
        "src.gui.core.file_manager",
        "src.gui.core.module_loader",
        "src.gui.core.validators",
        "src.gui.config.constants",
        "src.gui.config.settings",
        "src.gui.config.course_models",
        # 외부 라이브러리
        "openai", "pywhispercpp", "playwright", "requests",
        "dotenv", "google.generativeai", "certifi",
        # pywhispercpp 의존성
        "pywhispercpp.model", "pywhispercpp.utils",
        # 표준 라이브러리
        "json", "threading", "pathlib",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 불필요한 대용량 패키지 제외
        "tkinter", "matplotlib", "PIL", "Pillow",
        "scipy", "pandas", "notebook", "jupyter",
        "IPython", "cv2", "sklearn",
        # torch (불필요)
        "torch", "torch._C", "torch.nn", "torch.backends",
        # faster-whisper / CTranslate2 (whisper.cpp로 대체)
        "faster_whisper", "ctranslate2", "tokenizers", "huggingface_hub",
        # PyQt5 (더 이상 사용하지 않음)
        "PyQt5", "PyQt5.QtCore", "PyQt5.QtWidgets", "PyQt5.QtGui",
        "qtawesome",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,        # UPX 압축 활성화 (설치 시: brew install upx)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # GUI 앱: 콘솔 창 숨김
    icon='assets/icon.ico',
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)

# macOS .app 번들 생성
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon='assets/icon.icns',
        bundle_identifier="com.lms-summarizer.app",
        info_plist={
            "CFBundleDisplayName": "LMS 강의 다운로드 & 요약",
            "CFBundleShortVersionString": APP_VERSION,
            "CFBundleVersion": APP_VERSION,
            "NSHighResolutionCapable": True,
            "NSRequiresAquaSystemAppearance": False,  # Dark mode 지원
        },
    )
