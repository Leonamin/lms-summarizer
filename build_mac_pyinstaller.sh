#!/bin/bash

# LMS 요약 도구 Mac .app 빌드 스크립트 (PyInstaller 사용)
# 설명: PyInstaller를 사용하여 GUI 애플리케이션을 Mac .app 번들로 변환

set -e  # 오류 발생 시 스크립트 중단

echo "🚀 LMS 요약 도구 Mac 앱 빌드를 시작합니다 (PyInstaller 사용)..."

# 현재 디렉토리 확인
if [ ! -f "src/gui/main.py" ]; then
    echo "❌ src/gui/main.py 파일을 찾을 수 없습니다. 프로젝트 루트 디렉토리에서 실행해주세요."
    exit 1
fi

# 가상환경 활성화 확인
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  가상환경이 활성화되지 않았습니다. .venv를 활성화합니다..."
    source .venv/bin/activate
fi

echo "📦 PyInstaller를 설치합니다..."
pip install pyinstaller

# 기존 빌드 파일들 정리
echo "🧹 기존 빌드 파일들을 정리합니다..."
rm -rf build/ dist/ *.spec

echo "🔨 .app 번들을 빌드합니다..."

# PyInstaller로 Mac 앱 빌드
pyinstaller \
    --name="LMS-Summarizer" \
    --windowed \
    --onedir \
    --add-data="src:src" \
    --add-data="requirements.txt:." \
    --paths="src" \
    --paths="src/video_pipeline" \
    --paths="src/audio_pipeline" \
    --paths="src/summarize_pipeline" \
    --hidden-import=PyQt5 \
    --hidden-import=PyQt5.QtCore \
    --hidden-import=PyQt5.QtWidgets \
    --hidden-import=PyQt5.QtGui \
    --hidden-import=openai \
    --hidden-import=whisper \
    --hidden-import=playwright \
    --hidden-import=requests \
    --hidden-import=dotenv \
    --hidden-import=json \
    --hidden-import=threading \
    --hidden-import=src.user_setting \
    --hidden-import=src.video_pipeline.pipeline \
    --hidden-import=src.audio_pipeline.pipeline \
    --hidden-import=src.summarize_pipeline.pipeline \
    --hidden-import=src.video_pipeline.login \
    --hidden-import=src.video_pipeline.video_parser \
    --hidden-import=src.video_pipeline.download_video \
    --hidden-import=src.audio_pipeline.converter \
    --hidden-import=src.audio_pipeline.transcriber \
    --hidden-import=src.summarize_pipeline.summarizer \
    --collect-all=whisper \
    --collect-all=torch \
    --collect-all=torchaudio \
    --collect-all=openai \
    --collect-submodules=src \
    --exclude-module=tkinter \
    --exclude-module=matplotlib \
    --exclude-module=PIL \
    src/gui/main.py

# 빌드 결과 확인
if [ -d "dist/LMS-Summarizer.app" ]; then
    echo "✅ .app 번들 생성 완료!"
    
    # 앱 정보 출력
    echo "📱 생성된 앱: dist/LMS-Summarizer.app"
    echo "📏 앱 크기: $(du -sh dist/LMS-Summarizer.app | cut -f1)"
    
    # ZIP 파일로도 압축
    echo "📦 배포용 ZIP 파일을 생성합니다..."
    cd dist
    zip -r "LMS-Summarizer-Mac.zip" "LMS-Summarizer.app"
    cd ..
    
    echo "✅ 빌드 완료!"
    echo "📁 결과물:"
    echo "   - dist/LMS-Summarizer.app (Mac 애플리케이션)"
    echo "   - dist/LMS-Summarizer-Mac.zip (배포용 ZIP)"
    echo ""
    echo "🚀 애플리케이션을 실행하려면:"
    echo "   open dist/LMS-Summarizer.app"
    
    # 애플리케이션 정보 설정
    echo "📝 애플리케이션 정보를 설정합니다..."
    INFO_PLIST="dist/LMS-Summarizer.app/Contents/Info.plist"
    if [ -f "$INFO_PLIST" ]; then
        # CFBundleDisplayName 추가
        /usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName 'LMS 강의 다운로드 & 요약'" "$INFO_PLIST" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :CFBundleDisplayName string 'LMS 강의 다운로드 & 요약'" "$INFO_PLIST"
        
        # CFBundleVersion 설정
        /usr/libexec/PlistBuddy -c "Set :CFBundleVersion '1.0.0'" "$INFO_PLIST" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :CFBundleVersion string '1.0.0'" "$INFO_PLIST"
        
        # CFBundleShortVersionString 설정
        /usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString '1.0.0'" "$INFO_PLIST" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string '1.0.0'" "$INFO_PLIST"
        
        # NSHighResolutionCapable 설정
        /usr/libexec/PlistBuddy -c "Set :NSHighResolutionCapable true" "$INFO_PLIST" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :NSHighResolutionCapable bool true" "$INFO_PLIST"
        
        echo "✅ 애플리케이션 정보 설정 완료"
    fi
    
else
    echo "❌ .app 번들 생성에 실패했습니다."
    echo "빌드 로그를 확인해주세요."
    exit 1
fi

# 정리
echo "🧹 임시 파일들을 정리합니다..."
rm -rf build/ *.spec

echo "🎉 Mac 앱 빌드가 완료되었습니다!"
echo ""
echo "📋 사용법:"
echo "1. dist/LMS-Summarizer.app을 Applications 폴더로 복사"
echo "2. 처음 실행 시 '확인되지 않은 개발자' 경고가 나타날 수 있음"
echo "3. 시스템 환경설정 > 보안 및 개인 정보 보호에서 '확인 없이 열기' 클릭"
echo ""
echo "🎯 완전한 배포용 패키지를 원한다면 create_dmg.sh를 실행하세요"