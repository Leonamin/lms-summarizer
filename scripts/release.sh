#!/usr/bin/env bash
set -euo pipefail

# ───────────────────────────────────────────────────────
# LMS Summarizer Release Script
#
# Usage: scripts/release.sh <patch|minor|major>
#
# 1. pyproject.toml + lms-summarizer.spec 버전 범프
# 2. release 커밋 + 태그 생성
# 3. push → GitHub Actions가 빌드 + Release 생성
# ───────────────────────────────────────────────────────

MODE="${1:-}"
if [[ ! "$MODE" =~ ^(patch|minor|major)$ ]]; then
    echo "Usage: $0 <patch|minor|major>"
    echo ""
    echo "Examples:"
    echo "  $0 patch   # 1.8.0 → 1.8.1"
    echo "  $0 minor   # 1.8.0 → 1.9.0"
    echo "  $0 major   # 1.8.0 → 2.0.0"
    exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

# ── 현재 버전 읽기 ──────────────────────────────────────
CURRENT=$(grep -m1 '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
if [[ -z "$CURRENT" ]]; then
    echo "Error: pyproject.toml에서 version을 찾을 수 없습니다."
    exit 1
fi

IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

# ── 버전 범프 ────────────────────────────────────────────
case "$MODE" in
    patch) PATCH=$((PATCH + 1)) ;;
    minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
    major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
TAG="v${NEW_VERSION}"

echo "📦 Version: ${CURRENT} → ${NEW_VERSION} (${MODE})"
echo "🏷  Tag: ${TAG}"
echo ""

# ── Pre-flight 체크 ──────────────────────────────────────
# 1) Clean working tree
if [[ -n "$(git status --porcelain)" ]]; then
    echo "Error: 작업 트리가 깨끗하지 않습니다. 커밋 또는 stash 후 다시 시도하세요."
    exit 1
fi

# 2) master 브랜치인지 확인
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$BRANCH" != "master" ]]; then
    echo "Error: master 브랜치에서만 릴리즈할 수 있습니다. (현재: '${BRANCH}')"
    exit 1
fi

# 3) remote와 동기화 확인
git fetch origin master --quiet
LOCAL=$(git rev-parse master)
REMOTE=$(git rev-parse origin/master)
if [[ "$LOCAL" != "$REMOTE" ]]; then
    echo "Error: master가 origin/master와 동기화되지 않았습니다. pull 후 다시 시도하세요."
    exit 1
fi

# 4) 태그 중복 확인
if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "Error: 태그 '${TAG}'가 이미 존재합니다."
    exit 1
fi

# ── 버전 업데이트 ────────────────────────────────────────
# pyproject.toml
sed -i '' "s/^version = \"${CURRENT}\"/version = \"${NEW_VERSION}\"/" pyproject.toml

# lms-summarizer.spec (PyInstaller / macOS info.plist에 사용)
sed -i '' "s/^APP_VERSION = \".*\"/APP_VERSION = \"${NEW_VERSION}\"/" lms-summarizer.spec

echo "✏️  pyproject.toml, lms-summarizer.spec 버전 업데이트 완료"

# ── uv.lock 동기화 ───────────────────────────────────────
if command -v uv >/dev/null 2>&1; then
    uv lock --quiet 2>/dev/null || true
    if [[ -n "$(git diff --name-only uv.lock 2>/dev/null)" ]]; then
        echo "✏️  uv.lock 동기화 완료"
    fi
fi

# ── 커밋 & 태그 ──────────────────────────────────────────
git add pyproject.toml lms-summarizer.spec uv.lock 2>/dev/null || git add pyproject.toml lms-summarizer.spec
git commit -m "release: ${TAG}"
git tag -a "$TAG" -m "Release ${TAG}"

echo ""
echo "✅ 커밋 및 태그 생성 완료"
echo ""

# ── Push ─────────────────────────────────────────────────
echo "이 작업은 GitHub Actions 빌드를 트리거합니다."
read -p "origin에 push 하시겠습니까? [y/N] " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin master "$TAG"
    echo ""
    echo "🚀 ${TAG} push 완료 — GitHub Actions가 빌드 및 릴리즈를 생성합니다."
    echo "   https://github.com/Leonamin/lms-summarizer/actions"
else
    echo "Push를 건너뛰었습니다. 수동으로 push하려면:"
    echo "  git push origin master ${TAG}"
fi
