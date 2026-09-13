---
type: Log
title: "Wiki and Task Migration"
description: "위키 초기화 및 .tasks(Plank) 마이그레이션"
timestamp: 2026-09-14
okf_version: "0.1"
---

# Wiki and Task Migration

## 배경

작업 관리를 .tasks(Plank)에서 프로젝트 위키로 전환. 위키를 OKF v0.1 스타일로 초기화하고 기존 태스크를 이관함.

## 변경 내용

- 위키 구조 초기화: `concepts/`, `decisions/`, `references/`, `plans/`, `logs/` + 각 디렉토리 index.md
- 프로젝트 설정 추가: `.agents/wiki-path`, `.agents/wiki-structure.md`
- 완료 태스크 6건 → logs/ 이관 (본 문서 아래 목록)
- 미완료 태스크 7건 → plans/ 이관
- `.tasks/` 디렉토리 삭제 (휴지통의 폐기 소스 파일 3건 포함 — git 히스토리로 보존)
- CLAUDE.md에서 Plank 섹션 제거

## 이관된 완료 태스크

- CDP 비디오 URL 추출 복원 (2026-03-27) → [로그](2026-03-27-cdp-video-extractor-revival.md)
- 주차학습 목록 캐싱 (2026-03-27) → [로그](2026-03-27-lecture-list-cache.md)
- whisper.cpp 제거 + distil 모드 추가 (2026-03-27) → [로그](2026-03-27-remove-whisper-cpp-add-distil.md)
- distil-large-v3 한국어 미지원 제거 (2026-W16) → [로그](2026-04-16-distil-model-korean-broken.md)
- 코드/문서 최신화 (2026-09-13) → [로그](2026-09-13-codebase-modernization.md)
- Ollama 제거 + OpenAI 호환 레이어 (2026-09-13) → [로그](2026-09-13-remove-ollama-openai-compat-layer.md)
