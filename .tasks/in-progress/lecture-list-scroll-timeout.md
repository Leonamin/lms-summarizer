---
id: lecture-list-scroll-timeout
title: 강의 목록 주차학습 펼치기 스크롤 의존 + 타임아웃 문제
labels:
  - bug
priority: p1
created: 2026-03-26T00:00:00.000Z
depends_on: []
refs: []
epic: ''
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
- [x] 펼치기 버튼 클릭 후 프로그래밍적 스크롤 추가 (`_scroll_to_load_all`: iframe `evaluate`로 `scrollTo` 반복)
- [x] 스크롤 후 DOM 요소 개수가 안정될 때까지 대기하는 로직 추가 (3회 연속 동일 시 종료)
- [ ] headless 모드에서도 동작하는지 검증 (실환경 테스트 필요)
- [ ] 기존 headless=False 모드 동작에 영향 없는지 확인 (실환경 테스트 필요)

### 수정된 파일

- `src/video_pipeline/course_scraper.py`: `_scroll_to_load_all()` 메서드 추가, `fetch_lectures()`에서 펼치기 후 호출

### 사용자가 찾은 이슈
- <button class="xn-common-white-btn xnmb-all_fold-btn">모두 펼치기</button>
- 웹 사이트가 SSR이라서 주차학습을 확인하려면 모든 주차를 펼쳐야함
- `모두 펼치기`를 클릭하면 주차학습들이 모두 펴지게됨
- 근데 문제는 하필 사이트가 처음 열리면 현재 보이는 화면에 버튼이 숨겨지게 되는데 혹시 이 문제로 버튼이 안보이는걸까?
