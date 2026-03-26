---
id: timeout-dialog-freeze
title: 타임아웃 시 다이얼로그 미닫힘으로 프로그램 먹통
labels: [bug]
priority: p1
created: 2026-03-26
depends_on: [lecture-list-scroll-timeout]
---

# 타임아웃 시 다이얼로그 미닫힘으로 프로그램 먹통

## 현상
- 타임아웃 발생 시 "300초 타임아웃" 메시지가 다이얼로그에 표시됨
- 다이얼로그 창 자체가 닫히지 않아 프로그램이 먹통 상태

## 원인 분석

### 핵심: `mark_cancelled()`가 다이얼로그를 닫지 않음

**`src/gui/views/progress_view.py`**:
- `mark_cancelled()` (line ~557-570): progress UI를 숨기고 취소 콘텐츠를 표시하지만 **`dialog.open = False`를 호출하지 않음**
- `dialog`는 `modal=True`로 생성 (line ~294) → 백그라운드 UI와의 상호작용 차단
- `close()` 메서드 (line ~472-474)는 존재하지만, 사용자가 "닫기" 버튼을 직접 클릭해야만 호출됨

### 에러 전파 흐름
1. Worker에서 타임아웃 발생 → `_on_finished(False, error_msg)` 호출
2. `main_view.py` (line ~209-213): `self.modal.mark_cancelled()` 호출
3. `mark_cancelled()`는 에러 상태 UI만 표시, 다이얼로그는 여전히 열린 상태
4. `modal=True`라 배경 UI 클릭 불가 → 프로그램 먹통

### 추가 문제
- API 클라이언트(`gemini_provider.py`, `openai_provider.py` 등)에 **timeout 파라미터 미설정** → 라이브러리 기본값(최대 600초) 사용
- 타임아웃 에러와 일반 에러 구분 없음 → 사용자에게 불명확한 메시지
- 에러 발생 시 재시도 메커니즘 없음

## 체크리스트
- [ ] `mark_cancelled()` 호출 후 일정 시간 뒤 또는 즉시 다이얼로그 자동 닫기 처리
- [ ] 에러 상태에서 "닫기" 버튼이 명확히 보이고 클릭 가능한지 확인
- [ ] API 클라이언트에 적절한 timeout 파라미터 설정 (예: 60-120초)
- [ ] 타임아웃 에러 시 사용자에게 명확한 안내 메시지 + 재시도 옵션 제공
- [ ] `modal=True` 상태에서 에러 발생 시 UI 복구 경로 보장
