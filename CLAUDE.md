# CLAUDE.md

## 절대 건드리면 안 되는 것들

- **headless=False 유지**: 내장 Chromium에서는 LMS 영상 재생이 실패한다. 반드시 시스템 Chrome + headless=False 조합을 유지할 것.
- **로그인 플로우 순서 고정**: `login.py`의 SSO 버튼 클릭 → 폼 입력 → 로그인 버튼 클릭 순서는 LMS에 맞춰져 있다. 순서를 바꾸면 로그인이 깨진다.
- **DOM 추출 방식 기본**: `video_parser.py`에서 `video.vc-vplay-video1` 요소의 `src` 속성으로 영상 URL을 추출한다. CDP 스니핑(`CdpVideoExtractor`)은 deprecated fallback으로 유지된다.
- **`ssmovie.mp4` 패턴**: LMS 서버가 하드코딩한 영상 경로 패턴이다. LMS가 변경하면 같이 바뀌어야 하므로 향후 추상화 대상.

## 설계 의도

- **GUI 중심 개발**: CLI(`src/main.py`)는 폐기 예정. 단, 각 파이프라인 모듈은 독립 실행/테스트 가능하도록 추상화를 유지한다.
- **기본 엔진**: STT는 whisper.cpp(pywhispercpp, ggml 기반), 요약은 Gemini. 나머지(ReturnZero, OpenAI, ChatGPT)는 대안 옵션이다.
- **ChatGPTSummarizer**: API 호출이 아니라 클립보드 복사 + 브라우저 열기 방식이다. 의도된 동작이다.
- **Python >=3.11,<3.13**: pywhispercpp 호환성 때문. `.python-version`에 `3.11`로 설정되어 있고 uv가 자동 관리한다.

## 알려진 버그 (미수정)

- `summarizer.py`에서 `user_setting.OPENAI_API_KEY`를 참조하지만, `UserSetting` 클래스에 해당 속성이 정의되지 않았다.
- CLI(`src/main.py`)는 상대 import, GUI(`src/gui/`)는 `src.` prefix import를 사용한다. 경로 불일치 주의.

## 배포

- **패키지 매니저**: uv 사용. 의존성 추가는 `uv add`, 설치는 `uv sync`.
- PyInstaller 빌드 시 whisper.cpp(pywhispercpp) + PyAV 포함으로 ~150-200MB.
- Chrome 경로가 Mac용(`/Applications/Google Chrome.app/...`)으로 하드코딩되어 있다. Windows 배포 시 경로 분기 필요.

## 커밋 메시지 컨벤션

`type: 설명` 형식을 사용한다.

- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 스타일 수정 (formatting 등)
- `refactor`: 코드 리팩토링
- `test`: 테스트 코드 추가
- `chore`: 빌드 프로세스/보조 도구 변경
- `build`: 빌드 시스템/외부 의존성 변경
- `ci`: CI/CD 설정 변경
- `perf`: 성능 개선
- `release`: 릴리즈 (버전 태깅 포함)

## 외부 의존성 (시스템 설치 필수)

- `playwright install`: Playwright 브라우저 드라이버 설치가 별도로 필요하다. 단, 내장 Chromium이 아닌 시스템 Chrome을 사용한다.
- `ffmpeg`: 불필요. PyAV(`av` 패키지)를 사용하여 MP4→WAV 변환을 처리한다. 시스템 ffmpeg 설치 없이 동작한다.

<!-- PLANK:START -->
# Plank Integration

This project uses [Plank](https://github.com/Leonamin/plank) for task management. Tasks are stored as markdown files in `.tasks/`.

## Before Starting Work
- Read `.tasks/` to understand current progress. Check `in-progress/` and `todo/` for related tasks.
- If a related task exists, follow its checklist and dependencies.
- If none exists, create a task with a checklist (`- [ ]`) before starting.

## During / After Work
- Update checklist items (`- [ ]` → `- [x]`) without asking. Add a brief result summary.
- When all items are done, ask the user to move the task to `done`.
- Suggest new tasks for any TODOs discovered during work.

## Task File Rules
- Path: `.tasks/{column}/{id}.md` — move files between directories to change columns.
- Moving to `done`: create a weekly subfolder (e.g., `.tasks/done/2026-W12/`).
- Frontmatter: `id`, `title`, `labels`, `priority`, `created`, `depends_on`.
- New task IDs are slugified from the title.
- Deletion is always soft-delete (move to `.tasks/.trash/`).

<!-- PLANK:END -->
