---
type: Log
title: "Codebase Modernization"
description: "README·CLAUDE.md·빌드 스크립트 정리 및 Chrome 경로 분기"
timestamp: 2026-09-13
okf_version: "0.1"
---

# Codebase Modernization

## 배경

whisper.cpp 제거 및 faster-whisper 전환 이후 문서와 빌드 스크립트가 코드에 뒤처져 있었음.

## 변경 내용

- [x] README.md 갱신 — STT 엔진 표 (whisper.cpp → faster-whisper), 요약 엔진 표 갱신, 기술 스택 표 갱신
- [x] CLAUDE.md 갱신 — 해결된 알려진 버그(OPENAI_API_KEY 미정의) 제거, Chrome 경로 분기 완료 반영
- [x] 빌드 스크립트 pywhispercpp 잔존 제거 (scripts/build_windows.ps1, build_mac_pyinstaller.sh) + torch CPU 설치 잔존 제거
- [x] Chrome 경로 Windows 분기 (video_pipeline/pipeline.py, course_scraper.py)

## 결과 요약

- README.md: STT 표를 faster-whisper/OpenAI 호환/OpenAI Whisper API/ReturnZero로 갱신, 기술 스택·FAQ 모델 크기 갱신
- CLAUDE.md: OPENAI_API_KEY 버그 항목 삭제(user_setting.py에 정의됨 확인), Chrome 경로 분기 완료로 갱신
- 빌드 스크립트: pywhispercpp 모델 사전 다운로드 단계 제거(런타임 다운로드 정책), build_windows.ps1의 torch CPU 설치 제거(spec에서 torch excludes)
- pipeline.py / course_scraper.py: `_DEFAULT_CHROME_PATH`를 sys.platform 기반 분기(win32/darwin/linux)
