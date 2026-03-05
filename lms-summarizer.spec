# -*- mode: python ; coding: utf-8 -*-
#
# LMS Summarizer - PyInstaller spec file
#
# 빌드 명령:
#   Mac:     pyinstaller lms-summarizer.spec
#   Windows: pyinstaller lms-summarizer.spec
#
# 용량 최적화 참고:
#   - torch (CPU only): ~300MB  → GPU 버전 제외로 절감
#   - whisper base 모델: ~142MB → 번들에 포함
#   - Flet: ~20MB
#   - 전체 예상: ~600-800MB (압축 전), ZIP 시 ~300-400MB
#
# Windows에서 torch CPU only 설치 (용량 절감):
#   pip install torch --index-url https://download.pytorch.org/whl/cpu

import sys
import os
from pathlib import Path

APP_NAME = "LMS-Summarizer"
APP_VERSION = "1.2.1"

# ffmpeg 경로 자동 탐지
def find_ffmpeg():
    import shutil
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    for path in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg"]:
        if os.path.exists(path):
            return path
    raise RuntimeError(
        "ffmpeg를 찾을 수 없습니다. 'brew install ffmpeg' 또는 "
        "https://ffmpeg.org/download.html 에서 설치 후 빌드하세요."
    )

# Whisper 모델 캐시 경로
def find_whisper_models():
    home = Path.home()
    cache = home / ".cache" / "whisper"
    if cache.exists():
        return str(cache)
    return None

# torch 네이티브 라이브러리 수집 (Windows DLL 누락 방지)
def collect_torch_libs():
    """torch의 네이티브 바이너리를 명시적으로 수집"""
    binaries = []
    try:
        import torch
        torch_dir = os.path.dirname(torch.__file__)
        lib_dir = os.path.join(torch_dir, "lib")
        if os.path.isdir(lib_dir):
            for f in os.listdir(lib_dir):
                full = os.path.join(lib_dir, f)
                if os.path.isfile(full) and (
                    f.endswith(".dll") or f.endswith(".pyd") or
                    f.endswith(".so") or f.endswith(".dylib")
                ):
                    binaries.append((full, "torch/lib"))
        # Windows: torch/_C 관련 pyd
        for f in os.listdir(torch_dir):
            full = os.path.join(torch_dir, f)
            if os.path.isfile(full) and f.endswith(".pyd"):
                binaries.append((full, "torch"))
    except ImportError:
        print("[WARNING] torch not found, skipping torch lib collection")
    return binaries


ffmpeg_path = find_ffmpeg()
whisper_cache = find_whisper_models()

# 추가 데이터 파일
datas = [
    ("src", "src"),
    ("assets", "assets"),
]
if whisper_cache:
    datas.append((whisper_cache, "whisper_models"))

# 바이너리: ffmpeg + torch 네이티브 라이브러리
binaries = [(ffmpeg_path, ".")]
binaries.extend(collect_torch_libs())

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
        "openai", "whisper", "playwright", "requests",
        "dotenv", "google.generativeai",
        # torch 핵심 모듈 (Windows DLL 로드에 필요)
        "torch", "torch._C", "torch.nn", "torch.nn.functional",
        "torch.utils", "torch.backends", "torch.cuda",
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
        # PyQt5 (더 이상 사용하지 않음)
        "PyQt5", "PyQt5.QtCore", "PyQt5.QtWidgets", "PyQt5.QtGui",
        "qtawesome",
        # 주의: torch 하위 모듈은 내부 상호 참조가 많아 개별 제외 불가
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
