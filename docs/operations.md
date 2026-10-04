# 운영 가이드

[문서 목록](../README.md#문서)

인증 없는 개인용 단일 서버 운영을 기준으로 한다. 운영 기본 포트는 **8200**이며, 개발용 3000·8000은
`python -m src.web`과 Vite 프런트엔드에만 사용한다. 설정 값은 저장소 루트의 `.env`(gitignore)에 두고
`.env.example`을 복사해 쓴다. `docker compose`의 project 이름은 저장소 디렉토리 이름을 따르며 아래
볼륨 이름은 기본값 `lms-summarizer_web-data`, `lms-summarizer_web-models`다.

### 설치·시작

```bash
cp .env.example .env      # 주소·포트·허용 Host 조정
docker compose up -d --build
docker compose ps         # STATUS가 healthy인지 확인
```

최초 실행 때 음성 인식 모델(기본 `large-v3-turbo`, 약 800MB)을 `/models`에 내려받으므로
첫 로컬 음성 인식 작업은 다운로드 시간만큼 오래 걸린다. 시험 삼아 브라우저에서
`http://127.0.0.1:8200`을 연다.

### 중지·재시작

```bash
docker compose stop web            # 잠시 멈춤(볼륨 유지)
docker compose restart web         # 재시작
docker compose down                # 컨테이너·네트워크 제거, 볼륨 유지
```

`down -v`는 데이터·모델 볼륨을 삭제하므로 일반 중지에 쓰지 않는다. 재시작 시 실행 중 시도는
`중단(interrupted)`으로 기록하고 대기 작업은 자동 복원한다. 중단 작업은 화면에서 재시도한다.

### 업데이트

```bash
docker compose up -d --build       # 새 이미지로 교체, 데이터·모델 볼륨 유지
```

업데이트 전 데이터·모델 볼륨을 백업한다. 앱은 이미지를 자동 교체하지 않으며 서버 진단의
`업데이트 확인`은 릴리즈 정보만 알려 준다.

### 백업·복원

일관된 SQLite 사본을 위해 백업 전 잠시 컨테이너를 멈춘다.

```bash
docker compose stop web
mkdir -p backup
docker run --rm -v lms-summarizer_web-data:/data:ro -v "$PWD/backup":/backup alpine sh -c 'tar czf /backup/web-data.tar.gz -C /data .'
docker run --rm -v lms-summarizer_web-models:/models:ro -v "$PWD/backup":/backup alpine sh -c 'tar cf /backup/web-models.tar -C /models .'
docker compose start web
```

모델은 다시 내려받을 수 있으므로 필요할 때만 백업한다. 복원은 볼륨을 새로 만든 뒤 푼다.

```bash
docker compose down
docker volume rm lms-summarizer_web-data lms-summarizer_web-models
docker volume create lms-summarizer_web-data
docker volume create lms-summarizer_web-models
docker run --rm -v lms-summarizer_web-data:/data -v "$PWD/backup":/backup:ro alpine sh -c 'cd /data && tar xzf /backup/web-data.tar.gz'
docker run --rm -v lms-summarizer_web-models:/models -v "$PWD/backup":/backup:ro alpine sh -c 'cd /models && tar xf /backup/web-models.tar'
docker compose up -d
```

복원 후 작업 목록·설정·원문/요약이 그대로 조회되는지 확인한다.

### GPU·CPU

이미지 기본 실행은 CPU faster-whisper다. `faster-whisper` GPU 가속은 CUDA 기반이라
NVIDIA GPU가 필요하다. AMD 내장 GPU(예: Radeon 780M)는 CUDA를 지원하지 않아 CPU로 동작하며,
AMD ROCm 가속은 지원 대상이 아니다. GPU를 쓰려면 NVIDIA 장치 전달과 CUDA extra 구성이 필요하고,
그 전까지는 CPU 추론으로 운영한다.

### 문제 해결

- 화면이 안 열림/포트 충돌: `.env`의 `LMS_WEB_PORT`를 다른 값(예: 8200)으로 바꾸고 재기동한다.
- LAN·Tailscale 접속이 400: 접속 주소를 `LMS_ALLOWED_HOSTS`에 추가한다(포트 제외, 쉼표 구분).
  예 `LMS_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.0.104,100.105.226.124`.
- Headless에서 페이지 확인이 필요: `LMS_CHROME_HEADLESS=false`로 재기동한다(이미지에 Xvfb 포함).
- 모델 다운로드 실패: 네트워크를 확인하고 재시도한다. `web-models` 볼륨을 지우면 다시 받는다.
- 디스크 부족으로 제출 거부: `LMS_MIN_FREE_BYTES`(기본 2GiB)와 볼륨 사용량을 확인한다.
- 중복 supervisor 오류: 데이터 볼륨을 하나의 컨테이너에만 마운트한다(단일 서버 전제).
- 인증이 없으므로 공유 네트워크 밖(공개 인터넷)에 직접 노출하지 않는다.
