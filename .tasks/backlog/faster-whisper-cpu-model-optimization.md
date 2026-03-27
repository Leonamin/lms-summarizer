---
id: faster-whisper-cpu-model-optimization
title: faster-whisper CPU 사용자를 위한 경량 모델 및 양자화 모델 추가
labels:
  - dev
priority: p2
created: 2026-03-26
depends_on:
  - faster-whisper-gpu-windows
---

# faster-whisper CPU 사용자를 위한 경량 모델 및 양자화 모델 추가

## 배경

대부분의 사용자가 CUDA GPU 없음:
- **macOS**: Apple Silicon (M1~M5) → CUDA 미지원, CPU 폴백
- **Windows**: Intel Arc / AMD 내장 GPU → CUDA 미지원, CPU 폴백

현재 기본 모델 `large-v3-turbo`(~800MB)는 CPU int8에서도 느림.
whisper.cpp에서는 `royshilkrot/whisper-large-v3-turbo-korean-ggml`(GGML 양자화)을 사용했으나 CTranslate2(faster-whisper) 포맷과 호환 안 됨.

## 조사 결과 (HuggingFace CTranslate2 모델)

### 공식/커뮤니티 모델

| 모델 | 로드 방법 | 다운로드 | RAM | CPU 적합성 |
|------|-----------|---------|-----|-----------|
| `Systran/faster-whisper-small` | `WhisperModel("small", compute_type="int8")` | 488MB | ~244MB | 최고 (가장 빠름) |
| `Systran/faster-whisper-medium` | `WhisperModel("medium", compute_type="int8")` | 1.5GB | ~770MB | 양호 |
| `deepdml/faster-whisper-large-v3-turbo-ct2` | `WhisperModel("turbo", compute_type="int8")` | 1.6GB | ~810MB | 보통 (디코더 4층이라 CPU 친화적) |
| `Systran/faster-whisper-large-v3` | `WhisperModel("large-v3", compute_type="int8")` | 3.1GB | ~1.5GB | 느림 |

### 핵심 규칙

- CPU에서는 반드시 `compute_type="int8"` 사용 (float16은 CPU에서 float32로 폴백됨, 속도 이점 없음)
- `int8_float16`은 GPU 전용
- `deepdml/faster-whisper-large-v3-turbo-ct2`는 float16 저장, int8 양자화는 런타임에 수행

## 체크리스트

- [ ] `FW_MODEL_REGISTRY`에 `small`, `medium` 모델 추가
- [ ] CPU 모드 감지 시 기본 모델을 `small` 또는 `medium`으로 권장하는 UI 안내
- [ ] `compute_type` 자동 결정: CPU → `int8`, CUDA → `float16`으로 기본값 설정 (이미 `_resolve_device`에서 처리됨, 확인 필요)
- [ ] 모델별 한국어 강의 인식 품질 비교 테스트 (기본 다국어 모델 기준, 한국어 파인튜닝 모델은 테스트 결과 성능 저하 확인됨)
