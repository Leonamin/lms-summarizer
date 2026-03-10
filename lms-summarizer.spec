# -*- mode: python ; coding: utf-8 -*-
#
# LMS Summarizer - PyInstaller spec file
#
# 빌드 명령:
#   Mac:     pyinstaller lms-summarizer.spec
#   Windows: pyinstaller lms-summarizer.spec
#
# 용량 최적화 참고:
#   - faster-whisper (CTranslate2): ~80MB (torch 대비 대폭 절감)
#   - whisper base 모델: ~142MB → 번들에 포함
#   - Flet: ~20MB
#   - 전체 예상: ~250-350MB (압축 전), ZIP 시 ~150-200MB

import sys
import os
from pathlib import Path

APP_NAME = "LMS-Summarizer"
APP_VERSION = "1.3.0"

# faster-whisper 모델 캐시 경로 (huggingface hub 캐시)
def find_whisper_models():
    home = Path.home()
    # faster-whisper는 huggingface_hub 캐시를 사용
    hf_cache = home / ".cache" / "huggingface" / "hub"
    if hf_cache.exists():
        for d in hf_cache.iterdir():
            if d.is_dir() and "whisper" in d.name:
                return str(d)
    # openai-whisper 레거시 캐시도 확인
    whisper_cache = home / ".cache" / "whisper"
    if whisper_cache.exists():
        return str(whisper_cache)
    return None

# CTranslate2 라이브러리 수집
def collect_ctranslate2_libs():
    """CTranslate2의 네이티브 바이너리를 수집"""
    binaries = []
    try:
        import ctranslate2
        ct2_dir = os.path.dirname(ctranslate2.__file__)
        for f in os.listdir(ct2_dir):
            full = os.path.join(ct2_dir, f)
            if os.path.isfile(full) and (
                f.endswith(".dll") or f.endswith(".pyd") or
                f.endswith(".so") or f.endswith(".dylib")
            ):
                binaries.append((full, "ctranslate2"))
        lib_dir = os.path.join(ct2_dir, "lib")
        if os.path.isdir(lib_dir):
            for f in os.listdir(lib_dir):
                full = os.path.join(lib_dir, f)
                if os.path.isfile(full):
                    binaries.append((full, "ctranslate2/lib"))
    except ImportError:
        print("[WARNING] ctranslate2 not found, skipping lib collection")
    return binaries


whisper_cache = find_whisper_models()

# SSL 인증서 번들 경로 (PyInstaller에서 requests HTTPS 요청에 필요)
def find_certifi_cacert():
    try:
        import certifi
        return certifi.where()
    except ImportError:
        return None

certifi_cacert = find_certifi_cacert()

# 추가 데이터 파일
datas = [
    ("src", "src"),
    ("assets", "assets"),
]
if whisper_cache:
    datas.append((whisper_cache, "whisper_models"))
if certifi_cacert:
    datas.append((certifi_cacert, "certifi"))

# 바이너리: CTranslate2 네이티브 라이브러리
binaries = []
binaries.extend(collect_ctranslate2_libs())

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
        "openai", "faster_whisper", "playwright", "requests",
        "dotenv", "google.generativeai", "certifi",
        # faster-whisper 의존성
        "ctranslate2", "tokenizers", "huggingface_hub", "av",
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
        # torch (faster-whisper로 대체하여 불필요)
        "torch", "torch._C", "torch.nn", "torch.backends",
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
