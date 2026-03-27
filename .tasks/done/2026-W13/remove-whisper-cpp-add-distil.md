---
id: remove-whisper-cpp-add-distil
title: whisper-cpp 제거 + distil-large-v3 고속 모드 추가
labels:
  - refactor
  - stt
  - deps
priority: p1
created: 2026-03-27T00:00:00.000Z
depends_on: []
status: done
completed_at: '2026-03-27'
---

# whisper-cpp 제거 + distil-large-v3 고속 모드 추가

## 배경
- faster-whisper로 통합하면서 pywhispercpp 의존성 제거 → 빌드 크기 감소
- distil-large-v3 고속 모드 추가 (large-v3-turbo 대비 2~3배 빠름)

## 체크리스트

### model_manager.py 정리
- [x] whisper-cpp 전용 코드 제거: `MODEL_REGISTRY`, `MODE_ORDER`, `get_local_path`, `get_expected_path`, `resolve_for_transcriber`, `download_model`, `DownloadCancelled`
- [x] `FW_MODEL_REGISTRY`에 `distil-large-v3` 고속 모드 추가
- [x] `is_available` 단순화, 불필요 유틸 제거

### transcriber.py
- [x] `WhisperCppTranscriber` 클래스 제거
- [x] `transcribe_audio_to_text` 기본값 `engine="faster-whisper"` 변경

### audio_pipeline/pipeline.py
- [x] 기본값 `engine="faster-whisper"` 변경

### GUI 정리
- [x] `stt_settings.py`: whisper-cpp 옵션 및 모델 다운로드 섹션 제거
- [x] `file_manager.py`: 기본값 `"whisper-cpp"` → `"faster-whisper"`, whisper-cpp 전용 함수 정리
- [x] `processing_worker.py`: `_check_stt_model_available` whisper-cpp 전용 체크 제거

### 의존성
- [x] `pyproject.toml`: `pywhispercpp` 제거 (`uv remove pywhispercpp`)
- [x] `CLAUDE.md`: 기본 STT 엔진 업데이트
