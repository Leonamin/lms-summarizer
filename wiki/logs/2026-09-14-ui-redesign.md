---
type: Log
title: "UI Redesign — Background Queue Centered Layout"
description: "사이드바 탭, 소스 카드, 파이프라인 모니터, 모달 폐기로 메인 화면 전면 개편"
timestamp: 2026-09-14
okf_version: "0.1"
---

# UI Redesign — Background Queue Centered Layout

> 설계 배경과 결정 사항은 [ADR-001](../decisions/001-ui-redesign-background-queue.md) 참조.

## 구현 내용

### 신규 컴포넌트

- **`Sidebar`** (`gui/components/sidebar.py`): 계정/AI/STT/일반 4탭. 한 번에 하나만 표시. "일반" 탭에 요약 모드·강의 분야·원본 보관·저장 경로 통합 (기존 OptionsSection 역할 흡수)
- **`SourceSelector`/`SourceCard`** (`gui/components/source_selector.py`): LMS/파일 카드 2개, 선택 시 강조. 파일 확장자로 시작 단계 자동 유추 (.mp4→변환, .wav/.mp3→STT, .txt→요약). StageSelector 드롭다운 폐기
- **`PipelineMonitor`** (`gui/components/pipeline_monitor.py`): 단계별 적체량 표시 `⬇ 다운로드 [2] → 🔄 변환 [1] → 🎙 STT [0] → 🤖 요약 [3]`. 단계 클릭 시 항목 목록 펼침. 메인 화면 상주 (모달 아님)

### QueueManager 확장

- `submit_files(files, settings, start_stage)`: 파일 소스를 처리 큐에 직접 투입 (브라우저 세션 불필요, `_ensure_process_thread`)
- `ItemProcessor.process_full(start_stage=)`: "변환"/"STT"/"요약"부터 시작 지원
- `finalize(delete_source=)`: 사용자가 직접 선택한 파일은 삭제하지 않음

### main_view 재구성

- 레이아웃: 사이드바(탭) | 소스 카드 + 입력 + 시작 버튼 | 파이프라인 모니터 | 로그 드로어
- 진행 모달(ProgressModal) 완전 제거 — 작업은 큐가 소유, UI는 구독자
- "전체 중지" 버튼만 확인 다이얼로그 사용 (명시적 중지 의도)

## 검증

- 파일 소스 큐 테스트: WAV(STT 시작) 2건 + TXT(요약만) 1건 모두 완료
- 기존 URL 큐 테스트(오버랩/중지/재시작) 재통과

## 남은 검증 (실사 필요)

- [ ] Flet UI 렌더링 확인 (탭 전환, 카드 선택, 모니터 클릭)
- [ ] 실제 LMS URL 큐 동작 확인
