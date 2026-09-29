---
type: Log
title: "OpenAI 호환 호출 방식·OpenCode Go 세션, 산출물 보관 토글과 재개 수정"
description: "OpenCode Go·커스텀 LLM 요약 실패 진단, api_mode·세션 헤더, 영상/오디오 보관 토글, 설정 미저장 표시, 재개 지점·단계 표시 버그 수정"
timestamp: 2026-09-29
okf_version: "0.1"
---

# OpenAI 호환 provider·보관 토글·재개 수정

## 1. OpenCode Go / 커스텀 LLM 요약 실패 진단

배포된 `custom`(OpenAI 호환) 엔드포인트 두 곳이 모두 실패했다. 실제 키로 직접 호출해 원인을 분리했다.

| 엔드포인트 | 결과 | 원인 |
| --- | --- | --- |
| `https://api-max.cuteshrew.com/v1` | ❌ 400 | **공급자 서버 메모리 부족** — 모든 모델이 `Model loading was stopped due to insufficient system resources`(≈26~31GB 필요). 앱 재시작·재시도로 해결 불가 |
| `https://opencode.ai/zen/go/v1` | ❌ 400 `MissingSessionID` | **`x-opencode-session` 헤더 누락** |

- 처음엔 Cloudflare `403 error code: 1010`처럼 보였으나 Python `urllib` 기본 UA만 차단된 것이고, 앱이 쓰는 OpenAI SDK/httpx는 정상 통과였다.
- OpenCode Go는 모델별 라우트가 다르다: GPT·Grok·Muse = `/v1/responses`, DeepSeek·GLM·Kimi·MiMo 등 = `/v1/chat/completions`, Qwen·MiniMax = `/v1/messages`(Anthropic형, 미지원). `x-opencode-session`을 붙이면 정상 응답한다.

## 2. 조치 — OpenAI 호환 provider

- **`custom_api_mode` 설정 추가**: `auto`(responses→chat 폴백) / `chat` / `responses`. 설정 UI에 `요약 API 호출 방식` 노출.
- **OpenCode Go 세션 헤더 자동 주입**: 호스트가 `opencode.ai`면 `x-opencode-session`(UUID) 자동 생성, `extra_headers`로 덮어쓰기 가능.
- 오류 진단을 위해 provider를 실제 엔드포인트로 직접 호출하는 방식으로 검증.

## 3. 산출물 보관 토글 (`keep_source` / `keep_audio`)

- 기존에는 성공 시 **변환 오디오(wav)가 무조건 삭제**되고 원본 영상만 `keep_source`로 보관됐다.
- **영상(`keep_source`)과 변환 오디오(`keep_audio`)를 독립 토글**로 분리. `_apply_retention()`이 산출물 `kind`별로 각 플래그를 적용한다.
- 주의: 작업은 **제출 시점 설정을 고정**하므로, 이미 제출된 작업에는 소급되지 않는다(기존 작업 `keep_audio` 미설정 → 완료 시 오디오 삭제).

## 4. 설정 화면 미저장 표시·고정 저장바

- `draft`와 저장본을 필드별로 비교해 **"저장되지 않은 변경 N개"** 배지와 문구를 표시하고, 버튼을 `변경 저장`으로 바꾼다.
- 저장바를 `position: sticky`로 고정해 스크롤 위치와 무관하게 항상 보이게 했다.

## 5. 재개 실패 후 재개 불가·작업물 숨김 버그 (사용자 신고)

**증상**: 다운로드→오디오→STT 후 요약 실패 → `이어서 재개` → 또 요약 실패 → 재개가 사라지고 `다시 시도`만 가능, 다운로드/오디오/STT 단계가 삭제된 것처럼 보임.

**원인**: 재개/표시 로직이 **현재 시도(current attempt)만** 봤다. 재개는 4단계만 있는 새 시도를 만들고, 그 시도가 실패하면 완료 단계가 없어 재개 지점이 사라진다. UI도 최신 시도만 그려 이전 단계·산출물이 숨겨졌다. **파일은 삭제된 것이 아니었다** — DB 전수 확인 결과 실패 작업의 `video/audio/transcript`는 모두 `complete/live`.

**수정**:
- `_resume_point(job, end_stage)`: 작업의 **모든 시도(최신순)**에서 살아있는 최고 완료 단계를 재개 지점으로.
- `StageTrack`: 시도 전체를 병합(최신 시도 우선, 없으면 살아있는 완료 산출물 기준).
- 결과 목록(`WorkspacePage`): 작업 전체 산출물을 종류별 1개로, 현재 시도 산출물 우선.
- `ResultPanel.resumableStage`: 전체 시도 기준으로 재개 버튼 노출.

## 검증

- unittest **100개 통과**(신규: `api_mode` 라우팅·세션 헤더·공장 전달, 재개 실패 후 재개).
- OpenCode Go(`deepseek-v4.1-flash`)로 로컬 서버 업로드→4단계 요약 **end-to-end 성공**(한국어 요약 생성).
- 배포(`docker compose up -d --build`) 후 실제 화면 확인: 실패한 `선대_1_1`에서 `다운로드 ✓·오디오 변환 ✓·음성 인식 ✓·요약 실패`와 `이어서 재개` 버튼, 영상/오디오/STT 탭 정상 표시.

## 남은 것

- 400 계열(모델 로드 실패·잘못된 모델 ID) 오류 사유가 화면에 안 보인다(`stage_failed`로 뭉갬).
- 재개/재시도로 완료된 작업은 `_apply_retention()`이 "현재 시도"만 평가해 **이전 시도의 중간 산출물이 정리되지 않고 남는다**(중복 누적).
- OpenCode Go `x-opencode-session`은 provider 인스턴스(요약 1회)마다 새 UUID를 쓴다. 대화 단위 캐시 최적화가 필요하면 세션 ID 정책을 재검토.
