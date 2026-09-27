---
type: Log
title: "코어·웹 3단계: 영속 작업과 독립 단계 실행기"
description: "SQLite 상태 전이, 상주 프로세스, 취소·재시도·복구 및 장애 검증"
status: completed
created: 2026-09-27
okf_version: "0.1"
---

# 코어·웹 3단계: 영속 작업과 독립 단계 실행기

[상세 계획](../plans/core-web-dashboard-plan.md) · [진행 TODO](../plans/core-web-dashboard-todo.md) · [ADR-003](../decisions/003-web-runtime-and-job-contract.md)

## 구현

- `src/core/services/jobs.py`: 프레임워크 독립 JobService와 단일 supervisor. owner context와 입력 ID로 제출·조회·취소·전체 취소·재시도·산출물 조회·이벤트 조회/구독을 제공한다. GUI와 HTTP 요청 객체를 받지 않는다.
- `src/core/repositories/jobs.py`: SQLite schema v1의 설정 revision·작업·시도·단계 실행·산출물·이벤트·idempotency 기록. WAL·외래키·busy_timeout·FULL 동기화를 사용한다. 부모 프로세스만 DB를 열고 변경하며 서비스 lock으로 스레드 접근을 직렬화한다.
- 단계 완료, 산출물 메타데이터, 다음 대기 단계, 상태·이벤트 기록을 하나의 트랜잭션으로 처리한다. 파일은 작업·시도·단계 실행 ID 공간의 `.part`에서 `complete`로 원자 rename한다. DB 확정 전 장애로 남은 파일은 복구 때 정리한다.
- 다운로드·변환·STT·요약마다 상주 spawn 자식 프로세스 한 개와 독립 슬롯을 둔다. 대기는 DB의 FIFO 기록이 기준이며 프로세스가 DB에 쓰지 않는다. 작업·시도·단계 실행·워커 generation이 일치하는 결과만 확정한다.
- `src/core/runtime/executor.py`: 기존 Chrome/CDP·PyAV·STT·요약 공급자에 연결한다. STT 설정·자격 증명·모델 캐시 경로 지문이 같으면 transcriber를 재사용하고 바뀌면 기존 client/model을 해제한다. 초기 로컬 STT는 CPU/int8 기본값이며 모델 캐시 위치를 명시적으로 전달한다. 다운로드마다 열린 Chrome 세션은 해당 실행 안에서 반드시 닫는다.
- 개별 취소는 대기 즉시 cancelled, 실행은 cancelling → 협력 유예 → 프로세스 트리 회수 → cancelled 순서다. 전체 취소는 호출 시 존재하는 활성 시도만 snapshot으로 처리한다. 슬롯은 프로세스·IPC 회수 뒤 새 generation으로 교체한다.
- `src/core/runtime/processes.py`: 데이터 디렉토리 배타 락, Unix 세션/프로세스 그룹, PID 재사용을 확인하는 psutil 자식 추적·회수, Windows Job Object를 구현했다. Unix에서는 Chromium처럼 별도 그룹으로 분리된 자식도 회수한다. 부모 연결 종료 감시가 서버 강제 종료 시 자식 트리를 제거한다. 취소 플래그는 RawValue로 구현하여 강제 종료 때 named semaphore가 남지 않는다.
- 서버 재시작은 이전 running/cancelling을 interrupted로 기록하고 queued를 보존한다. 정상 종료도 신규 제출 차단·협력 종료·회수 후 실행 중단을 기록한다. 종료 중 받은 결과를 자동 완료로 확정하지 않는다. 워커 사망·단계 timeout은 명시적 실패이며 새 슬롯으로 교체한다.
- 재시도는 새 Attempt를 만들어 원래 입력 단계부터 실행하며 제출 설정·프롬프트·비밀 버전을 유지한다. 제출/재시도의 idempotency key 중복과 다른 요청 재사용을 구분한다. 활성 시도·이전 시도 ID 충돌, 원본·비밀 누락, 큐 한도를 검사한다.
- 사용자 파일은 서버 관리 복사본을 만들고 원본은 삭제하지 않는다. 성공 때만 보관 정책과 중간 오디오 삭제를 적용한다. 실패·취소·중단 입력과 다른 작업이 참조하는 입력을 보존한다. 업로드된 텍스트 원문도 보존한다. 비밀 버전 참조 조회와 참조 중 삭제 보호, 명시적 폐기의 영향 작업 목록을 제공한다.
- 원문·요약·프롬프트는 파일로 유지한다. 이벤트에는 제어된 상태·오류 코드·단계 로그만 기록하며 공급자의 stdout/stderr, 예외 원문, 비밀·URL·서버 경로를 전달하지 않는다. 이벤트 pagination·reset·구독 해제·heartbeat를 제공한다. API/SSE 전송 연결은 5단계다.
- 미사용 입력 24시간, 이벤트/로그 7일·10만 행을 정리한다. 디스크 여유 부족 시 단계 실행을 보류하고, 입력 크기·제출 수·활성 작업 수·취소/종료 유예·단계 제한은 조정 가능하다.
- 공급자 HTTP timeout과 단계 제한을 분리했다. OpenAI 호환·Anthropic·Gemini SDK 자동 재시도를 끄고 ReturnZero HTTP timeout을 지정했다. CustomProvider의 fallback은 미지원 route 상태(404/405/501)에 한정하며 모델 미존재·timeout·인증·서버 오류 뒤에 두 번째 유료 호출을 하지 않는다. 기존 다운로드 무결성 재시도는 유지한다.
- 다운로드 제목을 파일명으로 사용할 때 경로 구분자를 정리한다. httpx·psutil을 직접 의존성으로 명시하고 uv.lock을 갱신했다.

## 검증

`uv run --extra web python -m unittest discover -s tests -v`: **30개 통과**, Python 3.11.15·SQLite 3.53.1·Ubuntu에서 실행했다.

- 네 단계가 동시에 서로 다른 작업을 처리하는 구간과 각 단계 슬롯 최대 1개, FIFO 처리, 완료 후 DB 재조회.
- 대기 취소·실행 취소·전체 취소 이후 새 제출 보존, 비협력 워커 강제 회수와 별도 세션 자식 프로세스 종료, 기존 generation의 늦은 결과 거부.
- 실패 후 새 시도, 원래 설정·비밀 버전 유지, 중복 제출·재시도, 비밀·입력 누락, 소유자 경계·활성 작업 한도.
- 서버 프로세스를 SIGKILL한 뒤 실행 중단·대기 복원, 자식 종료, 정상 종료 중 실행 중단·대기 유지, 중복 supervisor 락.
- 실제 SQLite trigger로 다음 단계 INSERT 실패를 주입하여 단계 완료·산출물·다음 단계 전이가 함께 rollback되고 복구 때 고아 파일을 정리하는 것을 확인.
- 워커 사망·단계 timeout 뒤 슬롯 재사용, 공유 입력의 실패 작업 참조 보존, 사용자 원본 보존, 디스크 압력 보류 후 재개.
- 실제 PipelineExecutor에서 동일 transcriber 재사용·설정 변경 시 교체/해제를 mock으로 확인. 실제 Whisper 모델 다운로드/추론 검증은 아니다.
- 실제 PyAV WAV 변환, BOM 텍스트 수동 프롬프트 생성, 로컬 HTTP 서버에 OpenAI 호환 STT SDK 요청 후 원문·manual_ready 산출물 생성.
- 로컬 HTTP 500 응답에서 요청 한 번으로 실패하고 사용자 재시도 시에만 추가 요청을 보내는 것을 확인. CustomProvider timeout에서 fallback 호출이 없고 미지원 route에서만 fallback하는 것을 확인.
- 이벤트 페이지 누락 없음, 보존 범위 밖 reset, 구독 종료가 작업 취소를 하지 않음, 공개 조회·이벤트에 비밀·예외 URL이 없음.
- Flet·pyperclip 미설치 환경에서 JobService·PipelineExecutor import 성공. 기존 코어 경계·데이터 호환 테스트도 통과.
- `python3 -m compileall -q src tests`, `git diff --check` 통과.

## 적용 범위와 남은 검증

3단계 완료 기준인 영속 상태·단계 독립 실행·취소·재시도·설정 고정·복구·늦은 결과 차단을 위 테스트로 확인했다. 기존 GUI는 아직 이전 QueueManager를 사용하며 서비스 연결은 4단계다. 웹 API·업로드 스트림/실제 미디어 유형 검증·SSE 전송·컨테이너 수명 연결은 5단계다. LMS 과목 조회 프로세스 명령 연결은 6단계다.

이번 단계에서는 실제 LMS 전체 다운로드·유료 공급자 호출·로컬 Whisper 추론을 실행하지 않았다. Windows Job Object와 macOS 동작은 구현했지만 해당 OS 실행 환경이 없어 미검증이며 4단계 설치형 회귀와 7단계 운영 검증에 남긴다. 현재 다운로드 프로세스는 상주하되 Chrome 세션은 각 작업 종료 시 닫는다. 상세 공급자 로그는 민감 정보 유출을 막기 위해 수집하지 않고 제어된 단계 로그만 제공한다. 외부 요청과 발생한 비용은 취소로 되돌릴 수 없다.

SQLite는 현재 단일 connection을 사용한다. 실행 환경 3.53.1은 WAL-reset 수정 이후 버전이다. 배포 이미지의 SQLite 버전과 수정 여부는 5·7단계에서 다시 확인한다.

## 공식 문서 확인

- [SQLite WAL](https://www.sqlite.org/wal.html): 로컬 파일시스템·connection 관리와 WAL-reset 수정 버전 확인.
- [Python multiprocessing](https://docs.python.org/3.11/library/multiprocessing.html): spawn·프로세스 종료·IPC 수명 확인.
- [Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects): 자식 프로세스 포함·Job Object 종료 정책 확인.
- [OpenAI Docs — rate limits](https://developers.openai.com/api/docs/guides/rate-limits): SDK 재시도와 앱 재시도가 중첩되어 요청이 늘지 않도록 관리하는 근거. timeout/재시도 설정은 설치된 SDK 코드와 함께 확인했다.
