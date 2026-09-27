# LMS Summarizer - Windows 빌드 스크립트 (PowerShell)
# 사용법: powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1
#
# 사전 요구사항:
#   - Python 3.11-3.12 설치 (python.org)
#   - uv 설치: winget install astral-sh.uv

$ErrorActionPreference = "Stop"

$APP_NAME = "LMS-Summarizer"
$APP_VERSION = (Select-String -Path "pyproject.toml" -Pattern '^version = "(.*)"' |
    Select-Object -First 1).Matches[0].Groups[1].Value
if (-not $APP_VERSION) {
    Write-Host "❌ pyproject.toml에서 버전을 읽을 수 없습니다." -ForegroundColor Red
    exit 1
}

Write-Host "🚀 LMS Summarizer v$APP_VERSION Windows 빌드 시작..." -ForegroundColor Cyan

# 프로젝트 루트 확인
if (-not (Test-Path "src/desktop/main.py")) {
    Write-Host "❌ src/desktop/main.py를 찾을 수 없습니다. 프로젝트 루트에서 실행해주세요." -ForegroundColor Red
    exit 1
}

# uv 확인
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "❌ uv가 없습니다: https://docs.astral.sh/uv/" -ForegroundColor Red
    Write-Host "   설치: winget install astral-sh.uv" -ForegroundColor Yellow
    exit 1
}

# 의존성 설치
Write-Host "📦 의존성 설치 중..."
uv sync --extra desktop --extra cuda
uv pip install pyinstaller

# 이전 빌드 정리
Write-Host "🧹 이전 빌드 파일 정리..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# spec 파일로 빌드
Write-Host "🔨 PyInstaller 빌드 시작..."
uv run --extra desktop --extra cuda pyinstaller lms-summarizer.spec

# 빌드 결과 확인
$distExe = "dist\$APP_NAME\$APP_NAME.exe"
if (-not (Test-Path $distExe)) {
    Write-Host "❌ 빌드 실패: $distExe 를 찾을 수 없습니다." -ForegroundColor Red
    exit 1
}

# 콘솔 없는 번들에서도 spawn 워커 실행과 결과 생성을 확인
$smokeResult = Join-Path $env:TEMP "lms-core-smoke-$([guid]::NewGuid()).json"
try {
    $process = Start-Process -FilePath $distExe -ArgumentList @("--core-smoke", "--core-smoke-result", "`"$smokeResult`"") -Wait -PassThru
    if ($process.ExitCode -ne 0) { throw "Core smoke failed: $($process.ExitCode)" }
    if ((Get-Content $smokeResult | ConvertFrom-Json).status -ne "ok") { throw "Core smoke result missing" }
} finally {
    if (Test-Path $smokeResult) { Remove-Item $smokeResult }
}

$distDir = "dist\$APP_NAME"
$dirSize = [math]::Round((Get-ChildItem $distDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
Write-Host "✅ 빌드 완료! 크기: ${dirSize}MB" -ForegroundColor Green

# 배포용 ZIP 생성
$zipName = "$APP_NAME-v$APP_VERSION-windows.zip"
Write-Host "📦 배포용 ZIP 생성: dist\$zipName"
Compress-Archive -Path $distDir -DestinationPath "dist\$zipName" -Force

$zipSize = [math]::Round((Get-Item "dist\$zipName").Length / 1MB, 1)
Write-Host "✅ ZIP 생성 완료: dist\$zipName (${zipSize}MB)" -ForegroundColor Green

# 임시 빌드 파일 정리
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

Write-Host ""
Write-Host "🎉 빌드 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 결과물:"
Write-Host "   폴더: $distDir (${dirSize}MB)"
Write-Host "   ZIP:  dist\$zipName (${zipSize}MB)"
Write-Host ""
Write-Host "🚀 실행: dist\$APP_NAME\$APP_NAME.exe"
