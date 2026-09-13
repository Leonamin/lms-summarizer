---
type: Log
title: "Queue Pipeline — Download/Processing Overlap"
description: "다운로드↔처리 오버랩 파이프라인 + 백그라운드 작업 큐 구현"
timestamp: 2026-09-14
okf_version: "0.1"
---

# Queue Pipeline — Download/Processing Overlap

## 배경

기존 파이프라인은 단일 스레드에서 단계별 일괄 처리(전부 다운로드 → 전부 변환 → 전부 STT → 전부 요약)라 대기 시간이 낭비됐다. 다운로드는 네트워크/I/O, STT는 CPU/GPU, 요약은 네트워크(API)로 자원이 겹치지 않으므로 항목 단위 오버랩이 가능하다.

## 설계

- **`VideoPipeline` 세션 API**: `open_session()` / `process_single_url(url)` / `close_session()` — 브라우저 세션을 열린 채로 URL 단건 처리. 기존 `process(urls)`는 세션 API 기반으로 재구성 (하위 호환 유지).
- **`ItemProcessor`** (`gui/workers/item_processor.py`): 항목 단위 변환→STT→요약 처리기. 파일 존재 검증, 30분 타임아웃, 클립보드 모드 챗봇 텍스트, 히스토리 저장, 원본 삭제 포함.
- **`QueueManager`** (`gui/workers/queue_manager.py`): 다운로드 스레드(producer) + 처리 스레드(consumer). 다운로드 완료 즉시 처리 큐로 흘려보내 오버랩.
- **`QueuePanel`** (`gui/components/queue_panel.py`): 모달 대신 메인 레이아웃에 삽입되는 작업 대기열 패널. 항목별 상태(대기/다운로드/변환/STT/요약/완료/실패/취소) 표시 + 전체 중지.
- **main_view**: DOWNLOAD 단계 + URL 입력 시 큐 모드로 동작. 실행 중 "큐에 추가" 버튼으로 URL 추가 가능. 파일 기반 단계(CONVERT/STT/SUMMARIZE 시작)는 기존 원샷 모달 유지.

## 큐 생명주기 설계 (중요)

- 스레드는 모든 작업 완료 후 자연 종료(idle)하고, 새 제출 시 새 세션으로 기동 → idle 후에는 변경된 엔진/모델 설정이 적용됨.
- 실행 중 제출은 세션 설정 유지(변경 무시, 로그 안내).
- `request_stop`: 취소 이벤트 + STOP 센티널. 중지 시점의 WAITING/DOWNLOADING 작업만 취소 처리(`_stopped_ids` 스냅샷).
- 정리 중 제출된 작업은 유실 방지를 위해 cleanup에서 자동 재시작. 세대 검증(`self._download_thread is not dl → return`)으로 이중 재시작 방지.
- 로그 콜백 예외가 워커 스레드를 죽이지 않도록 `_log`에서 방어.

## 검증

- 모킹 테스트: 오버랩 확인 (task1 STT 진행 중 task2 다운로드 교차), 전체 중지 후 재시작, 실행 중 추가 제출 — 3회 이상 반복 통과.
- 테스트 중 발견·수정한 버그: idle 콜백 미발화(자기 스레드 is_alive 판정), 중지 시 DOWNLOADING 잔존, 정리 중 제출 유실, 이중 재시작 경합, 로그 콜백 예외로 스레드 사망.

## 남은 검증 (실사 필요)

- [ ] 실제 LMS에서 큐 모드 E2E 테스트 (다운로드 오버랩 + 실행 중 URL 추가)
- [ ] Flet UI에서 QueuePanel 렌더링 확인
