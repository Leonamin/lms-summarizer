---
type: Log
title: "작업 제목·과목·주차 표시"
description: "URL 작업 자동 이름 변경과 과목·주차 메타데이터 저장·표시 (PR #51)"
timestamp: 2026-09-28
okf_version: "0.1"
---

# 작업 제목·과목·주차

## 배경

URL로 제출한 작업이 전부 "LMS lecture"로 보여 목록에서 구분이 어려웠다. 과목·주차 정보도 화면에
드러나지 않았다.

## 구현

- **자동 이름 변경**: 다운로드(1단계)가 완료될 때 작업 이름이 일반값("LMS lecture")이면 **받은
  아티팩트 파일명(강의 제목)으로 자동 변경**한다(`_publish`). 과거에 완료된 작업은 소급 변경하지 않는다.
- **메타데이터**: `Source`/`JobCreate`에 `display_name`·`course_name`·`week_title` 선택 필드를 추가하고
  상세 응답(`detail`)에 `course_name`·`week_title`을 포함한다.
- **전달 경로**: 자동 재생 자동 저장은 재생 기록의 제목·과목·주차를, 과목·주차 화면 제출은 선택 강의의
  제목·과목·주차를 넘긴다.
- **표시**: 목록은 강의 제목 한 줄 말줄임 + `title` 툴팁(과목·주차는 미표시, 넘침 방지). 상세 헤더에는
  `.result-subtitle`로 "과목 · 주차" 보조 줄(있을 때만, 말줄임 + 툴팁).

## 검증

- 테스트: 메타데이터 저장·자동 이름 변경 포함 전체 **87개 통과**.
- 실제 LMS URL 제출 → 초기 'LMS lecture'/과목·주차 저장 → 다운로드 후 '선대_3_1'로 자동 변경 확인.

## 관련 문서

- [DESIGN.md](../../DESIGN.md) — 목록 이름 표시 / `.result-subtitle`
- [ADR-003](../decisions/003-web-runtime-and-job-contract.md) — 작업 상태·메타데이터 계약
