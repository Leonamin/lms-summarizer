# CLAUDE.md

## 절대 건드리면 안 되는 것들

- **시스템 Chrome + headless=False 고정**: 내장 Chromium에서는 LMS 영상 재생이 실패한다.
- **로그인 플로우** (`video_pipeline/login.py`): discovery 페이지(`.btn-ssu-main` 숭실대학교 선택) → gw.php(`.login_btn a` 통합 로그인) → smartid 폼(`input#userid`, `input#pwd`, `a.btn_login`). 순서를 바꾸면 로그인이 깨진다.
- **CDP 추출 기본** (`video_parser.py`): `Network.requestWillBeSent`로 `.mp4`를 가로챈다. `intro.mp4`는 필터링. `DomVideoExtractor`는 fallback.

## 설계 의도

- **GUI 중심**: CLI 진입점은 제거됨. 파이프라인 모듈은 독립 실행 가능하게 유지.
- **기본 엔진**: STT는 faster-whisper, 요약은 Gemini(gemini-3.8-flash). 나머지(OpenAI, Claude, Grok, OpenAI 호환, Clipboard)는 대안. OpenAI 호환(`CustomProvider`)은 OpenRouter·OpenCode GO 등 임의 호환 엔드포인트 지원, `/v1/responses` → `/v1/chat/completions` 자동 폴백. 로컬 모델(Ollama)은 제거됨.
- **클립보드 모드** (`ClipboardProvider`): 클립보드 복사 + 브라우저 열기 방식. 의도된 동작.
- **Python 3.11**: `.python-version`에서 uv가 자동 관리.
- **모델 목록은 하드코딩**되어 있으므로 몇 달마다 최신화 필요 (`src/summarize_pipeline/providers/`).

## 배포

- uv 사용 (`uv add` / `uv sync`).
- PyInstaller: torch는 excludes로 제외(CUDA 감지는 ctranslate2 API + nvidia-smi 의존), `faster_whisper/assets/silero_vad_v6.onnx`를 datas에 포함해야 VAD 동작.
- Chrome 기본 경로는 OS별 분기(`pipeline.py`, `course_scraper.py`). GUI는 `get_chrome_path()` 우선.

## 커밋 메시지

`type: 설명` — feat / fix / docs / style / refactor / test / chore / build / ci / perf / release

## 외부 의존성

- `playwright install` 필요 (단, 시스템 Chrome 사용).
- ffmpeg 불필요 — PyAV가 MP4→WAV 처리.

## 작업 관리

- `.tasks`(Plank)는 제거됨. 작업 관리와 지식 기록은 프로젝트 위키(`./wiki`, OKF 형식)로 수행한다. 구조는 `.agents/wiki-structure.md` 참조.

