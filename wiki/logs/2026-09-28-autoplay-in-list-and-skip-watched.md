---
type: Log
title: "자동 재생을 작업 목록에 표시 + 이미 본 강의 건너뛰기"
description: "AUTO PLAY 그룹으로 재생 큐를 목록에 노출하고, 자동 감지가 출석·완료 강의를 제외 (PR #45, #46)"
timestamp: 2026-09-28
okf_version: "0.1"
---

# 자동 재생 목록 표시와 건너뛰기

## 배경

자동 재생이 작업 목록에 보이지 않아 "대기 작업이 왜 안 도는지" 혼란스러웠다(#45).
또 자동 감지가 `seen` 기록만 확인해 **이미 다 본(출석/완료) 강의까지 재생 대상으로 잡았고**,
재생이 단일 Chrome 슬롯을 오래 점유해 뒤의 다운로드 작업이 밀렸다(#46).

## 구현

- **AUTO PLAY 그룹(#45)**: 재생 큐가 비어 있지 않으면 작업 목록 표 머리글 아래에
  `.playback-group`(brand-50 배경)으로 `재생 중`/`재생 대기` 배지 + 강의 제목 + 만든 시각을 표시한다.
  행은 `.playback-row`로 비인터랙티브이고, "단일 슬롯에서 순차 실행"을 안내한다.
  `WorkspacePage`가 `/playback`을 5초마다 폴링해 **활성 재생만** 전달한다. 공용 `Playback` 타입은
  `types.ts`로 옮겼다.
- **건너뛰기(#46)**: `detection.is_watched`(completion=completed 또는 출석 인정 토큰이면 True)와
  `detection.select_playback_videos`(재생이 필요한 신규 영상만 선택)를 추가하고 autoplay가 이를 사용한다.

## 검증

- #45: 컨테이너에서 재생 중 1 + 대기 8 행이 작업 목록에 표시되고, 그 아래 대기 작업과 구분되어
  보이는 것을 확인.
- #46: 테스트 2종 추가(헬퍼·엔진), 전체 **85개 통과**. 대기 재생 정리는 운영에서 별도 수행(queued 제거).

## 관련 문서

- [ADR-004](../decisions/004-auto-play-and-ux-improvements.md)
- [자동 재생 상세 계획](../plans/auto-play-new-lectures.md)
