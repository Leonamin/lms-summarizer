---
id: distil-model-korean-broken
title: distil-large-v3 고속모드 한국어 미지원 — 제거 또는 경고
labels: [bug, stt]
priority: p1
created: 2026-03-27
depends_on: []
---

# distil-large-v3 고속모드 한국어 미지원

## 증상

- 고속모드(`distil-large-v3`) STT 결과가 이해 불가능한 영어 hallucination
- 표준모드(`large-v3-turbo`)는 정상적인 한국어 출력
- M4 Mac Mini 기준 속도 차이도 미미 (646초 vs 694초)

## 원인

`distil-large-v3`는 영어 데이터 중심으로 증류된 모델.
`language="ko"`, `initial_prompt="한국어 강의입니다."` 설정에도 한국어를 무시하고 영어로 해석.

## 처리 방안

### A. 제거 (권장)
- `model_manager.py`에서 `distil-large-v3` 엔트리 제거
- `FW_MODE_ORDER`에서 제거
- `stt_settings.py` UI에서 2개 모델만 표시

### B. 경고 추가
- description을 "영어 전용 (한국어 미지원)"으로 변경
- UI에서 한국어 사용 시 선택 불가하게 처리

## 참고
- 속도 차이 미미 (646초 vs 694초) → 고속모드의 실질적 이점 없음
- `large-v3`(고정밀)는 3.1GB로 무겁지만 한국어 지원됨

## 체크리스트

- [ ] 방안 결정 (A: 제거 / B: 경고)
- [ ] model_manager.py 수정
- [ ] stt_settings.py UI 반영
