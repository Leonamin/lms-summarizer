---
type: Log
title: "코어·웹 2단계: 공통 모델·설정·저장 분리"
description: "프레임워크 독립 코어, 명시적 실행 설정과 설치형 JSON 호환 검증"
status: completed
created: 2026-09-27
okf_version: "0.1"
---

# 코어·웹 2단계: 공통 모델·설정·저장 분리

[상세 계획](../plans/core-web-dashboard-plan.md) · [TODO](../plans/core-web-dashboard-todo.md) · [ADR-003](../decisions/003-web-runtime-and-job-contract.md)

## 구현

- `src/core/models`: 기존 과목·강의와 단계 모델을 이동하고 JobStatus·ResultKind, UserContext·LMSCredentials·PromptSettings·SettingsRevision을 정의했다. 기존 import 경로는 호환 facade로 남겼다. 작업·시도·산출물 영속 모델과 전이는 3단계다.
- `src/core/prompts.py`, `validation.py`: 기존 프롬프트·입력 검증을 이동했다. 코어 Chrome 검증은 명시적 경로를 받으며 GUI 어댑터가 설치 경로를 탐지한다. 입력 확장자별 시작 단계와 종료 단계 검증을 추가했다.
- `src/core/repositories`: 설정·이력·캐시·비밀 저장 protocol과 구현, 명시적 데이터 경로를 마련했다. JSON은 임시 파일·fsync·원자 교체를 사용하고 프로세스 내부 공유 lock으로 변경을 직렬화한다. 캐시는 owner·LMS account·key로 구분한다. 비밀은 UUID 버전 참조, owner 검사, 디렉토리 0700·파일 0600을 사용한다.
- `src/core/services/settings.py`: 제출 설정을 직렬화된 불변 revision으로 복사하고 비밀 참조를 분리한다. 설정 안의 비밀 필드를 거부한다. 영속 revision 저장과 실행 서비스 연결은 3단계다.
- `src/core/runtime/item_processor.py`: 이력 쓰기와 수동 챗봇 동작을 주입받는 처리기다. GUI 클래스는 데스크톱 저장·OS 콜백을 전달하는 어댑터다. 기존 취소 스레드 구조는 유지하며 3단계의 프로세스 취소 구현으로 대체한다.
- 다운로드에서 GUI 저장 경로 참조, 요약에서 GUI 기본 프롬프트 참조, STT에서 UserSetting 전역 조회를 제거했다. 파이프라인은 출력 디렉토리와 자격 증명을 명시적으로 받는다. ReturnZero는 client_id/client_secret을 요구하며 단일 레거시 키를 임의로 인증 쌍으로 해석하지 않는다.
- 클립보드 공급자는 프롬프트를 생성한다. 데스크톱이 콜백을 주입할 때만 pyperclip·webbrowser를 실행한다. 웹의 manual_ready 상태 연결은 3·6단계다.
- `src/desktop/legacy_storage.py`는 기존 설정 경로·JSON 구조·캐시·이력·알 수 없는 필드를 유지하면서 원자적 저장을 사용한다. `legacy_import.py`는 원본을 변경하지 않고 설정·비밀·캐시·이력을 분리해 읽는다. STT endpoint/model이 키 맵에 섞인 구조를 정상 설정 필드로 변환한다. 웹은 이 어댑터를 자동 호출하지 않는다.
- 사용자 선택 로컬 원본은 STT·후처리에서 삭제하지 않는다. 중간 파일의 최종 수명 관리는 3단계다.
- pyproject의 기본 의존성은 코어, extras는 desktop/web/cuda로 분리하고 uv.lock을 갱신했다. 기존 `lms-summarizer` 명령은 데스크톱 진입점을 거쳐 GUI를 실행하며 `lms-summarizer-core`는 코어 진단이다. `src/web`는 전송 경계만 마련했고 서버/API 진입점은 5단계다. 빌드 스크립트는 desktop extra, Windows는 cuda extra를 설치한다.

## 검증

- `python3 -m unittest discover -s tests -v`: 10개 통과.
- `uv run --extra web python -m unittest discover -s tests -v`: Python 3.11.15에서 10개 통과.
- 웹 extra 환경에서 Flet·pyperclip 미설치를 확인하고 VideoPipeline·AudioToTextPipeline·SummarizePipeline import 및 수동 프롬프트 생성을 확인했다.
- 별도 import 차단 테스트로 전체 core 모듈이 Flet·GUI·FastAPI·pyperclip 없이 import되는 것을 확인했다. AST 검사로 core·각 pipeline의 GUI/UserSetting import 재도입을 검사한다.
- 동시 이력 추가 80회, 원자 교체 실패 시 이전 데이터 유지, owner·계정 캐시 분리, 경로 탈출 거부, 비밀 버전·권한·소유자, 레거시 원본 보존·정규화, 설정 고정·비밀 배제, 로컬 원본 보존·주입 이력, 입력 단계 검증을 확인했다.
- desktop extra 환경에서 GUI 진입점 import와 동적 로더의 UserSetting·VideoPipeline·AudioToTextPipeline·SummarizePipeline 로딩을 확인했다.
- `python3 -m compileall -q src`와 `git diff --check` 통과.

## 범위와 후속 작업

2단계 완료 기준인 Flet 없는 코어 사용, 명시적 경로·설정 전달, 기존 설치형 데이터 보존을 확인했다. 실제 LMS·유료 공급자·모델 추론은 이번 검증에서 실행하지 않았다. GUI 실제 조작과 macOS/Windows PyInstaller 빌드는 4단계다. 작업 DB·단계 프로세스·실제 취소·복구·비밀 폐기/참조 관리는 3단계이며, 현재 JSON 저장 lock은 다중 프로세스 DB 대체 수단이 아니다. 기존 설치형 비밀은 호환 저장 형식을 유지하고 웹용 비밀 저장소를 마련했다. desktop 설치 시 requests의 chardet 7 호환 경고를 관찰했지만 모듈 로딩은 통과했다.
