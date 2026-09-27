---
type: Log
title: "7단계 대상 환경 운영 검증·배포 마무리"
description: "Ubuntu 26.04 대상 호스트의 실제 LMS 전체 처리·CPU 추론·취소·복구·백업/복원·LAN/Tailscale·운영 문서"
timestamp: 2026-09-27
okf_version: "0.1"
---

# 7단계 대상 환경 운영 검증·배포 마무리

## 결과와 범위

**7단계 완료.** 대상 호스트(Ubuntu 26.04, Docker 29.6.2, Compose v5.3.1, Ryzen 7 8745HS,
26GiB RAM, 466GB 디스크)에서 실제 LMS 강의 한 편을 **다운로드→오디오 변환→로컬 CPU Whisper
추론→Gemini 요약**까지 처리하고, 취소·재시작 복구·백업/복원·업데이트·LAN/Tailscale 접속과
운영 문서를 확인했다. 4단계에서 보류한 macOS/Windows 설치형 빌드·네이티브 OS 검증은 그대로
잔여 항목이다. Gemini 외 유료 공급자의 실제 키 호출은 하지 않았고 어댑터 경계 검증과 구분한다.

## 운영 구성

- 운영 기본 포트를 **8200**으로 하고 개발 기본값 8000(`python -m src.web`, Vite 프록시)과 분리했다.
  Compose 호스트·컨테이너 포트와 이미지 `EXPOSE`·`HEALTHCHECK`를 8200으로 맞췄다.
- `.env`(gitignore)에 `LMS_BIND_ADDRESS`, `LMS_WEB_PORT`, `LMS_ALLOWED_HOSTS`를 두고
  `.env.example`을 함께 제공한다. 기본은 로컬(127.0.0.1)이고 LAN/Tailscale 노출은 명시한다.
- Compose project `lms-summarizer`, 데이터 `lms-summarizer_web-data`, 모델 `lms-summarizer_web-models`.
- GPU: 이미지 기본은 CPU faster-whisper다. 대상 호스트는 AMD Radeon 780M 내장 GPU로
  faster-whisper의 CUDA 가속을 쓸 수 없어 **CPU 기준**으로 검증·문서화했다. AMD ROCm은 지원 대상이 아니다.

## 검증 기록

- **기동·진단:** `docker compose up -d --build` 후 healthy. `/api/v1/system`에서 버전 1.9.3,
  SQLite 3.53.1, Chrome 154.0.8037.57, CPU STT, 여유 디스크 292GB를 확인했다. 컨테이너는
  UID 10001, Flet 미탑재, 정적 SPA 서빙 200, 카탈로그에 5개 요약 엔진·4개 STT 엔진이 노출됐다.
- **실제 로컬 CPU 추론:** 합성 한국어 음성을 업로드해 기본 `large-v3-turbo` 모델을 `/models`에
  내려받고(캐시 1.6GB) STT를 완료했다. 최초 실행은 다운로드 포함 152초, 캐시 후 약 15초 음성은
  추론 약 6초였다.
- **실제 LMS 전체 처리:** 저장한 학번·비밀번호로 **과목 11개**를 자동 조회하고(URL 입력이 아니라
  `과목·주차` 자동 감지 경로), 15주차 강의 목록에서 가장 짧은 **9분 6초 영상 1편**을 선택해
  end_stage 4로 제출했다. 시도 1에서 다운로드 54.8MB(20.9초)→오디오 변환 17.5MB(0.5초)→
  로컬 STT 5,935B 원문(124.3초)→요약 단계가 Gemini **503 high demand**로 실패했다.
  실패 원인은 저장된 비밀 버전과 고정 설정으로 provider 호출을 재현해 확인했고, 코드 결함이 아니라
  공급자 일시 과부하였다. `재시도`로 시도 2를 만들어 다운로드·변환·STT를 다시 거쳐
  **Gemini 요약 4,957B**를 완료했다. 요약 마크다운은 강의 주제(행렬·특정 행렬)와 핵심 내용을 담았다.
  원문·요약 화면 열람과 다운로드 바이트 일치를 확인했다.
- **취소:** 9분 42초 합성 음성 STT 실행 중 취소를 요청해 `cancelling`→`cancelled`를 6초 안에
  확인했고, 네 단계 대기·실행 수가 모두 0으로 돌아왔으며 상주 워커 외 잔여 추론 프로세스가 없었다.
- **재시작 복구:** 실행 중 `docker compose restart web`으로 재기동해 실행 시도가 `interrupted`+
  재시도 가능으로 기록되고, 재시도로 완료되는 것을 확인했다. 시도 기록 2개가 보존됐다.
- **재시도 정책:** 계약대로 사용자 재시도는 완료 단계를 자동 재사용하지 않고 원래 입력 단계부터
  다시 실행한다(다운로드·STT 재수행). 일시적 공급자 오류의 운영 비용으로 기록한다.
- **백업/복원:** 컨테이너를 잠시 멈추고 `web-data`(35MB gzip)·`web-models`(1.6GB tar) 볼륨을
  백업한 뒤 새 볼륨에 풀어 별도 project로 기동했다. 작업 6개·설정·원문/요약 아티팩트가 복원됐고
  리허설 볼륨을 정리했다.
- **업데이트:** Dockerfile·Compose 변경(8200 포트) 후 `up -d --build`로 이미지를 교체·재생성했고
  데이터·모델·작업이 유지됐다. 기존 8000 매핑은 사라지고 8200만 수신하는 것을 확인했다.
- **LAN·Tailscale:** `0.0.0.0:8200` 바인딩에서 LAN(192.168.0.104)과 Tailscale(100.105.226.124)
  모두 200, 목록에 없는 Host는 400으로 거부됐다. **실제 휴대폰에서 Tailscale 주소 접속 성공**을
  확인했다.
- **문서:** README에 설치·시작·중지·업데이트·백업·복원·GPU·문제 해결 운영 가이드를 추가하고
  `.env.example`을 제공했다.

## 미검증·제한

- Gemini 외 OpenAI/Claude/Grok/ReturnZero 실제 키 호출은 하지 않았다(어댑터 대체 검증만).
- 실제 동일 Wi-Fi LAN의 별도 PC/휴대폰 브라우저는 확인하지 않았고, 휴대폰은 Tailscale로 확인했다.
- 여러 시간 연속 상주 운영과 디스크 고갈·네트워크 단절 장기 시나리오는 단일 강의 전체 처리와
  취소·복구 검증으로 대체했다.
- macOS/Windows 설치형 빌드·네이티브 OS 동작은 4단계 보류 항목으로 남긴다.
- 검증 컨테이너·합성 음성·캡처는 `/tmp/lms-stage7` 등 저장소 밖에 두며 Git에 포함하지 않는다.
  실제 계정·비밀번호·강의 제목·URL은 출력물·위키에 기록하지 않았다.

[상세 계획](../plans/core-web-dashboard-plan.md) · [진행 TODO](../plans/core-web-dashboard-todo.md)
