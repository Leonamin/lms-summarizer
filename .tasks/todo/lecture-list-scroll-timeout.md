---
id: lecture-list-scroll-timeout
title: 강의 목록 주차학습 펼치기 스크롤 의존 + 타임아웃 문제
labels: [bug]
priority: p1
created: 2026-03-26
---

# 강의 목록 주차학습 펼치기 스크롤 의존 + 타임아웃 문제

## 현상
- `headless=False`에서 사용자가 마우스 스크롤을 해야만 주차학습이 펼쳐지고 동영상 정보를 가져옴
- 스크롤하지 않거나 headless 모드면 전부 타임아웃 발생

## 원인 분석
LMS 페이지가 **IntersectionObserver 기반 가상 스크롤**을 사용하여 뷰포트에 보이는 항목만 DOM에 렌더링함.

### 핵심 코드: `src/video_pipeline/course_scraper.py`
1. **`fetch_lectures()` (line ~160-167)**: 펼치기 버튼 클릭 후 `asyncio.sleep(0.5)`만 대기 — 가상 스크롤 렌더링에 불충분
2. **`_parse_weeks()` (line ~186-191)**: `query_selector_all(":scope > div")`는 DOM에 렌더링된 요소만 반환 — 스크롤 안된 항목은 누락
3. `wait_until="networkidle"`은 JS 렌더링/IntersectionObserver 콜백을 기다리지 않음

### 왜 수동 스크롤은 작동하는가
- 스크롤 → IntersectionObserver 트리거 → 오프스크린 요소 렌더링 → DOM 쿼리 성공

## 체크리스트
- [ ] 펼치기 버튼 클릭 후 프로그래밍적 스크롤 추가 (iframe 내부 `evaluate`로 `scrollTo` 반복)
- [ ] 스크롤 후 DOM 요소 개수가 안정될 때까지 대기하는 로직 추가
- [ ] headless 모드에서도 동작하는지 검증
- [ ] 기존 headless=False 모드 동작에 영향 없는지 확인
