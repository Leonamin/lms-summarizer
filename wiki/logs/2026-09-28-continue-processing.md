---
type: Log
title: "이어서 처리(continue) 기능"
description: "완료된 초기 단계 작업을 산출물 재사용으로 뒤 단계까지 이어서 실행"
timestamp: 2026-09-28
okf_version: "0.1"
---

# 이어서 처리(continue) 기능

## 배경

다운로드만(또는 STT까지만) 해둔 작업을 나중에 요약까지 이어서 처리하고 싶다는 요구가 있었다.
기존 `retry`는 원래 **시작 단계부터 다시** 실행하고 `end_stage`도 바꾸지 못해, URL 작업은 재다운로드,
파일 작업은 재업로드가 필요했다.

## 구현

- `JobService.continue_job(context, job_id, attempt_id, end_stage)`
  - **완료(`completed`)된 작업**만 대상. 현재 시도의 **마지막 완료 단계 산출물**을 입력으로 삼아
    `마지막 단계+1`부터 목표 단계까지 실행하는 **새 시도(attempt N+1)**를 만든다.
  - 같은 작업의 **`end_stage`를 확장**하고 `current_attempt_id`를 새 시도로 바꾼다. 제출 당시 고정
    설정·비밀 버전을 그대로 유지한다.
  - 목표는 2(오디오 변환)/3(음성 인식)/4(요약) 중 자유 선택이며 현재 완료 단계보다 커야 한다.
  - 검증: 완료 상태·현재 시도·목표 단계·마지막 산출물 존재·자격 증명·활성 작업 한도.
- API: `POST /api/v1/jobs/{id}/continue` `{attempt_id, end_stage}` (+ `Idempotency-Key`).
- UI: 작업 상세에 `이어서 처리` 드롭다운 + 버튼. `완료`이고 `end_stage < 4`일 때만 노출.

## retry와의 구분

- `retry`: 실패·취소·중단 작업을 **원래 입력 단계부터** 다시 실행(완료 단계 자동 재사용 안 함).
- `continue`: 완료 작업을 **마지막 완료 단계 다음부터** 실행하며 **이미 만든 산출물을 재사용**한다.
  (1단계 계약의 "재시도는 완료 단계를 자동 재사용하지 않는다"는 재시도 한정이며, 이어서 처리는 명시적
  사용자 동작으로 재사용한다.)

## 검증

- unittest **86개 통과** (continue 전용 테스트 포함: 산출물 재사용, end_stage 확장, 단계 진행, 잘못된 목표 거부).
- 실제 LMS: `end_stage 3`(요약 전) 완료 작업을 `end_stage 4`로 이어서 처리 → **시도 3에서 stage 4만**
  실행되어 완료(재다운로드·재STT 없음). 고정 설정이 챗봇(clipboard)이어서 결과는 `manual_ready`.

[진행 TODO](../plans/core-web-dashboard-todo.md) · [상세 계획](../plans/core-web-dashboard-plan.md)
