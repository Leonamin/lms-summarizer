---
type: Log
title: "요약 AI 실패 진단 — Gemini 503과 재시도·오류 코드"
description: "이어서 재개 실패 원인(Gemini 3.8-flash 503) 규명, provider 재시도·백오프와 안전 오류 코드 도입"
timestamp: 2026-09-29
okf_version: "0.1"
---

# 요약 AI 실패 진단 (Gemini 503)

## 증상

"이어서 재개"한 작업들이 **모두 4단계(요약)에서 ≈2초 만에 `stage_failed`** 로 실패하고 사유가 안 보였다.

## 진단

재개 로직 문제가 아니었고, "실패 지점이라서"도 아니었다. 재개 시도는 **4단계부터 정상 시작**(1~3단계 재사용)했고
4단계만 실패했다. 실제 작업의 고정 설정·키로 provider를 직접 호출해 재현했다.

| 모델 | 결과 |
| --- | --- |
| `gemini-3.8-flash` (작업이 쓰던 기본 모델) | ❌ 503 UNAVAILABLE ("model is currently experiencing high demand") |
| `gemini-3.6-flash` | ✅ 정상 |
| `gemini-3.1-pro-preview` | ❌ 429 RESOURCE_EXHAUSTED (쿼터) |

원인은 두 가지였다.
1. Gemini `gemini-3.8-flash`의 **일시적 과부하(503)**.
2. 모든 provider가 **재시도를 끄고 있었다** — gemini `HttpRetryOptions(attempts=1)`, openai/anthropic
   `max_retries=0`. 게다가 워커가 stdout/stderr를 버리고 모든 예외를 `stage_failed`로 뭉개 사유가 안 보였다.

## 조치

- **재시도·백오프**: gemini `HttpRetryOptions(attempts=4, initial_delay=1, max_delay=15, exp_base=2)`,
  openai·claude·grok·custom `max_retries=3`. (SDK 기본 재시도 대상에 408/429/5xx 포함)
- **오류 사유 노출**: executor가 provider 예외를 `ai_error_code()`로 안전 코드로 환원 —
  `ai_unavailable`(5xx/네트워크) · `ai_quota`(429) · `ai_auth`(401/403) · `ai_timeout`(408/타임아웃).
  워커 `SAFE_ERRORS`에 추가하고, `_terminal`이 코드별 한국어 `safe_message`(`STAGE_ERROR_MESSAGES`)를 넣는다.

## 검증

- 재시도 적용 후 실제 `gemini-3.8-flash` 호출이 **30.5초에 성공**(503 스파이크를 백오프로 통과).
- unittest **94개 통과**(신규: `ai_error_code` 매핑 4건, 코드별 `safe_message` 노출 1건).

## 남은 선택지

- 모델 폴백(3.8 → 3.6)과 "최신 설정으로 재시도"는 하지 않았다(작업 설정은 제출 시 고정).
