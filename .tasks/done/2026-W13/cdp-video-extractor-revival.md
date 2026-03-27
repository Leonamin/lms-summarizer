---
id: cdp-video-extractor-revival
title: CDP 비디오 URL 추출 복원 및 기본 방식 전환
labels:
  - fix
  - video-parser
priority: p1
created: 2026-03-27T00:00:00.000Z
depends_on: []
status: done
completed_at: '2026-03-27'
---

# CDP 비디오 URL 추출 복원 및 기본 방식 전환

## 배경
- DOM 기반 추출(`video.vc-vplay-video1` src)이 더 이상 작동하지 않는 영상이 존재
- CDP 네트워크 스니핑으로 실제 `.mp4` 요청을 가로채는 방식이 필요
- 기존 `CdpVideoExtractor`는 `ssmovie.mp4` 패턴만 매칭하고 deprecated 상태

## 체크리스트
- [x] CdpVideoExtractor 업데이트: URL 패턴 `.mp4` + `intro.mp4` 필터링
- [x] CdpVideoExtractor: deprecated 제거, `self._log` 사용, 다이얼로그 처리 추가
- [x] pipeline.py: 기본 method를 "cdp"로 변경
- [x] 기존 DomVideoExtractor는 fallback 옵션으로 유지
