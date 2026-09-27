---
type: Log
title: "8단계 개선 작업 계획 추가"
description: "타이포그래피·UX/UI 개선과 신규 강의 감지·자동 재생·자동 저장 계획·결정 기록"
timestamp: 2026-09-27
okf_version: "0.1"
---

# 8단계 개선 작업 계획 추가

## 변경 요약

7단계 완료 이후 개선 작업을 8단계로 추가하고, 상세 계획·TODO·ADR·별도 상세 계획을 연결했다.
아직 구현 전이므로 8단계는 미착수로 둔다.

- 추가: `plans/auto-play-new-lectures.md` — 신규 강의 감지·자동 재생·자동 저장 상세 계획
- 추가: `decisions/004-auto-play-and-ux-improvements.md` — 8단계 범위와 자동 재생 정책 ADR
- 갱신: `plans/core-web-dashboard-plan.md` — 8단계 섹션(8-A/8-B), 범위·초기 설계 과제
- 갱신: `plans/core-web-dashboard-todo.md` — 거시 TODO 8, 단계별 목록 8, 결과표 8행
- 갱신: `plans/index.md`, `decisions/index.md`, `index.md`

## 추가한 범위

- **8-A 타이포그래피·UX/UI 개선.** `frontend/src/style.css`가 `"Pretendard"`를 폰트명으로만
  선언하고 실제 로드가 없어 대체 폰트로 렌더되며 8~13px 크기가 많다는 점을 근거로, Pretendard
  실제 로드·타이포그래피 토큰화·목록 정보 재구성을 계획한다.
- **8-B 신규 강의 감지·자동 재생·자동 저장.** 주기 감지, 자동 재생 큐(동시 1건), 자동 저장,
  재생 팝업 HTML 파싱 확인, 다운로드와의 교착 방지를 계획한다. 기존 `courses.py` 조회 큐·캐시와
  `jobs.py` 다운로드 슬롯, `video_parser.py`의 `try_dismiss_confirm_dialog`를 근거로 연결한다.

## 확정 사항과 남은 조사

[ADR-004](../decisions/004-auto-play-and-ux-improvements.md)(Accepted)로 두 개선 범위와 세부 방향을
확정했다. 8-A는 Pretendard **자체 호스팅** 로드, **작업 목록·단계 모니터** 우선, **마스터-디테일 +
컴팩트 표** 재구성이다. 8-B는 **수동 토글**, **선택 과목·설정 주기** 감지, 자동 재생 목적 **출석·진도
+ 자동 저장**, 자동 저장 범위 **설정 선택**(다운로드만/전체), 재생 **동시 1건**, 팝업 유형별 처리와
**3회 반복 시 일시중지**다. LMS 버그로 실제 재생이 아닌데 "재생 중"으로 표시되는 경우에는 대기하지
않고 진행한다.

팝업의 실제 DOM 선택자·파싱 가능 여부, 감지 주기 기본값, Chrome/CDP 락 순서, 출석 인정 재생 시간
기준은 미확정으로 [상세 계획](../plans/auto-play-new-lectures.md)의 남은 조사에 남겼다.

이번 기록은 계획 추가이며 구현·검증 완료가 아니다. 8단계 결과표는 미착수로 둔다.

## 관련 문서

- [상세 계획](../plans/core-web-dashboard-plan.md) · [진행 TODO](../plans/core-web-dashboard-todo.md)
- [ADR-004](../decisions/004-auto-play-and-ux-improvements.md)
- [자동 재생 상세 계획](../plans/auto-play-new-lectures.md)
