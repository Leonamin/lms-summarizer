---
type: Log
title: "코어·웹 1단계: 기능 조사와 구현 계약"
description: "활성 기능 목록, 기술 선택, 데이터·API·실행 계약 및 환경 검증 현황"
status: completed
priority: p1
created: 2026-09-27
okf_version: "0.1"
---

# 코어·웹 1단계: 기능 조사와 구현 계약

[전체 계획](../plans/core-web-dashboard-plan.md) · [진행 TODO](../plans/core-web-dashboard-todo.md) · [제품 결정](../decisions/002-core-and-web-dashboard.md)

## 상태와 근거

2026-09-27 소스의 엔트리포인트·호출 경로를 조사했다. 아래 기능 현황은 정적 분석 결과이며 GUI 실제 실행 성공을 의미하지 않는다. 기술 선택은 사용자 요구에 맞춰 작성한 구현 기준이다. 실제 LMS 검증은 별도 완료 항목으로 관리한다.

## 활성 기능과 웹 검증 목록

파일 경로는 저장소 루트 기준이다. 활성 경로: `src/gui/main.py` → `MainView` → `Sidebar`, `SourceSelector`, `CourseListView`, `PipelineMonitor`, `LogDrawer`, `QueueManager` → `ItemProcessor`와 각 파이프라인.

| ID | 기능·현재 상태 | 코드 근거 | 웹 완료 확인 |
|---|---|---|---|
| F01 | 학번·비밀번호 입력·보기·저장 | `components/left_panel/account_section.py`, `input_field.py`, `core/file_manager.py` | 재접속 후 학번 유지, 비밀은 설정 여부만 응답, 교체·삭제 |
| F02 | 엔진별 요약 키·모델·호환 URL 저장 | `components/left_panel/ai_settings.py`, `model_selector.py` | 엔진 전환·재시작, 키 선택적 custom, 작업별 설정 고정 |
| F03 | STT 4엔진·3개 로컬 모델·장치·힌트·반복 제거 | `components/left_panel/stt_settings.py`, `audio_pipeline/model_manager.py` | 공급자별 필수 설정, CPU 실행, 모델 변경·재사용 |
| F04 | 요약 모드·과목 분야·직접 과목명·미리보기·초기화 | `sidebar.py`, `views/settings_view.py`, `summarize_pipeline/prompts.py` | 동일 설정의 프롬프트 일치, 제출 후 변경 격리 |
| F05 | 원본 보관·저장 경로·폴더 열기 | `sidebar.py`, `left_panel/storage_path.py`, `item_processor.finalize` | 웹은 서버 볼륨·보관 설정과 결과 다운로드로 대응 |
| F06 | 여러 URL 입력, 작업 실행 중 추가 | `MainView._enqueue`, `QueueManager.submit` | URL 검증·일괄 제출·추가·동일 요청 중복 방지 |
| F07 | 파일 여러 개 선택·제거·종류별 진입 | `MainView._enqueue_files`, `SourceSelector` | mp4/ts→변환, wav/mp3→STT, txt→요약; 업로드 완료 전 제출 차단 |
| F08 | 과목 조회·학기·즐겨찾기 표시·캐시 | `views/course_list_view.py`, `CourseListWorker`, `CourseScraper` | 계정 경계, 과목 캐시 만료·갱신, 로그인 오류 표시 |
| F09 | 주차 강의·시간·출석 표시·전체 선택·새로고침 | 같은 경로 | 예정/비영상 선택 제외, URL 선택 제출, 계정별 강의 캐시 |
| F10 | CDP 우선 영상 추출·DOM fallback·로그인 | `video_pipeline/login.py`, `video_parser.py`, `pipeline.py` | 실제 시스템 Chrome 로그인·중첩 프레임·MP4 포착·다운로드 |
| F11 | 다운로드 재시도·완전성 검사·이름별 저장 | `video_pipeline/download_video.py` | 잘린 파일 실패, 재시도, 같은 강의명 충돌 방지 |
| F12 | PyAV 변환·STT·요약 공급자 실행 | 각 파이프라인, `providers` | 단계별 결과, 오류 구분, 독립 단계 동시 실행 |
| F13 | 클립보드 프롬프트·챗봇 링크·별도 텍스트 | `ClipboardProvider`, `ItemProcessor._write_chatbot_text` | 접속 기기 복사·수동 복사 fallback·다운로드, manual_ready 결과 |
| F14 | 단계별 표시·상세 펼치기·로그·전체 중지 | `PipelineMonitor`, `LogDrawer`, `MainView._handle_queue_stop` | 각 단계 대기/실행 분리, 작업별 로그·취소·재시도 추가 |
| F15 | Chrome 경로 감지·선택·debug, 자동 폴더 열기 설정 | `SettingsView`, `file_manager` | 웹 서버 경로·headed 진단으로 대응, 호스트 OS 열기 호출 제거 |
| F16 | 버전 표시·시작 시/수동 업데이트 확인 | `components/header.py`, `core/update_checker.py` | 버전·업데이트 확인·배포 절차 안내, 자동 교체하지 않음 |
| F17 | 이력 저장은 활성, 조회 UI는 현재 없음 | `ItemProcessor.finalize`, `file_manager.load_history` | 웹 이력·원문·요약 열람·다운로드 신설 |
| F18 | 직접 raw 프롬프트 저장·레거시 호환은 코어에 존재, 편집 UI 없음 | `file_manager.get_summary_prompt/set_summary_prompt` | 웹 사용자 프롬프트 편집과 구조화 모드 선택, 호환 로딩 |
| F19 | 수동 시작 단계·산출물 감지는 구형 UI 경로에만 존재 | `StageSelector`, `ArtifactDetector`, `right_panel/options_section.py` | 업로드 자동 진입 유지; 작업 입력에서 실행 종료 단계 선택으로 부분 처리 제공 |
| F20 | 재시작 복구·개별 취소·재시도는 현재 없음 | 기존 `QueueManager` 메모리 모델 | 대기 복원·실행 중단, 개별 취소·재시도·시도 이력 |

현재 활성 화면에서 `QueuePanel`, `ProgressModal`, `StageSelector`는 생성하지 않는다. `workers/__init__.py`는 구형 ProcessingWorker를 import하지만 실제 작업 제출은 QueueManager를 사용한다. 파일 존재와 활성 기능을 구분하고, 삭제는 코어 전환 후 수행한다.

### 호환 시 반드시 정리할 기존 불일치

- ReturnZero UI는 단일 `stt_api_key`를 저장하지만 실행기는 `UserSetting()`의 client_id/client_secret을 사용한다. 동일 키로 동작한다고 가정하지 않고, 실제 공급자 인증 규격 확인 후 명시적 자격 증명 계약으로 통합한다.
- 업로드 시작 단계의 미지원 확장자는 현재 변환으로 fallback한다. 웹은 mp4/ts/wav/mp3/txt를 명시적으로 지원하고 미지원 파일은 오류로 안내한다.
- 현재 wav/mp3 입력은 STT 후 삭제될 수 있고 mp4 입력도 후처리에서 삭제될 수 있다. 웹은 서버 소유 복사본에만 보관 정책을 적용하고 설치형 사용자 선택 원본은 삭제하지 않는다.
- 현재 구조화 summary_mode가 raw prompt보다 우선한다. 웹은 `prompt_mode=structured|custom`으로 우선순위를 명시한다.
- 문서는 headless=False 고정이라 하나 현재 MainView/CourseListWorker는 `not debug_mode`를 전달한다. 실제 LMS 검증 전 어느 방식도 검증 완료로 주장하지 않는다.

## 선택한 기술과 패키지 경계

구체적 패키지 버전은 구현 착수 시 lock에 고정한다. 이번 단계에서 UI를 구현하지 않는다.

| 영역 | 구현 기준 | 이유 |
|---|---|---|
| 웹 UI | React + TypeScript + Vite, 정적 SPA | 별도 프런트엔드, PC·휴대폰 공통 UI; SSR 요구 없음 |
| API | Python 3.11, FastAPI + Uvicorn 단일 서버 프로세스, Pydantic API DTO | 기존 Python 코드 연결, OpenAPI 계약, 앱 수명 관리 |
| DB | Python sqlite3, SQLite 로컬 볼륨, WAL·외래키·busy_timeout·버전 마이그레이션 | 개인 서버 영속 상태, 별도 DB 서비스 불필요 |
| 이벤트 | SSE 단일 연결 + REST 명령 | 서버→화면 상태 전달, 재접속 시 전체 조회 |
| 실행 | 프레임워크 독립 supervisor + 단계별 상주 자식 프로세스 | 실제 취소·격리, STT 모델 재사용 |
| 배포 | 다단계 Docker 빌드, FastAPI가 SPA 정적 파일 제공, Compose 1서비스 | 같은 origin, 한 포트, Python 실행 이미지에 Node 불필요 |
| 미디어 | 설치된 Google Chrome + CDP, PyAV | 코덱 요구 유지; fixture 생성용 ffmpeg는 조사 이미지에만 필요 |

초기 패키지는 `src/core/{models,services,repositories,runtime}`, `src/web/{api,schemas}`, 기존 `src/gui` 및 `frontend/`로 구성한다. 기존 파이프라인은 어댑터로 유지하며 GUI import를 제거한다. core 모델은 dataclass/enum/protocol로 정의하고 Pydantic은 웹 경계에서 사용한다. 데스크톱은 core를 직접 호출한다.

단일 서비스라도 supervisor와 자식 프로세스는 앱 내부 실행 구성이다. Uvicorn 다중 workers와 replica는 사용하지 않는다. 데이터 디렉토리 실행 락으로 중복 supervisor 기동을 차단한다. DB는 네트워크 파일시스템에 두지 않으며 WAL 버전 관련 최신 수정 사항을 배포 의존성 선택 때 확인한다.

## 데이터 계약

모든 시간은 UTC ISO 8601, ID는 UUID 문자열, 상태 값은 영문으로 정의한다.

| 모델 | 필수 데이터 |
|---|---|
| UserContext | owner_id; 초기 서버가 `local`로 고정, 클라이언트 지정 불가 |
| SettingsRevision | id, owner_id, 요약/STT 설정, resolved_prompt, input/end_stage, 보관 정책, secret_version 참조 |
| Job | id, owner_id, source_kind/url/upload_id, initial_stage/end_stage, settings_revision_id, current_attempt_id, status, created_at, revision |
| Attempt | id, job_id, number, generation, status, current_stage, cancel_requested_at, started/ended_at, error_code, safe_message |
| StageRun | id, attempt_id, stage, queued/running/completed/failed 상태, 시간, input/output_artifact_id |
| Artifact | id, owner_id, job/attempt_id, kind, 내부 상대 경로, 표시명, size, input_pin, 완성/삭제 상태 |
| Upload | id, owner_id, filename, expected/received_size, uploading/ready/failed, 경로·시간 |
| SecretVersion | id, owner_id, provider/account, version; 값은 별도 저장소 |
| Event/Log | 증가 seq, owner/job/attempt_id, type, 안전한 payload, timestamp |
| CourseCache | owner_id, LMS 계정 참조, course_id, 조회시각·만료, 데이터 |

Job 상태: `queued`, `running`, `cancelling`, `completed`, `failed`, `cancelled`, `interrupted`. `failed/cancelled/interrupted`는 공통 재시도 가능 종료군이다. `completed`의 `result_kind=summary|manual_ready|stage_artifact`로 결과 종류를 구분한다. 일부 단계만 처리하는 작업은 end_stage 산출물에서 완료한다.

설정과 프롬프트는 제출 때 서버에서 해석·고정한다. API는 비밀 원문을 반환하지 않고 `configured`를 반환한다. 비밀 변경은 새 버전을 만들고 이미 제출한 작업은 기존 버전을 참조한다. 최초 비밀 저장은 별도 로컬 파일, 디렉토리 0700·파일 0600·원자적 교체로 관리한다. 암호화 보관은 이번 결정에 포함하지 않는다. 참조 중 버전은 보존하고 명시적 비밀 폐기 시 영향 작업을 안내한다. HTTP DTO/로그/SSE에 비밀 값이나 임의 서버 경로를 넣지 않는다.

설치형 JSON은 읽기 호환 어댑터로 가져오고 원본을 보존한다. 웹은 설치형 설정을 자동으로 가져오지 않는다. STT의 base_url/model과 키가 기존 stt_api_keys에 섞인 구조를 정상 필드로 변환한다.

## 실행·취소·복구 계약

- DB가 대기와 실행 상태의 기준이다. 메모리 큐는 실행 알림만 담당한다. 슬롯은 단계별 FIFO 한 개, 단계 간 독립 실행이다.
- supervisor만 상태를 확정한다. 자식은 generation/attempt/stage 식별자가 있는 진행·결과 메시지를 보낸다. 파일 최종 경로 확정과 DB 완료 기록의 간격에서 생긴 고아 파일은 복구 시 정리하고 완성 확인 없는 파일은 사용하지 않는다.
- 단계 완료, 다음 StageRun 대기 생성, Event 기록은 하나의 DB 트랜잭션이다. 자식은 DB에 직접 쓰지 않는다.
- 각 단계에 상주 spawn 프로세스 1개를 둔다. STT는 설정 지문으로 모델을 재사용한다. 다운로드 프로세스는 Chrome 세션과 진행 중 다운로드를 소유한다.
- 취소 시 대기는 즉시 cancelled, 실행 중은 cancelling → 협력 종료 최대 5초 → 프로세스 트리 종료·회수 → cancelled로 전환한다. 슬롯은 회수 후에만 재사용한다. Unix 프로세스 그룹과 Windows Job Object 등 플랫폼별 자식·Chrome 종료 구현이 필요하다.
- 외부 API에 이미 전송한 요청과 비용은 취소로 되돌릴 수 없다. 늦은 응답은 확정하지 않고 자동으로 새 유료 호출을 시작하지 않는다.
- 사용자 재시도는 새 Attempt로 원래 입력 단계부터 실행한다. 첫 버전은 완료 단계 자동 재사용을 하지 않는다. 동일 제출 설정·비밀 버전을 쓰고 원본·비밀이 없으면 `input_missing`/`credentials_missing`으로 안내한다. 설정을 바꾸려면 새 작업으로 제출한다.
- 실패·취소·중단 시 원래 입력을 보존한다. 성공 후에는 원본 보관 설정을 적용한다. 다른 작업/시도가 참조하는 업로드는 참조가 끝나기 전 삭제하지 않는다.
- 재기동은 단일 supervisor 확보 → 이전 running/cancelling을 interrupted 기록 → queued 복원 → 워커 기동 순서다. 자동 shutdown은 사용자의 취소와 구분한다.
- 종료는 신규 제출 차단, 대기 보존, 실행 협력 종료 10초 및 프로세스 회수, 중단 기록으로 수행한다. 컨테이너 stop_grace_period는 30초를 기본으로 한다.
- 다운로드는 기존 완전성 재시도를 유지한다. 공급자 HTTP 연결/읽기 timeout과 최대 단계 시간을 분리하고, 유료 요약·STT는 사용자 재시도 중심으로 운영한다.

## API v1 계약

| 메서드·경로 | 요청·응답 / 의미 |
|---|---|
| GET /api/v1/me | local 사용자·인증 모드 |
| GET/PATCH /api/v1/settings | 비밀 제외 설정과 revision; PATCH는 expected_revision 불일치 시 409 |
| PUT/DELETE /api/v1/secrets/{provider} | 비밀 등록·교체·폐기; 응답은 configured만 |
| GET /api/v1/catalog | STT/요약 엔진·모델·설정 항목·입력 형식 |
| GET /api/v1/courses | 캐시 조회; cache_age·조회 작업 ID |
| POST /api/v1/course-refreshes | LMS 조회 작업 202, 조회 상태는 응답 ID로 추적 |
| GET /api/v1/courses/{id}/lectures | 계정별 캐시; 명시적 refresh 요청은 별도 조회 작업 |
| POST /api/v1/uploads | filename/size로 업로드 예약, id 반환 |
| PUT /api/v1/uploads/{id}/content | raw 스트림 전체 업로드, 서버 검증 후 ready; 실패 시 처음부터 재전송 |
| GET/DELETE /api/v1/uploads/{id} | 상태/미사용 업로드 취소·삭제 |
| POST /api/v1/jobs | sources 배열 + settings_revision + end_stage; Idempotency-Key, 작업별 검증 결과 |
| GET /api/v1/jobs | 상태·검색·cursor·limit 페이지 목록과 event cursor |
| GET /api/v1/jobs/{id} | 시도·단계·산출물·재시도 가능 여부 |
| POST /api/v1/jobs/{id}/cancel | 대상 attempt_id 지정; 이미 종료면 현재 상태 반환 |
| POST /api/v1/jobs/{id}/retry | 대상 attempt_id+Idempotency-Key; terminal에서 새 시도, 중복/활성이면 409 |
| POST /api/v1/jobs/cancel-all | 요청 시 존재하는 활성 시도만 snapshot 취소 |
| GET /api/v1/jobs/{id}/logs | cursor 로그, 원문·비밀·서명 URL 제외 |
| GET /api/v1/artifacts/{id}/content | UTF-8 원문·요약·프롬프트; 큰 텍스트는 페이지 또는 다운로드 안내 |
| GET /api/v1/artifacts/{id}/download | 실제 파일 다운로드; 사용자 소유권과 완성 여부 확인 |
| GET /api/v1/events | SSE seq, job.updated/stage.updated/log/course.updated/reset |
| GET /api/v1/system | 버전·업데이트·Chrome/STT/용량 진단·설정된 한도 |

LMS 조회도 브라우저 프로세스에서 다운로드 사이에 순서대로 수행하며 동시에 같은 Chrome을 조작하지 않는다. 조회 작업 상태 API는 `/course-refreshes/{id}`를 사용한다. 일반 큐 처리 오류와 별도로 표시하고 인증 정보를 프로필별로 격리한다.

SSE는 Last-Event-ID를 지원하며 보존 범위 밖이면 reset을 보내 전체 목록·상세를 재조회한다. 첫 구독 전에 snapshot/event cursor를 얻고 이후 cursor 뒤 이벤트를 처리한다. revision 낮은 갱신을 무시한다. 초당 과도한 진행 로그는 합치고 heartbeat는 15초다. API·정적 파일은 같은 origin, 초기 LAN HTTP를 기본으로 하되 허용 Origin/Host를 명시하고 무제한 CORS를 열지 않는다.

오류 envelope: `{error:{code,message,field?,retryable?}}`. HTTP 400 입력 형식, 404 미존재, 409 상태·revision 충돌, 413 업로드 한도, 422 의미 검증, 507 디스크 부족. 디스크 경로·비밀·서명 URL을 message로 노출하지 않는다.

## 파일·보관과 조정 가능한 기본값

- 데이터는 `/data` 로컬 볼륨, 모델은 `/models` 볼륨. 웹 입력은 파일 ID로 지정한다.
- 업로드 mp4/ts/wav/mp3/txt; 확장자와 실제 미디어·텍스트 파싱을 함께 확인한다. UTF-8/BOM 텍스트를 지원한다.
- 파일 1개 기본 4 GiB, 제출 1회 50항목, 활성 작업 최대 200개. 모두 서버 설정으로 조정한다. 디스크 여유 기본 2 GiB 이하이면 새 업로드·단계 실행을 보류/거부하며 실행 중 ENOSPC는 명시적으로 실패 처리한다.
- 저장은 작업·시도 ID 아래 `.part` 후 원자 rename. 파일명은 표시용이다. 기존 파일을 덮어쓰지 않는다.
- 미완료·미사용 업로드는 24시간 후 정리한다. 실패·취소·중단 입력은 재시도용으로 유지한다. 완료 작업은 원본 보관 옵션, 중간 WAV는 후속 성공 후 정리한다.
- STT 원문·요약·프롬프트·작업 이력은 자동 삭제하지 않는다. 로그·SSE 저널은 기본 7일, 10만 행 한도로 정리한다. 시간·행 제한은 설정 가능하다.
- 렌더링은 원문 plain text, 요약 Markdown은 raw HTML 비활성화와 안전한 링크 정책을 사용한다.
- LAN HTTP에서는 Clipboard API가 허용되지 않을 수 있으므로 수동 전체 선택·복사와 파일 다운로드를 제공한다. 자동 복사 성공은 실제 성공 응답 뒤에만 표시한다.

## 환경 검증 현황

- Ubuntu 26.04 LTS, amd64 확인.
- Docker Engine 29.6.2, Compose v5.3.1, daemon 접근 확인. 기존 서비스는 변경하지 않았다.
- host PATH에 google-chrome/chromium 없음. 컨테이너에는 Google Chrome을 직접 설치한다.
- lspci는 AMD HawkPoint 내장 GPU를 표시하며 NVIDIA 장치는 확인되지 않고 nvidia-smi도 없다. 초기 faster-whisper는 CPU 기준; NVIDIA CUDA 프로필은 후속 선택사항이다.
- 최초 조사에서 기본 설정 경로에 계정 파일이 없었다. 이후 사용자가 `.local/lms-probe/settings.json`에 검증용 설정을 작성했고 읽기 전용 mount로 사용했다. 해당 디렉토리는 Git에서 제외하고 비밀 원문은 출력하지 않았다.
- [검증 도구](../../scripts/browser_probe/README.md): 격리 컨테이너의 합성 H.264/AAC 재생·CDP 포착을 두 모드에서 확인했다.

| 검증 | 버전·조건 | 결과 |
|---|---|---|
| Docker 이미지 빌드 | Python 3.11 bookworm, Playwright 1.56.0, Google Chrome 154.0.8037.57 | 성공 |
| headless 재생 | 외부 네트워크 없음, H.264/AAC fixture | currentTime > 0, readyState=4, H.264/AAC probably |
| headless CDP | Network.requestWillBeSent | fixture.mp4 URL 포착 성공 |
| headed 재생 | Xvfb 가상 화면, 외부 네트워크 없음 | currentTime > 0, readyState=4, H.264/AAC probably |
| headed CDP | Network.requestWillBeSent | fixture.mp4 URL 포착 성공 |

이 Playwright 버전은 조사 이미지에서 고정한 버전이며 프로젝트 의존성 lock은 변경하지 않았다. 조사 이미지와 Docker 빌드 캐시만 추가했고 실행 컨테이너는 --rm으로 제거했다. headless와 headed 모두 가능하므로 실제 LMS에서 headless를 먼저 검증하고 필요할 때 headed를 사용한다.

### 실제 LMS 검증 결과 (2026-09-27)

`lms_probe.py`는 기존 VideoPipeline 로그인과 `extract_video_url(method="cdp")`를 그대로 사용했다. Google Chrome 154.0.8037.57, Playwright 1.56.0의 Docker headless 실행에서 다음 결과를 확인했다.

- login=true: LMS 로그인 후 Canvas 호스트 도달.
- cdp_mp4_captured=true: 실제 강의 MP4 요청 3개 포착, CDP 추출 성공.
- title_found=true: 강의 제목 확보.
- success=true, 정상 종료 및 브라우저 정리.

DOM fallback은 사용하지 않았다. 학번·비밀번호·강의 제목 원문·강의 URL·추출된 영상 주소는 출력하거나 위키에 저장하지 않았다. 설정 파일은 읽기 전용, 컨테이너는 --rm으로 제거했다. 실제 headed 실행은 필요하지 않아 수행하지 않았다. 전체 영상 다운로드·미디어 스트림 구성·STT·요약·모든 강의 유형 성공은 이번 검증 범위가 아니다. 후속 기능 검증에 남긴다.

따라서 초기 컨테이너는 시스템 Google Chrome headless를 기준으로 진행하고 headed/Xvfb는 필요한 경우 진단 경로로 둔다. 프로젝트의 기존 headless=False 설명은 이 환경의 확인 결과와 구분해야 한다.

## 검증 기준과 다음 단계

코드 조사·기술 계약·Docker Chrome 실제 LMS 로그인과 CDP 검증을 완료하여 1단계를 완료 처리했다. 다음 작업은 2단계 공통 모델·설정·저장 분리다. 실제 LMS 결과는 제공된 강의 한 개와 검증 이미지 버전에 한정되며 전체 기능 검증은 후속 단계에서 수행한다. 본 문서의 기술·정책 값은 구현 중 근거가 달라지면 ADR과 함께 갱신한다.

## 공식 문서 근거

- [React의 Vite 기반 앱 구성](https://react.dev/learn/build-a-react-app-from-scratch), [Vite 시작 문서](https://vite.dev/guide/): 별도 SPA 빌드 구성 참고.
- [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/): 서버 시작·종료와 서비스 수명 연결.
- [SQLite WAL](https://www.sqlite.org/wal.html), [SQLite 변경 이력](https://www.sqlite.org/changes.html): 동시 조회·쓰기, 로컬 파일시스템 제약과 배포 버전 확인.
- [Playwright Chrome·코덱](https://playwright.dev/python/docs/browsers): 공식 Chrome 채널과 Chromium의 코덱 차이.
- [Python multiprocessing](https://docs.python.org/3.11/library/multiprocessing.html): spawn·프로세스 종료 및 IPC 손상 가능성; 강제 종료 후 IPC와 프로세스를 새로 생성한다.
- [Docker 다중 프로세스](https://docs.docker.com/engine/containers/multi-service_container/): init과 자식 회수 참고.
- [MDN SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events), [Clipboard.writeText](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText): 재접속·이벤트와 보안 컨텍스트 제한.

기술 선택과 기본값은 위 자료와 프로젝트 요구에서 내린 설계 판단이며 공식 문서가 프로젝트 구조 자체를 권장한다는 의미는 아니다.
