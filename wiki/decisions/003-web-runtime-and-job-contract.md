---
type: Decision
title: "ADR-003: 웹 실행 기술과 작업 계약"
description: "개인 서버의 SPA·API·저장·단계 프로세스 및 재시도 구현 기준"
status: accepted
date: 2026-09-27
okf_version: "0.1"
---

# ADR-003: 웹 실행 기술과 작업 계약

## Context

[ADR-002](002-core-and-web-dashboard.md)의 개인용 Docker 서버, 단계 간 병렬 처리, 실제 취소, 재시작 복구를 구현할 기술 기준이 필요하다. 사용자 요청에 따라 1단계를 진행하면서 기존 코드와 공식 문서, 대상 PC를 조사했다.

## Decision

- React·TypeScript·Vite SPA, Python 3.11 FastAPI·Uvicorn 단일 프로세스, SQLite 로컬 볼륨, SSE를 사용한다.
- API 앱의 수명에 공통 supervisor를 연결하고 다운로드·변환·STT·요약에 상주 자식 프로세스 한 개씩 둔다. STT 모델은 설정이 같으면 재사용한다.
- supervisor만 DB 상태를 확정한다. 자식 프로세스 메시지는 작업·시도·세대 ID를 가진다. 강제 취소 후 프로세스와 IPC를 새로 생성한다.
- 동일 작업의 재시도는 새 시도로 원래 입력부터 실행한다. 완료 단계 자동 재사용은 첫 버전에 넣지 않는다. 기존 설정·비밀 버전은 유지한다.
- 작업 상태는 queued/running/cancelling/completed/failed/cancelled/interrupted로 관리한다. 종료 이유와 시도 이력을 보존한다. completed는 summary/manual_ready/stage_artifact 결과 종류를 가진다.
- 실패·취소·중단 입력은 재시도용으로 보존한다. 성공 후 원본 보관 옵션을 적용한다. 다른 작업 참조가 있는 파일은 삭제하지 않는다.
- 비밀은 별도 로컬 저장소(0700/0600)에 버전으로 보관하고 DTO·로그·이벤트에 원문을 반환하지 않는다. 암호화 보관은 이 결정에 포함하지 않는다.
- 설치형은 코어 직접 호출, 웹은 같은 origin의 API·정적 파일로 구성한다. 웹 데이터는 설치형에서 자동 가져오지 않는다.
- 대상 PC에서 NVIDIA 장치가 확인되지 않았으므로 초기 로컬 STT는 CPU 기준이다. Google Chrome은 컨테이너에 설치한다.

## Consequences

별도 Redis·DB 서비스 없이 영속 큐를 관리할 수 있지만 supervisor는 하나만 실행해야 한다. SQLite는 로컬 파일시스템에서 사용하고 배포 버전의 WAL 관련 수정 여부를 확인해야 한다. 강제 취소는 프로세스 트리·Chrome·IPC 회수를 구현해야 하며, 외부 API 요청·비용을 되돌릴 수 없다.

LAN HTTP에서 브라우저 자동 클립보드 복사가 제한될 수 있어 수동 전체 선택·복사와 다운로드를 제공한다. API·모델·조정 가능한 운영 기본값 및 기능별 검증 기준은 [1단계 계약](../logs/2026-09-27-core-web-stage1-contract.md)에 기록한다.

## Status

Accepted — 구현을 위한 기술 판단으로 선택했다. 사용자가 특정 라이브러리나 운영 한도 숫자를 직접 지정한 것은 아니다. 실제 LMS 결과나 새 요구로 달라지면 본 결정을 갱신한다. 2026-09-27 Docker Google Chrome headless에서 제공된 강의 한 개의 로그인·CDP 추출 성공을 확인했다. 초기 실행은 headless, headed/Xvfb는 진단 경로로 둔다. 전체 다운로드·STT·요약 성공을 의미하지 않는다.

## 공식 근거

[React 구성](https://react.dev/learn/build-a-react-app-from-scratch), [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/), [SQLite WAL](https://www.sqlite.org/wal.html), [Playwright Chrome·코덱](https://playwright.dev/python/docs/browsers), [Python multiprocessing](https://docs.python.org/3.11/library/multiprocessing.html), [MDN 클립보드](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText)를 확인했다. 기술 구성은 프로젝트 조건에 따른 설계 판단이다.
