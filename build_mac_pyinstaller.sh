#!/bin/bash
#
# LMS Summarizer - Mac .app 빌드 스크립트
# 사용법: ./build_mac_pyinstaller.sh
#

set -e

APP_VERSION="0.1.0-beta"
APP_NAME="LMS-Summarizer"

echo "🚀 LMS Summarizer v${APP_VERSION} Mac 빌드 시작..."

# 프로젝트 루트 확인
if [ ! -f "src/gui/main.py" ]; then
    echo "❌ src/gui/main.py를 찾을 수 없습니다. 프로젝트 루트에서 실행해주세요."
    exit 1
fi

# uv 확인
if ! command -v uv &> /dev/null; then
    echo "❌ uv가 없습니다: https://docs.astral.sh/uv/"
    exit 1
fi

# ffmpeg 확인
FFMPEG_PATH=""
for path in "/opt/homebrew/bin/ffmpeg" "/usr/local/bin/ffmpeg" "/usr/bin/ffmpeg"; do
    if [ -f "$path" ]; then
        FFMPEG_PATH="$path"
        break
    fi
done
if [ -z "$FFMPEG_PATH" ]; then
    echo "❌ ffmpeg를 찾을 수 없습니다."
    echo "   설치: brew install ffmpeg"
    exit 1
fi
echo "✅ ffmpeg: $FFMPEG_PATH"

# Whisper 모델 사전 다운로드 (base 모델 ~142MB)
echo "📥 Whisper base 모델 확인 중..."
uv run python -c "import whisper; whisper.load_model('base'); print('✅ 모델 준비 완료')"

# 의존성 설치
echo "📦 의존성 설치 중..."
uv sync
uv pip install pyinstaller

# 기존 빌드 정리
echo "🧹 이전 빌드 파일 정리..."
rm -rf build/ dist/

# spec 파일로 빌드
echo "🔨 PyInstaller 빌드 시작..."
uv run pyinstaller lms-summarizer.spec

# 빌드 결과 확인
DIST_APP="dist/${APP_NAME}.app"
if [ ! -d "$DIST_APP" ]; then
    echo "❌ 빌드 실패: $DIST_APP 를 찾을 수 없습니다."
    exit 1
fi

APP_SIZE=$(du -sh "$DIST_APP" | cut -f1)
echo "✅ .app 번들 생성 완료!"
echo "   경로: $DIST_APP"
echo "   크기: $APP_SIZE"

# 배포용 ZIP 생성
ZIP_NAME="${APP_NAME}-v${APP_VERSION}-mac.zip"
echo "📦 배포용 ZIP 생성: dist/$ZIP_NAME"
(cd dist && zip -qr "$ZIP_NAME" "${APP_NAME}.app")

ZIP_SIZE=$(du -sh "dist/$ZIP_NAME" | cut -f1)
echo "✅ ZIP 생성 완료: dist/$ZIP_NAME ($ZIP_SIZE)"

# 임시 빌드 파일 정리
rm -rf build/

echo ""
echo "🎉 빌드 완료!"
echo ""
echo "📋 결과물:"
echo "   .app: $DIST_APP ($APP_SIZE)"
echo "   ZIP:  dist/$ZIP_NAME ($ZIP_SIZE)"
echo ""
echo "🚀 실행:"
echo "   open $DIST_APP"
echo ""
echo "⚠️  Gatekeeper 경고 해제 (서명 없는 앱):"
echo "   xattr -rd com.apple.quarantine $DIST_APP"
