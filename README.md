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
| **whisper.cpp** | 로컬 실행 | 무료 | 기본 엔진, API 키 불필요 |
| **ReturnZero** | 클라우드 API | 유료 | 높은 정확도 |

### AI 요약 엔진

| 엔진 | 지원 모델 | 비용 |
| --- | --- | --- |
| **Gemini** (Google) | 2.5 Flash (권장), 2.5 Pro, 2.5 Flash Lite, 2.0 Flash | 무료 티어 제공 |
| **OpenAI** | GPT-4o (권장), GPT-4o Mini, o3-mini | 유료 |
| **Claude** (Anthropic) | Claude Sonnet 4 (권장), Claude Haiku 4.5 | 유료 |
| **Grok** (xAI) | Grok 3 (권장), Grok 3 Mini | 유료 |
| **클립보드 모드** | ChatGPT / Claude / Grok 웹 | 무료 (API 키 불필요, 브라우저에서 수동 붙여넣기) |

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
uv sync
uv run python src/gui/main.py
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
| Gemini 2.5 Flash | 분당 10회 요청, 하루 500회   |
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
│  🤖 AI 모델: [Gemini 2.5 Flash ▼]        │
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
| **AI 모델**       | Gemini 2.5 Flash 권장 (다른 엔진도 지원) |
| **강의 URL**      | LMS 강의 페이지 URL (아래 참고)   |

> 💡 **학번과 API 키는 자동으로 저장됩니다.** 다음 실행 시 다시 입력하지 않아도 됩니다.
> 비밀번호는 보안상 저장되지 않습니다.

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

첫 실행 시 Whisper AI 모델(약 142MB)을 다운로드합니다. 한 번만 다운로드되며 이후에는 빠릅니다.

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

- **Gemini 2.5 Pro** 등 상위 모델을 선택하면 더 상세한 요약이 가능합니다
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
| 음성 변환 (STT) | whisper.cpp (pywhispercpp, 로컬 실행)      |
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
    └── providers/          # AI 엔진별 구현 (Gemini, OpenAI, Claude, Grok, 클립보드)
```

### 빌드

GitHub Actions(`release.yml`)가 `v*` 태그 push 시 macOS/Windows 빌드를 자동 생성합니다.

로컬에서 직접 빌드하려면:

```bash
uv run pyinstaller lms-summarizer.spec
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

본 프로젝트는 개인 학습 보조 목적으로 제작되었습니다. LMS 서비스 약관을 준수하여 사용하시기 바랍니다.
