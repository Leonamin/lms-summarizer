---
id: faster-whisper-gpu-windows
title: faster-whisper Windows GPU 동작 불가 문제 (정적 분석)
labels: [bug]
priority: p1
created: 2026-03-26
---

# faster-whisper Windows GPU 동작 불가 문제

## 현상
- Windows 사용자들이 faster-whisper GPU 모드가 안 된다고 다수 보고

## 원인 분석 (정적 분석)

### 핵심 문제: GPU 초기화 에러 핸들링 전무

**`src/audio_pipeline/transcriber.py` (line ~153-165)**:
```python
self.model = WhisperModel(model_name, device=device, compute_type=compute_type)
# → try/except 없음. CUDA 없으면 즉시 크래시
```

### 세부 문제 목록

1. **GPU/CUDA 감지 로직 없음**: `torch.cuda.is_available()` 등 사전 검증 없이 `device="auto"` 그대로 전달
2. **CPU 폴백 없음**: GPU 초기화 실패 시 CPU로 자동 전환하는 로직 부재
3. **UI에서 GPU 선택 시 사전 검증 없음**: `src/gui/components/left_panel/stt_settings.py` (line ~163-179)에서 CUDA 선택 가능하지만 실제 가용 여부 미확인
4. **초기화 시점 문제**: 파일 처리 시작 후에야 GPU 검증 — 실패하면 전체 작업 실패
5. **compute_type 검증 없음**: `"auto"` 기본값이 특정 GPU에서 호환 안 될 수 있음
6. **의존성 명세 불완전**: `pyproject.toml`에 CUDA 관련 환경 마커 없음
7. **디버깅 정보 부족**: GPU 이름, VRAM, CUDA/PyTorch 버전 등 로깅 없음

## 체크리스트
- [x] `WhisperModel()` 생성을 try/except로 감싸고 GPU 실패 시 CPU 폴백 추가
- [x] GPU 사용 가능 여부 사전 감지 로직 추가 (`_resolve_device`: torch/ctranslate2 CUDA 확인)
- [ ] UI에서 GPU 선택 시 사전 검증 + 불가 시 경고 표시
- [x] GPU 초기화 실패 시 사용자에게 명확한 안내 메시지 (`on_log`로 전달)
- [x] 디바이스 정보 로깅 추가 (GPU 이름, resolved device/compute_type)
- [ ] pyproject.toml에 CUDA 관련 optional dependency 그룹 검토

### 수정된 파일

- `src/audio_pipeline/transcriber.py`: `_resolve_device()` 메서드 추가 (auto 감지), GPU 실패 시 CPU int8 자동 폴백
