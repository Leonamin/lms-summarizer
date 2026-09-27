---
type: Log
title: "5단계 Docker 웹 최소 흐름 구현·검증"
description: "React 작업실·FastAPI·SSE·업로드·결과 다운로드와 실제 컨테이너 재생성 복원"
timestamp: 2026-09-27
okf_version: "0.1"
---

# 5단계 Docker 웹 최소 흐름 구현·검증

## 상태와 이전 단계

**5단계 완료.** 파일 업로드→공통 작업 서비스 실행→원문/요약/프롬프트 열람·다운로드,
화면 재접속과 서버/컨테이너 재생성 복구를 확인했다. 실제 LMS 전체 흐름·유료 공급자·로컬 Whisper 추론·LAN 실제 기기와 장시간 운영은 6–7단계에서 확인한다.

사용자 합의에 따라 4단계 설치형 잔여 검증은 부분 완료/출시 전 확인 항목으로 보류했다.
4단계 변경과 진행 TODO를 `ac79344 feat: 4단계 설치형 공통 작업 서비스 전환`으로 커밋했다.
4단계 전체 완료 체크를 하지 않았다.

## 구현

- `src.web.app.create_app`의 FastAPI lifespan이 `JobService`와 네 spawn 워커를 소유한다. 브라우저 요청·SSE 연결의 종료는 작업을 취소하지 않는다. Uvicorn은 한 프로세스이며 종료 시 서비스를 정리한다.
- 기본 owner는 서버에서 고정한 `local`, 인증 모드는 `none`이다. 허용 Host와 same-origin을 검사하고 명시한 추가 Origin만 허용한다. JSON 명령의 타입/크기를 확인하고 raw 업로드는 별도 스트리밍 경로로 처리한다.
- 설정·비밀·고정 스냅샷은 웹 데이터 디렉토리에 별도 저장한다. 설정 수정은 expected_revision으로 충돌을 확인한다. 비밀 응답은 configured만 반환하고 제출 이후 변경은 이전 작업에 영향을 주지 않는다. 작업의 안전한 설정 조회는 비밀 참조·서버 Chrome 경로를 반환하지 않는다.
- 업로드는 예약→raw 스트림→실제 UTF-8/PyAV 내용 검증→관리 입력 import→ready 순서다. 파일명 경로 탈출/제어문자, 크기 불일치, 초과 한도, 바이너리 TXT·잘못된 미디어를 거부한다. 실패 후 처음부터 재전송할 수 있고 uploading/ready 중복 PUT을 거부한다.
- 미사용 업로드 삭제와 24시간 만료 정리를 제공한다. 재시작 시 미완료 업로드를 failed로 복구하고 임시 파일을 정리한다. 공통 서비스의 `delete_input`은 작업이 참조하는 입력을 삭제하지 않는다.
- 작업 API는 업로드 ID·설정 스냅샷·마지막 단계와 Idempotency-Key를 받는다. 개별/전체 취소, 같은 시도 대상 확인, 재시도·중복 요청, 목록/상세/시도·단계 이력을 제공한다.
- SSE는 영속 seq, Last-Event-ID, cursor와 reset/heartbeat를 지원한다. React는 조회 후 SSE를 연결하고 낮은 revision을 무시하며 주기적인 목록 재확인으로 일시적인 상세 조회 실패를 복구한다. 연결을 다시 열어도 처리 중인 작업을 중복 제출하지 않는다.
- 제출 응답 유실 시 웹 화면은 업로드·고정 설정·요청 키를 유지하고 같은 요청을 다시 확인한다. 자동으로 파일을 다시 올려 별도 작업을 만들지 않는다.
- 원문은 plain text, 요약은 ReactMarkdown으로 표시한다. raw HTML은 실행하지 않고 안전한 링크 변환을 사용한다. 콘텐츠 읽기는 2 MiB까지, 더 큰 파일은 다운로드한다.
- 초기 요약 방식은 키 없이 검증 가능한 챗봇 프롬프트 준비이다. API 방식·모델·키를 저장하면 자동 요약한다. manual_ready와 자동 요약 완료를 구분하며 LAN HTTP 복사 실패 시 텍스트 전체 선택으로 대응한다. 완료 작업의 챗봇 링크는 현재 설정이 아닌 제출 당시 모델을 따른다.
- React·TypeScript·Vite 작업실에 파일 선택/드롭, 단계 대기·실행 수, 목록/검색/상태 필터, 개별 취소·전체 중지·재시도, 결과 탭·복사·다운로드·시도 이력과 기본 설정을 구현했다. 넓은 화면은 좌측 메뉴와 목록/읽기 패널, 좁은 화면은 순차 배치한다.

## Docker

Node 24 프런트엔드 빌드와 Python 3.11.15/uv 0.11.25 실행 이미지로 분리했다. 실행 이미지에는 Node·Flet·CUDA extras가 없다. Google Chrome을 설치하고 UID 10001 사용자로 실행한다. PyAV 변환에는 ffmpeg 실행 파일이 필요 없다.

Compose는 한 서비스, init, 1 GiB shm, 30초 stop grace, web-data `/data`와 web-models `/models` 볼륨으로 구성했다. 기본 포트는 localhost:8000이며 LAN 노출/허용 Host는 명시적인 환경 변수로 변경한다. 설치형 데이터는 가져오지 않는다. Python 배포에 포함된 SQLite **3.53.1**을 확인했고 이미지 빌드 시 수정된 3.53 계열 이상을 요구한다.

README에 실행·LAN 주소·설정·볼륨·중지/업데이트·복원과 로컬 개발 방법을 기록했다. 일반 중지의 `down`은 볼륨을 유지하며 데이터 삭제 옵션 `-v`와 구분한다.

## 검증 근거

- 전체 unittest **51개 통과**: 기존 코어/설치형 44개와 웹 API 7개. 웹 테스트는 실제 생산용 클립보드 실행, 합성 프로세스의 설정 고정·취소·재시도·서버 재시작, 크기/내용/Host/Origin 검증·비밀 미노출·잘못된 종료 단계·입력 삭제 보호를 확인한다.
- TypeScript 검사·Vite 프로덕션 빌드 통과. npm lock을 기록했다.
- Docker 이미지 `lms-summarizer-web:stage5` 빌드, Compose 구성 검사, 격리한 `lms-stage5-check` 프로젝트의 실제 실행/healthy 확인. Chrome 설치·SQLite 3.53.1·Flet 미설치를 컨테이너에서 확인했다.
- 생산용 `PipelineExecutor`와 HTTP STT/요약 어댑터를 사용해 **합성 WAV→STT 원문→요약** 완료, 원문/요약 열람과 다운로드의 바이트 일치를 확인했다. 같은 Docker 네트워크의 합성 응답 서버를 사용했으며 유료 API/실제 음성 추론 검증이 아니다.
- 실제 HTTP SSE 프레임을 받고 연결을 끊은 뒤 작업이 completed/summary로 완료되는 것을 확인했다. 같은 Idempotency-Key 제출은 같은 작업 ID를 반환했다.
- 30개 합성 요약 작업 제출 후 컨테이너 force-recreate. 확인 시점에 interrupted 1, completed 16, running 1, queued 12를 관찰했다. 대기 작업이 이후 완료됐고 기존 완료 원문/요약·설정 스냅샷도 복원됐다. 나머지 합성 대기는 확인 후 전체 중지했다.
- agent-browser로 실제 화면에서 TXT 선택→제출→manual_ready→원문/프롬프트 열람과 복사, 새로고침 복원, 자동 요약 Markdown 화면을 확인했다. 합성 요약의 `<script>`는 실행 가능한 DOM으로 렌더링되지 않았다.
- 390px 화면에서 document scrollWidth=innerWidth, 결과·복사·다운로드/시도 이력의 세로 배치를 확인했다. 실제 휴대폰 LAN 접속 검증은 7단계에 남긴다.
- 화면 캡처는 `/tmp/lms-stage5-result.png`, `/tmp/lms-stage5-mobile-ready.png`, `/tmp/lms-stage5-docker-summary.png` 등 임시 파일로 보관하며 Git에 포함하지 않는다. 검증용 컨테이너·서버는 종료하고 기존 운영 서비스는 변경하지 않는다.

## 6–7단계에 남은 항목

- LMS 과목·주차 강의·캐시·URL 입력 화면과 실제 다운로드 전체 회귀.
- 모든 STT/요약 공급자의 모델·키·고급 설정 편집 화면, 구조화 프롬프트의 모드·분야 편집과 카탈로그.
- 상세 로그·진단·버전/업데이트·기능 대응표 전체 확인과 실제 공급자 키 검증.
- 대상 Ubuntu CPU/GPU/모델 추론·실제 LAN PC/휴대폰·장시간 작업·운영·백업/복원 최종 검증.
- 별도로 보류한 설치형 macOS/Windows 빌드·네이티브 OS/실계정 기능 회귀.

## 공식 참고

[FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/), [Vite 구성](https://vite.dev/guide/),
[SQLite 변경 이력](https://www.sqlite.org/changes.html)의 WAL 수정 버전을 확인했다.

[진행 TODO](../plans/core-web-dashboard-todo.md) · [상세 계획](../plans/core-web-dashboard-plan.md)
