---
type: Log
title: "Log Auto-scroll and CUDA 12 Runtime Fix"
description: "로그 자동 스크롤 구현 및 cublas64_12.dll 누락으로 CUDA STT 실패하던 문제 수정"
timestamp: 2026-09-14
okf_version: "0.1"
---

# Log Auto-scroll and CUDA 12 Runtime Fix

## 1. 로그 자동 스크롤

### 요구사항

- 새 로그가 생기면 끝으로 자동 스크롤 (끝에 가까우면 오차 몇 px도 허용)
- 사용자가 중간을 읽고 있으면 자동 스크롤하지 않음

### 구현

- `AutoScrollLog` 컴포넌트 신규 (`gui/components/auto_scroll_log.py`): TextField 대신 스크롤 가능한 Column 사용 (TextField는 스크롤 제어 불가)
- `on_scroll` 이벤트로 끝 부착 여부 추적: `max_scroll_extent - pixels <= 32px`이면 "끝"으로 판단
- 끝에 붙어 있을 때만 `scroll_to(offset=-1)` 발화
- `LogDrawer`와 `ProgressModal` 로그 모두 교체 적용

## 2. CUDA STT 실패 (cublas64_12.dll)

### 증상

- RTX 5080(CUDA 13.2 설치) 환경에서 STT 변환 실패: `Library cublas64_12.dll is not found or cannot be loaded`

### 원인

- ctranslate2 4.7.1은 **CUDA 12** 런타임(cublas64_12.dll)을 요구
- 시스템에는 CUDA 13.2만 설치되어 있음 (cublas64_13.dll)
- `_resolve_device`의 CUDA 감지는 드라이버 기반(`get_supported_compute_types`)이라 통과 → 모델 로드는 성공하지만 **첫 encode 시점**에 cublas 로드 실패
- GPU 초기화 실패 폴백 로직도 이 시점 이후라 동작하지 않았음

### 수정

1. **의존성 추가**: `nvidia-cublas-cu12`, `nvidia-cuda-runtime-cu12` (pip) — cublas64_12.dll 제공
2. **DLL 경로 부트스트랩** (`_bootstrap_cuda_dll_paths`): pip nvidia 패키지의 bin 디렉토리를 PATH 앞에 추가. `add_dll_directory`는 ctranslate2 로드에 반영되지 않음 (PATH 방식만 동작 확인)
3. **사전 검증** (`_check_cuda_runtime_loadable`): cublas64_12.dll을 전체 경로로 실제 로드해보고 실패 시 CPU int8로 폴백 — 연산 시점 크래시 대신 명확한 로그와 폴백 제공

### 검증

- RTX 5080에서 `WhisperModel('small', device='cuda', compute_type='float16')` 실제 transcribe 성공
- 사전 검증 로직: PATH/시스템 경로에서 cublas64_12.dll 탐색 → ctypes 전체 경로 로드

### 참고

- PyInstaller 번들 시 nvidia 패키지 DLL을 datas에 포함하거나 frozen 환경에서는 부트스트랩을 건너뜀 (`sys.frozen` 체크)
