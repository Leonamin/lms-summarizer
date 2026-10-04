# 개발 가이드

[문서 목록](../README.md#문서)

모든 명령은 별도 안내가 없으면 저장소 루트에서 실행합니다.

## 소스 구조

```text
src/
├── core/                  # 프레임워크 독립 모델·서비스·저장소·워커
├── desktop/               # 설치형 진입점, OS 동작, 기존 설정 호환
├── gui/                   # Flet 화면·컴포넌트와 호환 import
├── web/                   # FastAPI, HTTP/SSE, 업로드, 서버 설정
├── video_pipeline/        # LMS 로그인·조회·다운로드·재생
├── audio_pipeline/        # 미디어 변환·음성 인식
├── summarize_pipeline/    # AI 요약과 공급자 구현
├── pipeline_stage.py      # 기존 단계 import 호환
└── user_setting.py        # 기존 설치형 입력 호환
frontend/src/              # React 페이지·컴포넌트·API
tests/                     # 코어·데스크톱·웹·파이프라인 검증
```

`src.gui`와 기존 파이프라인 경로는 호환용으로 유지합니다.
코어와 파이프라인의 GUI 의존성 금지는 `tests/test_core_boundaries.py`에서 검증합니다.
테스트는 공통 fake executor를 `test_job_service.py`에서 가져오므로 현재의 단일 검색 경로를 유지합니다.

## 로컬 개발과 검증

```bash
uv sync --extra desktop --extra web
uv run --extra desktop lms-summarizer
uv run lms-summarizer-core
uv run --extra desktop --extra web python -m unittest discover -s tests -v
```

웹 개발:

```bash
npm ci --prefix frontend
npm run build --prefix frontend
uv run --extra web python -m src.web
```

별도 터미널에서 `npm run dev --prefix frontend`를 실행하면 API를 localhost:8000으로 전달합니다.
개발 origin은 백엔드 `LMS_ALLOWED_ORIGINS`에 지정합니다.
데이터와 모델 경로는 [웹 가이드](web.md)를 참고합니다.

## 데스크톱 빌드

```bash
# macOS
bash scripts/build_mac.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1
```

두 스크립트는 자신의 위치에서 저장소 루트를 찾습니다.
직접 PyInstaller를 실행할 때는 저장소 루트에서 아래 명령을 사용합니다.

```bash
uv sync --extra desktop
uv pip install pyinstaller
uv run --extra desktop pyinstaller packaging/lms-summarizer.spec
```

Windows CUDA 번들은 `--extra cuda`도 사용합니다. 결과는 루트 `dist/`에 생성됩니다.
패키징 버전은 `pyproject.toml`에서 읽습니다.
`.github/workflows/release.yml`은 `v*` 태그 push 시 macOS/Windows 빌드와 번들 smoke 검증을 실행합니다.
`scripts/release.sh <patch|minor|major>`는 버전 변경·커밋·태그를 만들고 push 여부를 묻는 릴리즈 도구입니다.

## 파일 배치 원칙

- 사용자 안내는 `docs/`, 의사결정·계획·이력은 `wiki/`에 둡니다.
- 실행 도구는 `scripts/`, 번들 설정은 `packaging/`, 정적 자원은 `assets/`에 둡니다.
- `examples/user_settings.json`은 레거시 URL 입력 예제입니다. 필요하면 실행 디렉토리의
  `user_settings.json`으로 복사해 사용합니다. 사용자 설정과 비밀 값은 커밋하지 않습니다.
- `src/`에는 소스만 두며 실행 결과와 사용자 데이터를 추가하지 않습니다.
- 새 boolean 이름은 `is`, `has`, `can`, `should`, `needs` 접두사를 사용합니다.
- 커밋 전 staged diff를 확인하고 `feat(scope): ...`, `fix(scope): ...`,
  `refactor(scope): ...` 등 변경에 맞는 Conventional Commits 형식을 사용합니다.

## 공통 실행 구조

### 공통 코어와 실행 환경

공통 모델·프롬프트·검증·저장 경계는 `src/core`, 설치형 호환 입력·저장·OS 동작은
`src/desktop`, 웹 전송 경계는 `src/web`에 있습니다. 기존 GUI import 경로는 호환용으로 유지합니다.

- 설치형: `uv sync --extra desktop`, `uv run --extra desktop lms-summarizer`
- Windows CUDA 설치형: `uv sync --extra desktop --extra cuda`
- 코어 진단: `uv run lms-summarizer-core`
- 웹 의존성: `uv sync --extra web` (FastAPI 서버/API)
- 코어 검증: `uv run python -m unittest discover -s tests -v`

파이프라인은 출력 경로와 실행 설정·자격 증명을 명시적으로 받습니다.
`output_dir` 생성자 인자 또는 기존 `downloads_dir` 속성으로 출력 경로를 전달할 수 있습니다.
설치형 `settings.json`의 설정·과목 캐시·이력 구조와 기존 결과 경로는 유지합니다.
웹 저장 경로는 별도로 전달하며 설치형 데이터를 자동으로 가져오지 않습니다.

### 영속 작업 서비스 (3단계)

`src.core.services.jobs.JobService`는 앱 수명 동안 한 번 생성·시작하고 종료 시 `close()`합니다.
데이터 디렉토리에 SQLite와 관리 입력·산출물을 저장하며, 같은 디렉토리의 중복 supervisor 실행은 차단합니다.
설치형 화면은 공통 서비스를 직접 호출하고, 웹 서버는 FastAPI 수명에 연결한 공통 서비스를 HTTP/SSE로 제공합니다.

- `import_file(context, path)`: 사용자 원본을 보존하고 관리 입력의 파일 ID 반환
- `submit(context, sources, revision, idempotency_key=...)`: 고정 설정으로 작업 제출
- `detail`, `list_jobs`, `stage_counts`, `artifact_path`: 소유자별 작업·단계·산출물 조회
- `cancel`, `cancel_all`, `retry`: 대상 시도 확인, 취소, 원래 설정·입력으로 새 시도 생성
- `events_since`, `subscribe`: 영속 이벤트 조회·구독; 구독 해제는 작업 취소와 무관
- `secret_usage`, `delete_secret`: 참조 중 비밀 버전 보호 및 명시적 폐기의 영향 작업 조회

네 단계는 각 한 개의 상주 spawn 프로세스를 사용하고 서로 다른 작업을 동시에 처리합니다.
강제 취소는 프로세스 트리와 IPC를 회수한 후 슬롯을 교체합니다. 재시작 시 대기 작업은 복원하고,
실행 중 시도는 `interrupted`로 기록합니다. 실패·취소·중단 작업은 자동 재시도하지 않습니다.

서비스 기본값은 활성 작업 200개, 제출 50개, 입력 4 GiB, 디스크 여유 2 GiB,
취소 유예 5초, 종료 유예 10초, 단계 제한 30분입니다. 생성자에서 조정할 수 있습니다.
모델 캐시는 `models_dir`로 전달하며 기본값은 데이터 디렉토리 아래 `models/`입니다.
공급자 요청은 연결 10초·요청 120초 기본값이며 SDK 자동 재시도를 끕니다.
기존 다운로드 무결성 재시도는 유지합니다. 취소는 이미 전송된 외부 요청·비용을 되돌리지 못합니다.

성공 후 `keep_source`(원본 영상)·`keep_audio`(변환 오디오) 설정을 각각 적용합니다. 선택하지
않은 중간 산출물은 정리합니다. 실패·취소·중단의 관리 입력과 다른 작업이 참조하는 입력은
보존합니다. 원문·요약·수동 프롬프트·이력은 자동 삭제하지 않습니다.
사용하지 않은 관리 입력은 기본 24시간, 이벤트·로그는 7일·10만 행 한도로 정리합니다.

검증: `uv run --extra desktop --extra web python -m unittest discover -s tests -v`.
실제 LMS·유료 공급자·로컬 Whisper 추론과 OS별 실행 검증은 후속 단계에서 별도로 진행합니다.
