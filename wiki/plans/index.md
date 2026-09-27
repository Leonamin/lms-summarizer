---
type: Index
title: "Plans"
description: "진행 중·예정된 작업 항목의 구조와 목록"
scope: "plans"
okf_version: "0.1"
---

# Plans

진행 중이거나 예정된 작업 항목입니다. 기존 .tasks(Plank)의 미완료 태스크를 이관한 문서를 포함합니다.

## 규칙

- 작업 완료 시 결과를 logs/에 기록하고 이 디렉토리에서 문서를 제거합니다.
- 우선순위는 frontmatter의 priority(p1 > p2 > p3)로 표현합니다.

## 문서


- [core-web-dashboard-todo.md](core-web-dashboard-todo.md) — 공통 코어·웹 대시보드 진행 TODO, 5단계 완료·4단계 OS 검증 잔여 (p1)
- [core-web-dashboard-plan.md](core-web-dashboard-plan.md) — 기능 대응·구조·단계별 완료 기준 상세 계획 (p1)

- [cdp-audio-video-split.md](cdp-audio-video-split.md) — CDP 영상 추출 오디오/비디오 분리 mp4 검증 (p1)
- [login-flow-e2e-test.md](login-flow-e2e-test.md) — 새 로그인 플로우 실환경 E2E 테스트 (p1)
- [faster-whisper-gpu-windows.md](faster-whisper-gpu-windows.md) — faster-whisper Windows GPU 잔여 항목 (p1)
- [file-save-silent-failure.md](file-save-silent-failure.md) — 파일 저장 실패 Mac 엣지케이스 확인 (p1)
- [lecture-list-scroll-timeout.md](lecture-list-scroll-timeout.md) — 강의 목록 스크롤 headless 검증 (p1)
- [timeout-dialog-freeze.md](timeout-dialog-freeze.md) — API timeout 파라미터 및 재시도 (p1)
- [faster-whisper-cpu-model-optimization.md](faster-whisper-cpu-model-optimization.md) — CPU용 경량 모델 추가 (p2)
