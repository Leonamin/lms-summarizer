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
#   - PyQt5: ~40MB
#   - 전체 .app 예상: ~600-800MB (압축 전), ZIP 시 ~300-400MB
#
# Windows에서 torch CPU only 설치 (용량 절감):
#   pip install torch --index-url https://download.pytorch.org/whl/cpu

import sys
import os
from pathlib import Path

APP_NAME = "LMS-Summarizer"
APP_VERSION = "1.1.0"

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

ffmpeg_path = find_ffmpeg()
whisper_cache = find_whisper_models()

# 추가 데이터 파일
datas = [
    ("src", "src"),
    ("assets", "assets"),
]
if whisper_cache:
    datas.append((whisper_cache, "whisper_models"))

# ffmpeg 바이너리 포함
binaries = [(ffmpeg_path, ".")]

a = Analysis(
    ["src/gui/main.py"],
    pathex=[".", "src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        # PyQt5
        "PyQt5", "PyQt5.QtCore", "PyQt5.QtWidgets", "PyQt5.QtGui",
        # 앱 모듈
        "src.user_setting",
        "src.video_pipeline.pipeline",
        "src.video_pipeline.login",
        "src.video_pipeline.video_parser",
        "src.video_pipeline.download_video",
        "src.audio_pipeline.pipeline",
        "src.audio_pipeline.converter",
        "src.audio_pipeline.transcriber",
        "src.summarize_pipeline.pipeline",
        "src.summarize_pipeline.summarizer",
        # 외부 라이브러리
        "openai", "whisper", "playwright", "requests",
        "dotenv", "google.generativeai",
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
        # torch CUDA 관련 제외 (Mac/CPU-only 빌드)
        "torch.cuda", "torch.backends.cudnn",
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
