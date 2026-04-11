---
id: lecture-list-cache
title: 주차학습 목록 캐싱 (논의 필요)
labels: [feature, performance, discussion]
priority: p2
created: 2026-03-27
depends_on: []
---

# 주차학습 목록 캐싱

## 배경
매번 주차학습 페이지에 진입해서 주차 목록을 불러오는 과정이 느림.
캐싱으로 재방문 시 속도를 개선할 수 있을지 논의 필요.

## 결정 사항

- **전략**: 옵션 2 (앱 세션 인메모리 캐시)
- **캐시 키**: `course.id` (강의 ID 기준)
- **만료 정책**: 앱 수명 = TTL. 앱 재시작 시 자동 소멸
- **저장 위치**: `CourseListView._lecture_cache` (메모리 dict, persist 안 함)
- **갱신 트리거**: 강의 목록 화면 새로고침 버튼 (`force_refresh=True`)
- **일관성**: persist 없으므로 stale 위험 최소. 앱 재시작이 곧 캐시 무효화

## 체크리스트
- [x] 캐싱 전략 결정 (옵션 2: 앱 세션 인메모리 캐시)
- [x] 구현 — `_lecture_cache` dict + 캐시 히트 로직 + 새로고침 버튼
