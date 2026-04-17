# -*- mode: python ; coding: utf-8 -*-
#
# LMS Summarizer - PyInstaller spec file
#
# 빌드 명령:
#   Mac:     pyinstaller lms-summarizer.spec
#   Windows: pyinstaller lms-summarizer.spec
#
# 용량 최적화 참고:
#   - faster-whisper (CTranslate2 기반): STT 엔진
#   - 모델: 런타임 다운로드 (번들 미포함)
#   - Flet: ~20MB

import sys
import os
from pathlib import Path

APP_NAME = "LMS-Summarizer"

# pyproject.toml에서 버전 자동 읽기
def _read_version():
    try:
        import tomllib
        with open("pyproject.toml", "rb") as f:
            return tomllib.load(f)["project"]["version"]
    except Exception:
        return "0.0.0"

APP_VERSION = _read_version()

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
    ("pyproject.toml", "."),  # 버전 정보 (src/__init__.py에서 읽음)
]
if certifi_cacert:
    datas.append((certifi_cacert, "certifi"))

# faster_whisper VAD(silero) ONNX 모델 포함
try:
    import faster_whisper
    fw_assets = os.path.join(os.path.dirname(faster_whisper.__file__), "assets")
    if os.path.isdir(fw_assets):
        datas.append((fw_assets, "faster_whisper/assets"))
except ImportError:
    pass

binaries = []

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
        "openai", "faster_whisper", "ctranslate2", "playwright", "requests",
        "dotenv", "google.genai", "certifi", "huggingface_hub", "tokenizers",
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
        # torch 및 관련 (~275MB 절감)
        "torch", "torch._C", "torch.nn", "torch.backends",
        "torch.cuda", "torch.distributed", "torch.utils",
        "torchvision", "torchaudio", "caffe2",
        # numba / llvmlite (~100MB 절감)
        "numba", "llvmlite",
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

# 불필요한 대용량 네이티브 라이브러리 필터링 (excludes는 Python 모듈만 차단)
_bloat_prefixes = ('torch', 'libtorch', 'numba', 'llvmlite', 'caffe2')

def _is_bloat(name):
    parts = name.replace('\\', '/').split('/')
    return any(p.startswith(_bloat_prefixes) for p in parts)

a.binaries = [b for b in a.binaries if not _is_bloat(b[0])]
a.datas = [d for d in a.datas if not _is_bloat(d[0])]

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
