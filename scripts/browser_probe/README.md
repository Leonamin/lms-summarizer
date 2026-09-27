# Chrome/CDP 환경 확인

1단계 검증용 임시 이미지다. 제품 배포 이미지와 구분한다. 호스트 Chrome을 설치하거나 기존 컨테이너를 변경하지 않는다.

```sh
docker build -t lms-browser-probe:stage1 scripts/browser_probe
docker run --rm --init --shm-size=1g --network none lms-browser-probe:stage1
docker run --rm --init --shm-size=1g --network none --entrypoint xvfb-run lms-browser-probe:stage1 -a python /probe/probe.py --headed
```

로컬 H.264/AAC MP4를 생성하고 Google Chrome 재생 및 CDP `Network.requestWillBeSent`의 MP4 URL 포착을 확인한다. 외부 LMS 접속·로그인·실제 강의 코덱·프로젝트의 중첩 프레임 추출 성공을 증명하지 않는다. Google Chrome은 빌드 시 stable을 내려받고 Playwright는 이 조사 이미지에서 1.56.0으로 고정한다. 배포 버전은 실제 LMS 검증 후 별도 고정한다.

2026-09-27 실행 결과: Chrome 154.0.8037.57, Playwright 1.56.0에서 headless와 Xvfb headed 모두 합성 영상 재생·CDP 포착 성공. 실제 LMS 검증 결과는 아래에 별도로 기록했다.

## 실제 LMS 검증

프로젝트 루트에서 실행한다. `.local/lms-probe/settings.json`에 student_id/password/lecture_url을 작성한다. 비밀 값은 CLI 인자나 이미지에 넣지 않는다. 기본 컨테이너 사용자는 UID 1000이며 설정 파일을 읽을 권한이 필요하다.

```sh
docker run --rm --init --shm-size=1g \
  --mount "type=bind,src=$PWD/src,dst=/workspace/src,readonly" \
  --mount "type=bind,src=$PWD/scripts/browser_probe/lms_probe.py,dst=/probe/lms_probe.py,readonly" \
  --mount "type=bind,src=$PWD/.local/lms-probe/settings.json,dst=/run/lms-settings.json,readonly" \
  --env PYTHONPATH=/workspace --entrypoint python \
  lms-browser-probe:stage1 /probe/lms_probe.py
```

기존 로그인과 strict CDP 경로로 추출하며 DOM fallback과 영상 전체 다운로드는 수행하지 않는다. 로그인·추출 결과의 불리언과 요청 수만 출력한다. 오류 메시지에 URL/토큰이 포함될 수 있어 예외 종류만 출력한다. 실제 강의 재생이 시작될 수 있으므로 로그인·강의 접근 기록 및 시청 상태가 LMS에 기록될 수 있다.

2026-09-27 실제 강의 한 개: headless에서 로그인·CDP 추출 성공, MP4 요청 3개·제목 확보. 전체 다운로드·STT·요약과 모든 강의 유형은 미검증.
