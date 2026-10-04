# LMS 강의 AI 요약기

숭실대학교 LMS 강의를 다운로드하고, 음성을 텍스트로 변환한 뒤 AI로 요약하는 개인 학습 도구입니다.
Flet 데스크톱 앱과 Docker 웹 작업실이 공통 Python 코어를 사용합니다.

## 빠른 시작

데스크톱 배포 파일은 [Releases](https://github.com/Leonamin/lms-summarizer/releases)에서 받습니다.
소스에서 실행하려면 Python 3.11–3.12와 uv를 설치한 뒤 저장소 루트에서 실행합니다.

```bash
uv sync --extra desktop
uv run --extra desktop lms-summarizer
```

웹 작업실은 Docker로 실행합니다.

```bash
cp .env.example .env
docker compose up -d --build
```

브라우저에서 `http://127.0.0.1:8200`을 엽니다. LMS 접근에는 시스템 Google Chrome이 필요하며,
웹 컨테이너에는 포함되어 있습니다. 웹은 인증 없는 개인용 서버이므로 공개 인터넷에 직접 노출하지 않습니다.

## 문서

- [데스크톱 사용 가이드](docs/desktop.md): 설치, 지원 엔진, API 키, 사용 방법, FAQ
- [웹 작업실 가이드](docs/web.md): 처리 설정, Chrome, LAN 접속, 작업·데이터 경로
- [개발 가이드](docs/development.md): 프로젝트 구조, 실행, 테스트, 패키징, 공통 작업 서비스
- [운영 가이드](docs/operations.md): 업데이트, 백업·복원, 장애 대응
- [디자인 규칙](DESIGN.md): 화면과 공용 스타일
- [프로젝트 위키](wiki/index.md): 설계 결정, 계획, 변경 이력

## 폴더 안내

| 경로 | 용도 |
| --- | --- |
| `src/` | Python 코어, 데스크톱·웹 어댑터, 처리 파이프라인 |
| `frontend/` | React 웹 화면 |
| `tests/` | Python 자동 검증 |
| `scripts/` | OS별 빌드, 릴리즈, LMS 브라우저 진단 |
| `packaging/` | PyInstaller 데스크톱 패키징 설정 |
| `assets/` | 앱 아이콘 |
| `examples/` | 자격 증명을 포함하지 않는 설정 예제 |
| `docs/` | 현재 사용·개발·운영 방법 |
| `wiki/` | 의사결정과 작업 이력 |

Docker 실행 설정과 패키지 매니저 설정은 저장소 루트에 둡니다.
로컬 의존성(`.venv/`, `frontend/node_modules/`), 빌드 결과(`build/`, `dist/`, `frontend/dist/`),
운영 데이터(`.local/web-data/`, `.local/web-models/`, `backup/`)는 소스와 구분하며 Git에 커밋하지 않습니다.

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
