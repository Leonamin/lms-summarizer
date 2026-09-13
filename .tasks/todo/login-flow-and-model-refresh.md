---
id: login-flow-and-model-refresh
title: 로그인 플로우 재구현 + 모델 최신화(2026-09) + CLAUDE.md 간소화
labels: [fix, feat, docs, video-pipeline, summarize-pipeline]
priority: p1
created: 2026-09-13
depends_on: []
---

# 로그인 플로우 재구현 + 모델 최신화(2026-09) + CLAUDE.md 간소화

## 배경

- 숭실대 LMS 로그인 사이트가 변경됨: discovery 페이지(사이트 선택) → 통합 로그인 선택 → smartid 폼 순서로 변경.
- 하드코딩된 AI 모델 목록이 수개월 전 기준(gemini-2.5 등)이라 2026-09 기준으로 최신화 필요.
- CLAUDE.md가 비대해져 간소화 필요.

## 체크리스트

- [x] 로그인 페이지 실제 구조 확인 (discovery: `.btn-ssu-main`, gw.php: `.login_btn a` 통합 로그인, smartid: `input#userid`/`input#pwd`/`a.btn_login`)
- [x] `login.py` 재구현 — 3단계 조건부 플로우, 기존 셀렉터는 smartid 단계에 그대로 유효
- [x] 모델 최신화: Gemini 3.8 Flash / OpenAI GPT-5.6 Luna / Claude Sonnet 5 / Grok 4.6 (provider 4개 + 기본값 4곳)
- [x] CLAUDE.md 간소화 + 새 로그인 플로우 반영
- [x] README 모델 표 동기화
- [x] import 및 provider 레지스트리 검증

## 결과 요약

- `src/video_pipeline/login.py`: discovery(`.btn-ssu-main`) → gw.php 통합 로그인(`.login_btn a`) → smartid 폼의 3단계 조건부 플로우로 재작성. `_navigate_and_wait` 헬퍼로 네비게이션 대기 통일. 실패 감지에 smartid 도메인 잔류 체크 추가.
- 모델 갱신 (2026-09 기준): gemini-3.8-flash(기본)/3.6-flash/3.1-pro-preview, gpt-5.6-luna(기본)/terra/sol, claude-sonnet-5(기본)/opus-5/haiku-4-5, grok-4.6(기본)/4.5/4.1-fast. 기본값 참조 4곳(summarizer.py, pipeline.py, processing_worker.py, gui/state.py) 동기화.
- Ollama(qwen2.5)는 미검증 상태로 유지 — 추후 태스크로 검토 제안.

## 남은 검증 (실사 필요)

- [ ] 실제 LMS에서 브라우저 로그인 E2E 테스트 (headless=False 실행 필요)
