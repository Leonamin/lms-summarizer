# LMS 요약

숭실대학교 LMS 강의 동영상을 다운로드하고 AI로 요약하는 도구입니다.

## 환경설정

### 1. uv 설치

[uv](https://docs.astral.sh/uv/getting-started/installation/)를 설치합니다.

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 의존성 설치

프로젝트 루트에서 아래 명령어를 실행하면 Python 설치, 가상환경 생성, 패키지 설치가 한번에 처리됩니다.

```bash
uv sync
```

새 패키지를 추가할 때:

```bash
uv add <패키지명>
```

### 3. Playwright 브라우저 설치

```bash
uv run playwright install
```

### 4. ffmpeg 설치

동영상 파일을 wav로 변환하기 위해 ffmpeg이 필요합니다.

```bash
# macOS
brew install ffmpeg

# Windows
# https://ffmpeg.org/download.html 에서 다운로드
```

### 5. .env 설정

프로젝트 루트에 `.env` 파일을 생성합니다.

```
USERID=학번
PASSWORD=비밀번호
GOOGLE_API_KEY=구글_제미나이_API_키
```

선택 사항:

```
RETURNZERO_CLIENT_ID=리턴제로_클라이언트_ID
RETURNZERO_CLIENT_SECRET=리턴제로_클라이언트_시크릿
OPENAI_API_KEY=OpenAI_API_키
```

- **Gemini API 키**: 요약 기능에 사용 (기본 엔진)
- **ReturnZero API 키**: STT 대안 엔진. 미설정 시 Whisper(로컬) 사용. [API 키 발급](https://developers.rtzr.ai/) (월 600분 무료)
- **OpenAI API 키**: 요약 대안 엔진

### 6. user_settings.json 설정 (선택)

GUI를 사용하지 않고 CLI로 실행할 때 URL 목록을 미리 지정할 수 있습니다.

```json
{
  "video": [
    "https://canvas.ssu.ac.kr/courses/xxxxx/modules/items/xxxxxxx?return_url=..."
  ]
}
```

## 실행

```bash
# GUI 실행
uv run python src/gui/main.py
```

## 빌드 (macOS)

```bash
./build_mac_pyinstaller.sh
```

## 에러 발생 시

### ModuleNotFoundError

단위 테스트 파일 실행 시 `ModuleNotFoundError: No module named 'audio_pipeline'` 같은 에러가 발생하면:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

## 커밋 메시지 규칙

| 타입 | 설명 | 예시 |
|------|------|------|
| `feat` | 새로운 기능 추가 | `feat: 사용자 로그인 기능 추가` |
| `fix` | 버그 수정 | `fix: 로그인 페이지 오류 수정` |
| `docs` | 문서 수정 | `docs: README.md 업데이트` |
| `style` | 코드 스타일 수정 | `style: 들여쓰기 통일` |
| `refactor` | 코드 리팩토링 | `refactor: 로그인 기능 리팩토링` |
| `test` | 테스트 코드 추가 | `test: 로그인 기능 테스트 추가` |
| `chore` | 보조 도구/설정 변경 | `chore: 의존성 업데이트` |
| `build` | 빌드 시스템/외부 의존성 변경 | `build: uv로 패키지 매니저 전환` |
| `ci` | CI/CD 설정 변경 | `ci: Github Actions 설정 수정` |
| `perf` | 성능 개선 | `perf: 다운로드 속도 개선` |
| `release` | 릴리즈 | `release: v1.0.0` (버전 태깅 포함) |
