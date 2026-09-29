---
type: Concept
title: "요약 AI Provider 계층"
description: "요약 엔진(Provider) 구조, OpenAI 호환(custom) 엔드포인트와 호출 방식, OpenCode Go 세션 헤더, 오류 코드"
tags: [summary, provider, openai-compatible, opencode-go, api]
timestamp: 2026-09-29
---

# 요약 AI Provider 계층

## 엔진 레지스트리

`src/summarize_pipeline/providers/`가 엔진 이름 → Provider 클래스를 매핑한다.

| 엔진 | 클래스 | 비고 |
| --- | --- | --- |
| `gemini` | GeminiProvider | Google Gemini(기본 모델 `gemini-3.8-flash`) |
| `openai` | OpenAIProvider | `api.openai.com` 공식 전용(고정 base_url) |
| `claude` | ClaudeProvider | Anthropic |
| `grok` | GrokProvider | xAI 고정(`https://api.x.ai/v1`) |
| `custom` | CustomProvider | **OpenAI 호환 임의 엔드포인트**(OpenRouter, OpenCode Go, Ollama, vLLM 등) |
| `clipboard` | ClipboardProvider | 브라우저로 열어 수동 요약 |

`create_provider(engine, api_key, model_name, base_url, api_mode, request_timeout)`가 인스턴스를 만든다.
`base_url`과 `api_mode`는 `custom`에만 전달된다. 실행은 `src/core/runtime/executor.py`의 4단계가 담당하고,
설정은 제출 시점에 고정된다.

## OpenAI 호환(custom) 엔드포인트

- base_url + model ID를 사용자가 직접 입력한다. API 키는 선택(없으면 `not-needed`)이라 키 불필요 서버도 지원한다.
- 내부적으로 OpenAI Python SDK(`openai`)를 쓴다.

### 호출 방식(`custom_api_mode`)

| 값 | 동작 |
| --- | --- |
| `auto`(기본) | `/v1/responses`를 먼저 시도하고, **미지원 라우트**(404/405/501)일 때만 `/v1/chat/completions`로 폴백. 폴백 결과는 인스턴스에 캐시 |
| `chat` | `/v1/chat/completions`만 사용 |
| `responses` | `/v1/responses`만 사용 |

- 인증·쿼터·서버·모델 오류는 **폴백하지 않고 그대로 올린다**(유료 요청 중복 방지).
- 서버마다 지원 라우트가 다르므로, 응답 프로토콜이 고정된 서버는 `chat`/`responses`를 명시한다.
  예: OpenCode Go의 GPT계열은 `responses` 전용, 대부분의 프록시는 `chat/completions`.

### OpenCode Go 세션 헤더

`https://opencode.ai/zen/go/v1`는 대화 라우팅·프롬프트 캐시를 위해 요청마다 **`x-opencode-session`** 헤더를
요구한다. 없으면 `400 MissingSessionID`로 거부된다. `CustomProvider._default_headers()`가 base_url 호스트가
`opencode.ai`(`*.opencode.ai` 포함)일 때 요청별 UUID를 자동 주입한다. `extra_headers`로 같은 이름을 주면 그 값이 우선한다.

## 오류 코드

`executor.ai_error_code()`가 provider 예외를 안전 코드로 환원하고 `STAGE_ERROR_MESSAGES`가 한국어 문구를 붙인다.

| 코드 | 조건 |
| --- | --- |
| `ai_quota` | 429 / RESOURCE_EXHAUSTED |
| `ai_auth` | 401 / 403 / UNAUTHENTICATED / PERMISSION_DENIED |
| `ai_unavailable` | 5xx / UNAVAILABLE / 네트워크 연결 오류 |
| `ai_timeout` | 408 / 타임아웃 |

400 계열(모델 로드 실패, 잘못된 모델 ID 등)은 구분 코드 없이 `stage_failed`로 뭉개져 화면에 사유가 안 보인다(미개선).

## 관련 문서

- [decisions/003-web-runtime-and-job-contract.md](../decisions/003-web-runtime-and-job-contract.md) — 실행·보관 계약
- [logs/2026-09-29-ai-provider-retention-and-resume-fix.md](../logs/2026-09-29-ai-provider-retention-and-resume-fix.md)
- [logs/2026-09-29-ai-error-retry.md](../logs/2026-09-29-ai-error-retry.md)
