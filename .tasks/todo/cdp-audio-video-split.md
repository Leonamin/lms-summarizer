---
id: cdp-audio-video-split
title: CDP 영상 추출 — 오디오/비디오 분리 mp4 검증
labels: [bug, video-pipeline]
priority: p1
created: 2026-03-27
depends_on: []
---

# CDP 영상 추출 — 오디오/비디오 분리 mp4 검증

## 배경

LMS 플레이어가 오디오 전용 mp4와 비디오 mp4를 분리 요청하는 것으로 추정됨.
기존 CDP 추출기는 첫 번째 mp4만 캡처했기 때문에 오디오 전용 파일이 먼저 오면 소리만 있는 파일이 다운로드됨.

## 현재 상태

`_pick_video_url` 로직을 추가하여 모든 mp4 URL을 수집 + audio 힌트 필터링을 구현함.
실제 LMS에서 테스트하여 URL 패턴을 확인하고 필터를 정밀 조정해야 함.

## 체크리스트

- [ ] LMS에서 실제 다운로드 테스트 → 로그에서 mp4 URL 패턴 확인
- [ ] URL 패턴 기반으로 `_pick_video_url` 필터 정밀 조정
- [ ] 다양한 강의 유형(movie, readystream, everlec)에서 정상 동작 확인
- [ ] DOM fallback도 동일 이슈가 있는지 확인
