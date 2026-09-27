# 🎓 LMS 강의 AI 요약기

숭실대학교 LMS 강의 내용을 AI가 자동으로 분석하고 핵심을 요약해주는 학습 보조 도구입니다.

> **이런 분께 추천합니다**: 강의 내용을 빠르게 파악하고 싶거나, 핵심 개념만 정리해서 학습 효율을 높이고 싶은 분

---

## 📌 이 프로그램이 하는 일

1. **강의 페이지 접근 및 콘텐츠 분석** — LMS에 로그인하여 강의 콘텐츠를 처리합니다
2. **음성 → 텍스트 변환** — AI(Whisper)가 강의 내용을 텍스트로 변환합니다
3. **AI 요약 생성** — AI가 핵심 내용을 요약해줍니다

결과물로 요약 텍스트 파일이 저장됩니다. (.txt)

---

## 🧩 지원 기능

### 음성 인식 (STT) 엔진

| 엔진 | 방식 | 비용 | 특징 |
| --- | --- | --- | --- |
| **faster-whisper** | 로컬 실행 | 무료 | 기본 엔진, API 키 불필요, GPU(CUDA) 지원 |
| **OpenAI 호환 엔드포인트** | 로컬/원격 서버 | 무료~ | Speaches, faster-whisper-server, LM Studio 등 연결 |
| **OpenAI Whisper API** | 클라우드 API | 유료 ($0.006/분) | 로컬 모델 다운로드 불필요 |
| **ReturnZero** | 클라우드 API | 유료 | 높은 정확도 |

### AI 요약 엔진

| 엔진 | 지원 모델 | 비용 |
| --- | --- | --- |
| **Gemini** (Google) | 3.8 Flash (권장), 3.6 Flash, 3.1 Pro | 무료 티어 제공 |
| **OpenAI** | GPT-5.6 Luna (권장), GPT-5.6 Terra, GPT-5.6 Sol | 유료 |
| **Claude** (Anthropic) | Claude Sonnet 5 (권장), Claude Opus 5, Claude Haiku 4.5 | 유료 |
| **Grok** (xAI) | Grok 4.6 (권장), Grok 4.5, Grok 4.1 Fast | 유료 |
| **OpenAI 호환** | OpenAI 공식 API, OpenRouter, OpenCode GO 등 임의 호환 엔드포인트 | 엔드포인트 정책에 따름 |
| **클립보드 모드** | Gemini / ChatGPT / Claude / Grok 웹 | 무료 (API 키 불필요, 브라우저에서 수동 붙여넣기) |

> ⚠️ **모델 목록은 각 AI 공급자의 최신 상황에 따라 달라질 수 있습니다.** 사용 가능한 모델이 변경되었거나 오류가 발생하는 경우, 각 공급자의 공식 문서를 확인하세요.
>
> - [Gemini 모델](https://ai.google.dev/gemini-api/docs/models)
> - [OpenAI 모델](https://developers.openai.com/api/docs/models)
> - [Claude 모델](https://platform.claude.com/docs/en/about-claude/models/overview)
> - [Grok 모델](https://docs.x.ai/developers/models)

### 기타 기능

- LMS 강의 목록 자동 조회
- 처리 완료 후 원본 파일 보관/삭제 선택
- 처리 단계 선택 (다운로드만, STT만, 요약만 등)
- 사용자 설정 자동 저장 (학번, API 키 등)
- 디버그 모드

---

## ✅ 시작 전 필요한 것

| 항목                | 설명                                 | 비용 |
| ------------------- | ------------------------------------ | ---- |
| **숭실대 LMS 계정** | 학번 + 비밀번호                      | 무료 |
| **AI API 키**       | AI 요약에 사용 (Gemini 무료 발급 가능, 아래 참고) | 무료~유료 |
| **Google Chrome**   | 강의 콘텐츠 접근에 필요              | 무료 |

---

## 📥 설치 방법

### 방법 1: 프로그램 직접 다운로드 (추천 ⭐)

> 코딩을 모르는 일반 사용자라면 이 방법을 사용하세요.

1. [Releases 페이지](https://github.com/Leonamin/lms-summarizer/releases)에서 최신 버전을 찾습니다
2. 본인 운영체제에 맞는 파일을 다운로드합니다
   - **Mac**: `LMS-Summarizer-vX.X.X-mac.zip`
   - **Windows**: `LMS-Summarizer-vX.X.X-windows.zip`
3. 압축을 해제하고 실행합니다

> ⚠️ **Mac에서 "확인되지 않은 개발자" 경고가 뜨는 경우**
>
> 터미널을 열고 아래 명령어를 입력한 후 다시 실행하세요:
>
> ```
> xattr -rd com.apple.quarantine /path/to/LMS-Summarizer.app
> ```
>
> 또는: 시스템 설정 → 개인 정보 보호 및 보안 → "확인 없이 열기" 클릭

---

### 방법 2: 소스코드로 직접 실행 (개발자용)

<details>
<summary>펼쳐보기</summary>

#### 1. 필수 도구 설치

**uv** (Python 패키지 관리자):

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> ffmpeg는 별도 설치가 필요 없습니다. PyAV(`av` 패키지)가 MP4→WAV 변환을 자체 처리합니다.

#### 2. 저장소 복제 및 실행

```bash
git clone https://github.com/Leonamin/lms-summarizer.git
cd lms-summarizer
uv sync --extra desktop
uv run --extra desktop python src/gui/main.py
```

</details>

---

## 🔑 Gemini API 키 발급 방법 (무료)

AI 요약 기능을 사용하려면 Google Gemini API 키가 필요합니다. **무료**로 발급받을 수 있습니다.

### 발급 절차

**1단계 — Google AI Studio 접속**

[https://aistudio.google.com/](https://aistudio.google.com/) 에 접속합니다.
Google 계정으로 로그인하세요.

---

**2단계 — API 키 생성**

왼쪽 메뉴에서 **"Get API key"** 를 클릭합니다.

또는 아래 링크로 바로 이동:
[https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

---

**3단계 — 새 API 키 만들기**

"**Create API key**" 버튼을 클릭합니다.

프로젝트를 선택하라는 화면이 나오면 "**Create API key in new project**"를 선택해도 됩니다.

---

**4단계 — API 키 복사**

생성된 키(`AIzaSy...`로 시작하는 긴 문자열)를 복사합니다.

> 🔒 API 키는 비밀번호와 같습니다. 다른 사람과 공유하지 마세요.

---

**무료 사용 한도** (2025년 기준):

| 모델             | 무료 한도                    |
| ---------------- | ---------------------------- |
| Gemini 3.8 Flash | 분당 10회 요청, 하루 500회   |
| Gemini 2.0 Flash | 분당 15회 요청, 하루 1,500회 |

강의 요약 용도라면 무료 한도로 충분합니다.

---

## 🚀 사용 방법

### 1. 프로그램 실행

프로그램을 실행하면 아래와 같은 화면이 나타납니다.

```
┌──────────────────────────────────────────┐
│  🎓 LMS 강의 다운로드 & 요약   v0.1.0   │
├──────────────────────────────────────────┤
│  📁 저장 경로: ~/Documents/LMS-Summarizer│
├──────────────────────────────────────────┤
│  📚 학번: [          ]                   │
│  🔒 비밀번호: [       ] 👁               │
│  🔑 Gemini API 키: [              ]      │
│  🤖 AI 모델: [Gemini 3.8 Flash ▼]        │
│  🎬 강의 URL 목록:                       │
│  [                              ]        │
│                                          │
│  ☐ 처리 완료 후 원본 파일 보관           │
│                                          │
│  [▶ 처리 시작]  [초기화]                 │
└──────────────────────────────────────────┘
```

### 2. 정보 입력

| 항목              | 입력 내용                         |
| ----------------- | --------------------------------- |
| **학번**          | 숭실대 LMS 학번                   |
| **비밀번호**      | LMS 비밀번호 (영문 자판으로 입력) |
| **Gemini API 키** | 위에서 발급받은 API 키            |
| **AI 모델**       | Gemini 3.8 Flash 권장 (다른 엔진도 지원) |
| **강의 URL**      | LMS 강의 페이지 URL (아래 참고)   |

> 💡 **학번, 비밀번호, API 키는 자동으로 저장됩니다.** 다음 실행 시 다시 입력하지 않아도 됩니다.
> 비밀번호는 로컬 설정 파일(`settings.json`)에 저장되며 외부로 전송되지 않습니다.

### 3. 강의 URL 찾는 방법

1. LMS ([canvas.ssu.ac.kr](https://canvas.ssu.ac.kr)) 에 로그인합니다
2. 수강 중인 강의 → 모듈/강의자료 페이지로 이동합니다
3. 영상이 있는 강의 항목을 클릭합니다
4. 브라우저 주소창의 URL을 복사해서 입력란에 붙여넣습니다

여러 강의를 한 번에 처리하려면 URL을 **한 줄에 하나씩** 입력하세요:

```
https://canvas.ssu.ac.kr/courses/12345/modules/items/111111
https://canvas.ssu.ac.kr/courses/12345/modules/items/222222
```

### 4. 처리 시작

"**▶ 처리 시작**" 버튼을 클릭하면 자동으로 진행됩니다.

처리 단계:

- **1단계**: 강의 콘텐츠 처리 (인터넷 속도에 따라 수 분 소요)
- **2단계**: 음성 → 텍스트 변환 (영상 길이의 20~50% 소요)
- **3단계**: AI 요약 생성 (수십 초 소요)

### 5. 결과 확인

완료 후 요약 파일이 저장 경로에 생성됩니다:

- `강의명_summarized.txt` — AI 요약 내용

저장 경로는 기본값이 `~/Documents/LMS-Summarizer/` 이며, "경로 변경" 버튼으로 바꿀 수 있습니다.

---

## ❓ 자주 묻는 질문

### Q. 처음 실행할 때 오래 걸려요

첫 실행 시 faster-whisper AI 모델(기본 모드 기준 약 800MB)을 다운로드합니다. 한 번만 다운로드되며 이후에는 빠릅니다.

### Q. 비밀번호가 입력이 안 돼요

비밀번호 입력란은 **영문 자판**에서만 입력됩니다. 한글 자판으로 되어 있다면 영문으로 전환 후 입력하세요.

### Q. 강의 콘텐츠를 찾을 수 없다고 나와요

- URL이 올바른지 확인하세요 (영상이 있는 강의 항목의 URL이어야 합니다)
- 해당 강의가 현재 수강 중인지 확인하세요
- Chrome이 설치되어 있는지 확인하세요

### Q. API 키 오류가 나요

- Gemini API 키가 올바르게 입력됐는지 확인하세요 (`AIzaSy`로 시작)
- [Google AI Studio](https://aistudio.google.com/app/apikey)에서 키가 활성화 상태인지 확인하세요

### Q. Mac에서 "개발자를 확인할 수 없음" 오류가 나요

터미널에서 아래 명령어를 실행하세요:

```bash
xattr -rd com.apple.quarantine ~/Downloads/LMS-Summarizer.app
```

### Q. 요약 결과가 마음에 안 들어요

- **Gemini 3.1 Pro** 등 상위 모델을 선택하면 더 상세한 요약이 가능합니다
- OpenAI, Claude, Grok 등 다른 AI 엔진도 지원합니다 (유료 API 키 필요)
- 강의 음질이 좋지 않으면 텍스트 변환 정확도가 낮아질 수 있습니다

---

## 🛠️ 개발자 정보

<details>
<summary>개발 환경 및 기술 스택</summary>

### 기술 스택

| 영역            | 기술                                       |
| --------------- | ------------------------------------------ |
| GUI             | Flet 0.81.0                                |
| 콘텐츠 처리     | Playwright (headless=False, 시스템 Chrome) |
| 음성 변환 (STT) | faster-whisper (CTranslate2, 로컬 실행)    |
| 미디어 변환     | PyAV (ffmpeg 불필요)                       |
| AI 요약         | Gemini / OpenAI / Claude / Grok API        |
| 패키지 관리     | uv                                         |
| Python          | >=3.11, <3.13                              |

### 프로젝트 구조

```
src/
├── gui/                    # Flet GUI 애플리케이션
│   ├── main.py             # 엔트리포인트
│   ├── config/             # 상수, 스타일, 설정
│   ├── core/               # 파일 관리, 모듈 로더
│   ├── components/         # UI 컴포넌트
│   ├── views/              # 화면 (메인, 설정, 강의 목록, 진행 상태)
│   └── workers/            # 백그라운드 처리 스레드
├── video_pipeline/         # 콘텐츠 다운로드 파이프라인
├── audio_pipeline/         # 음성 → 텍스트 파이프라인
└── summarize_pipeline/     # AI 요약 파이프라인
    └── providers/          # AI 엔진별 구현 (Gemini, OpenAI, Claude, Grok, OpenAI 호환, 클립보드)
```

### 빌드

GitHub Actions(`release.yml`)가 `v*` 태그 push 시 macOS/Windows 빌드를 자동 생성합니다.

로컬에서 직접 빌드하려면:

```bash
uv run --extra desktop pyinstaller lms-summarizer.spec
```

### 커밋 메시지 규칙

```
feat: 새 기능  |  fix: 버그 수정  |  refactor: 리팩토링
docs: 문서      |  style: 스타일   |  test: 테스트
```

</details>

---

## ⚠️ 주의사항

- 본 도구는 **개인 학습 목적**으로만 사용하세요
- 처리된 콘텐츠의 **외부 공유 및 배포는 금지**됩니다
- 숭실대학교 LMS **이용약관을 준수**하여 사용하세요
- 본 프로그램은 LMS 서비스에 어떠한 변조나 침해도 가하지 않습니다
- 문제 발생 시 즉시 사용을 중단하세요

---

## 📄 라이선스

이 프로젝트는 [MIT License](LICENSE)에 따라 배포됩니다.

본 프로젝트는 개인 학습 보조 목적으로 제작되었습니다. LMS 서비스 약관을 준수하여 사용하시기 바랍니다.

### 공통 코어와 실행 환경

공통 모델·프롬프트·검증·저장 경계는 `src/core`, 설치형 호환 입력·저장·OS 동작은
`src/desktop`, 웹 전송 경계는 `src/web`에 있습니다. 기존 GUI import 경로는 호환용으로 유지합니다.

- 설치형: `uv sync --extra desktop`, `uv run --extra desktop lms-summarizer`
- Windows CUDA 설치형: `uv sync --extra desktop --extra cuda`
- 코어 진단: `uv run lms-summarizer-core`
- 웹 의존성: `uv sync --extra web` (웹 서버/API는 후속 단계에서 구현)
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

성공 후 `keep_source` 설정을 적용하고 중간 오디오를 정리합니다. 실패·취소·중단의 관리 입력과
다른 작업이 참조하는 입력은 보존합니다. 원문·요약·수동 프롬프트·이력은 자동 삭제하지 않습니다.
사용하지 않은 관리 입력은 기본 24시간, 이벤트·로그는 7일·10만 행 한도로 정리합니다.

검증: `uv run --extra desktop --extra web python -m unittest discover -s tests -v`.
실제 LMS·유료 공급자·로컬 Whisper 추론과 OS별 실행 검증은 후속 단계에서 별도로 진행합니다.


## Docker 웹 작업실 (5단계)

설치형과 별도 데이터로 실행하는 개인용 웹 화면입니다. 현재 파일 업로드, 단계별 처리, 개별·전체 취소,
재시도, 시도 이력, STT 원문·요약·프롬프트 열람/다운로드를 지원합니다. 화면을 닫거나 새로고침해도
작업은 서버에서 계속됩니다. LMS 목록/URL 입력 화면, 모든 공급자의 상세 설정 화면과 운영 점검은
6–7단계에서 확장합니다. 설치형 macOS/Windows 검증은 별도 잔여 항목입니다.

```bash
docker compose up -d --build
```

브라우저에서 `http://127.0.0.1:8000`을 엽니다. 초기 요약 방식은 API 키가 필요 없는 챗봇 프롬프트 준비입니다.
`처리 설정`에서 요약 API 방식·모델·키를 저장하면 자동 요약을 사용할 수 있습니다.
MP4/TS는 오디오 변환부터, WAV/MP3는 음성 인식부터, UTF-8 TXT는 요약부터 처리합니다.
TXT만 선택한 작업에서 마지막 단계를 음성 인식/변환으로 지정하면 입력 오류로 표시됩니다.
로컬 음성 인식은 CPU faster-whisper이며 첫 실행 때 모델을 다운로드해 `/models`에 보관합니다.

LAN 접속은 허용할 서버 주소를 명시해서 실행합니다. 로그인 없는 개인 모드이며 외부 공개용이 아닙니다.

```bash
LMS_BIND_ADDRESS=0.0.0.0 LMS_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.0.10 docker compose up -d
```

포트는 `LMS_WEB_PORT`로 변경할 수 있습니다. 동일 origin만 허용하며 별도 프런트엔드 origin이 필요하면
`LMS_ALLOWED_ORIGINS`에 명시합니다. 무제한 CORS는 사용하지 않습니다.

- `web-data:/data`: SQLite 작업·시도·산출물, 업로드 상태, 웹 설정·비밀 버전. 설치형 설정을 자동으로 가져오지 않습니다.
- `web-models:/models`: 음성 인식 모델 캐시.
- 서버는 한 프로세스와 네 단계 워커를 소유합니다. Uvicorn workers/서비스 replica를 늘리지 않습니다.
- 파일 4 GiB, TXT 16 MiB, 한 번에 50개, 활성 작업 200개가 기본 한도입니다. 열람은 2 MiB까지이며 큰 텍스트는 다운로드합니다.
- 미사용 업로드는 24시간 후 정리합니다. 실패·취소·중단 입력은 재시도용으로 남기고 원문·요약·프롬프트는 자동 삭제하지 않습니다.
- LAN HTTP에서 자동 복사가 불가능하면 원문을 전체 선택하므로 기기의 복사 기능을 사용할 수 있습니다.

```bash
docker compose logs -f web
docker compose down                 # 데이터·모델 볼륨 유지
docker compose up -d --build         # 컨테이너 교체 후 기존 작업·결과 복원
```

실행 중 작업은 서버 종료/재시작 후 `중단`으로 기록하고, 대기 작업은 자동 재개합니다. 중단 작업은
사용자가 재시도하며 원래 설정·비밀 버전을 유지합니다. `down -v`는 데이터·모델 볼륨을 삭제하므로
일반 중지에 사용하지 않습니다.

로컬 개발:

```bash
uv sync --extra web
npm ci --prefix frontend
npm run build --prefix frontend
uv run --extra web python -m src.web
```

프런트엔드 개발 서버는 `npm run dev --prefix frontend`이며 `/api`를 localhost:8000으로 전달합니다.
개발 서버 접속에 사용할 origin은 백엔드 `LMS_ALLOWED_ORIGINS`에 명시합니다.
기본 데이터는 `.local/web-data`, 모델은 `.local/web-models`이며 환경 변수 `LMS_DATA_DIR`,
`LMS_MODELS_DIR`, `LMS_STATIC_DIR`, `LMS_PORT`로 변경할 수 있습니다.
