---
type: Log
title: "재개·재시도 '현재 설정 사용' 옵션"
description: "실패 작업을 현재(최신) 설정 revision으로 재개/재시도하는 체크박스 추가와 리뷰 반영"
timestamp: 2026-09-29
okf_version: "0.1"
---

# 재개·재시도 '현재 설정 사용'

## 배경

작업은 제출 시점 설정(`settings_revision_id`)을 고정하므로, 이미 제출된 작업은 `다시 시도`/`이어서 재개`를
해도 **원래 설정(예: 할당량이 소진된 Gemini)** 으로만 실행된다. 엔진·모델을 바꿔 다시 돌리려면 새 작업을
제출해야 했다.

## 결정

- 작업 상세의 `이어서 재개`/`다시 시도` 옆에 **`현재 설정 사용` 체크박스(기본 꺼짐)** 를 추가한다.
- 켜면 최신 설정 revision으로 작업 설정을 교체한 뒤 새 시도를 만든다. 끄면 기존처럼 제출 당시 설정을 유지한다(하위 호환).
- 재개는 산출물(영상/오디오/전사본)을 재사용하고 요약 단계만 새 설정으로 실행하므로 의미상 안전하다.

## 구현

- 스키마 `RetryCommand(attempt_id, use_current_settings=False)`. `cancel`은 기존 `AttemptCommand` 유지(추가 필드 거부).
- 라우트 `retry`/`resume`가 플래그가 켜지면 `WebSettings`의 최신 revision을 `_adopted_revision()`으로 해석해 전달.
- `JobService.retry/resume(settings_revision=None)`:
  - `_revision_for_attempt()` — 소유자 검증, 미지정 시 고정 revision 재사용.
  - `_save_revision()` — 새 revision을 DB에 저장(멱등), 트랜잭션 안에서 원자 처리.
  - `_bind_revision()` — `job.settings_revision_id` 교체 + **`keep_source`/`keep_audio`도 현재 설정에서 함께 반영**.
  - 멱등 fingerprint에 revision id를 포함(설정이 다르면 재생 충돌).

## 리뷰 반영

- (major) 교체 시 보관 플래그 미반영 → `_bind_revision`에서 동기화.
- (minor) `_attempt_revision` → `_revision_for_attempt` 개명, frozen revision 누락 시 `settings_conflict`, 타입 가드.
- (suggestion) 라우트 중복 헬퍼 추출, retry 경로·보관 플래그 테스트 추가, 버튼 title에 설정 교체 안내.

## 검증

- unittest **102개 통과**(신규: 현재 설정으로 재개 시 revision·보관 플래그 교체, 현재 설정으로 재시도).
- 로컬 E2E: 깨진 엔드포인트로 제출 → 실패 → OpenCode Go로 `현재 설정 사용` 재시도 → `completed`, revision 교체, 실제 한국어 요약 생성.
- 프런트엔드 빌드 통과.
