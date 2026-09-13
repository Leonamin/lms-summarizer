---
type: Log
title: "Remove Ollama and OpenAI Compat Layer"
description: "Ollama 제거 및 OpenAI 호환 레이어 자동 폴백 지원"
timestamp: 2026-09-13
okf_version: "0.1"
---

# Remove Ollama and OpenAI Compat Layer

## 배경

로컬 모델(Ollama) 사용 중단. 대신 OpenAI API 호환 레이어(`/v1/chat/completions`, `/v1/responses`)로 OpenRouter·OpenCode GO·OpenAI 공식 API를 지원.

## 결정 사항

- `/v1/responses` 우선 시도 → 미지원 서버면 `/v1/chat/completions` 자동 폴백 (인스턴스 캐시)
- Ollama 완전 제거 (provider·레지스트리·GUI)
- 엔드포인트는 힌트만 제공 (프리셋 드롭다운 없음)

## 변경 내용

- [x] `custom_provider.py` 재작성 — responses→chat/completions 자동 폴백, 기본 URL을 OpenAI 공식으로 변경
- [x] `ollama_provider.py` 삭제 + `providers/__init__.py` 정리
- [x] GUI 정리 — model_selector·ai_settings·main_view에서 ollama 제거, custom 라벨 "OpenAI 호환 (OpenRouter 등)"
- [x] 문서 갱신 — README 엔진 표, CLAUDE.md 설계 의도
- [x] 검증 — 레지스트리/폴백 로직 모킹 테스트 통과, ollama 잔존 참조 제거

## 결과 요약

- CustomProvider: `responses.create` 실패 시 `chat.completions.create`로 폴백하며 결과를 캐시. 기본 base_url `https://api.openai.com/v1`.
- 저장된 설정의 구 `ollama` 엔진은 model_selector의 알 수 없는 엔진 무시 로직으로 gemini 기본값 폴백.
