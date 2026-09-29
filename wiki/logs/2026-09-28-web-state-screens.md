---
type: Log
title: "웹 대시보드 상태 화면 — 로딩·서버 오류·빈 결과"
description: "초기 로딩 스켈레톤, 서버 오류 배너, 검색·필터 빈 결과 상태 구현 (PR #44)"
timestamp: 2026-09-28
okf_version: "0.1"
---

# 웹 대시보드 상태 화면

## 배경

8-A 디자인(B, Soft Editorial) 방향에서 정상 상태 외의 세 화면이 비어 있었다. 초기 로딩,
서버 연결 끊김, 검색·필터 결과 없음.

## 구현

- **초기 로딩 스켈레톤**: App의 `ready` 전까지 통계 카드(`.skeleton-num`/`.skeleton-label`),
  작업 목록 6행(`.skeleton-row`), 상세 패널(`.result-skeleton`)을 렌더한다. shimmer는
  `prefers-reduced-motion: no-preference`에서만 동작하고, 헤더·파이프라인·입력 카드는 그대로
  그려 레이아웃이 흔들리지 않는다.
- **서버 오류 배너**: 연결이 끊기면 헤더 아래 `.server-banner`(아이콘 + "서버에 연결하지 못했습니다." +
  "다시 연결")를 표시하고, 버튼으로 즉시 재연결한다. 자동 재연결도 병행한다.
- **검색·필터 빈 결과**: 작업 목록 `.empty`에 `.secondary` "검색·필터 초기화" 버튼. 작업이 아예 없을
  때는 초기화 버튼 없이 안내만 표시한다.
- DESIGN.md에 States 섹션을 추가했다.

## 검증

- `tsc`·Vite 빌드 통과.
- 필터 빈 상태는 실제 앱에서, 로딩 스켈레톤(6행+통계)과 오류 배너는 API가 죽은 Vite dev 환경에서
  렌더를 확인했다.

## 관련 문서

- [DESIGN.md](../../DESIGN.md) — States (로딩 · 오류 · 빈 결과)
- [ADR-004](../decisions/004-auto-play-and-ux-improvements.md)
