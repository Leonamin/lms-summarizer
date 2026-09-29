---
type: Log
title: "이어서 재개(resume) — 끊긴 단계부터 복구"
description: "실패·취소·중단 작업을 마지막 완료 단계부터 산출물 재사용으로 재개"
timestamp: 2026-09-29
okf_version: "0.1"
---

# 이어서 재개(resume)

## 배경

수정 후 재배포(`docker compose up -d --build`) 때 컨테이너가 재생성되며 **실행 중이던 작업이 중단**된다.
재시작 시 `_recover()`가 `running/cancelling` → `interrupted`로 바꾸지만 재큐잉하지 않아 자동으로 이어지지 않는다.

무조건 자동 재시작하면 **누적된 과거 실패까지 한꺼번에 재큐잉**되고, 게다가 기존 `retry`는 `initial_stage`부터
새 시도를 만들어 URL 작업은 **재다운로드**부터 다시 한다(Chrome 슬롯이 병목).

## 결정

- **자동 재시작은 하지 않는다(기본).** 누적 실패가 자동으로 올라가지 않도록 복구는 사용자가 명시적으로 트리거한다.
- 대신 **끊긴 단계부터 값싸게 재개**하는 `resume`을 제공한다.

## 구현

- `JobService.resume(context, job_id, attempt_id)` + `_resume_point(attempt_id, end_stage)`
  - `retryable`(failed/cancelled/interrupted)만 대상.
  - 현재 시도의 **완료 단계 중 마지막**의 산출물이 디스크에 남아 있으면 그 `단계+1`부터 새 시도 생성(산출물 재사용).
  - 산출물이 없으면 `no_resume_point`. 자격 증명·`queue_full`·`attempt_conflict`는 `retry`와 동일.
- API: `POST /api/v1/jobs/{id}/resume` `{attempt_id}` (+ `Idempotency-Key`).
- UI: 상세 액션에 `이어서 재개`(`.secondary`) + `처음부터`(`.quiet`)를 함께 노출. 재개 불가면 `다시 시도`만.

## 후속(미구현)

- 재시작 스코프 마킹(`boot_id`)으로 "이번 재시작으로 중단된 것"만 자동/원클릭 복구.
- 배너 + 일괄 재시도, attempt 상한·영구 오류(`credentials_missing` 등) 자동 제외.
- 배포 시 `docker compose stop` → `up -d --build`로 graceful 종료 유도.

## 검증

- unittest **89개 통과**(신규 2: 마지막 완료 단계부터 재개·완료 단계 없으면 거부).
- 실제 중단 작업에서 UI `이어서 재개 (3단계부터)` / `처음부터` 노출 확인.
