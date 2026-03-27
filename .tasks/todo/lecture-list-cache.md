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

## 논의 항목

- **캐시 키**: URL 기준? 강의 ID 기준?
- **만료 정책**: TTL 기반 (예: 1일)? 수동 갱신 버튼?
- **저장 위치**: `settings.json` 내 포함? 별도 `cache.json`?
- **갱신 트리거**: 앱 시작 시? 수동 새로고침 버튼?
- **일관성 문제**: LMS에서 강의가 추가/변경됐을 때 stale 캐시 처리

## 체크리스트
- [ ] 캐싱 전략 결정 (논의 후 작성)
- [ ] 구현
