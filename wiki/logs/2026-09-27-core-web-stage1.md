---
type: Log
title: "코어·웹 1단계 착수: 기능과 기술 계약"
description: "활성 기능 조사, API·작업 실행 설계, Docker Chrome 합성 영상·CDP 검증"
timestamp: 2026-09-27
okf_version: "0.1"
---

# 코어·웹 1단계 착수

- 추가: [1단계 기능·구현 계약](2026-09-27-core-web-stage1-contract.md).
- 추가: [ADR-003](../decisions/003-web-runtime-and-job-contract.md).
- 추가: `scripts/browser_probe/` 검증용 Dockerfile·합성 영상/CDP 도구·실행 안내.
- 갱신: 전체 상세 계획과 TODO의 1단계 상태, 관련 인덱스와 루트 탐색 설명.

## 조사 결과

현재 Flet 활성 경로와 구형 경로를 구분했다. ReturnZero 자격 증명 연결, 업로드 원본 삭제, 프롬프트 우선순위, headless 문서·코드 차이를 후속 구현 항목으로 기록했다.

호스트 Ubuntu 26.04·amd64, Docker 29.6.2·Compose v5.3.1과 daemon 접근을 확인했다. GPU는 AMD 내장 그래픽이며 NVIDIA는 확인되지 않았다. 알려진 기본 설정 경로에 LMS 계정이 없었다. 기존 서비스와 호스트 브라우저 설치는 변경하지 않았다.

실제 LMS 로그인·영상 추출은 계정 설정 경로와 강의 URL이 없어 미완료다. 기술 계약 작성과 환경 probe는 실제 LMS 완료와 구분한다.

## 실행 검증 결과

Google Chrome 154.0.8037.57 + Playwright 1.56.0 조사 이미지 빌드 성공. 네트워크를 끈 임시 컨테이너에서 H.264/AAC fixture를 재생하고 CDP MP4 URL 포착을 확인했다. headless 및 Xvfb headed 모두 readyState=4, currentTime>0, 포착=true로 성공했다. 실제 LMS는 미검증이며 1단계는 부분 완료로 기록했다.

## 실제 LMS 검증 완료

사용자가 로컬 검증 설정을 작성한 뒤 기존 로그인과 CDP 추출 경로로 확인했다. Docker Google Chrome headless에서 login=true, cdp_mp4_captured=true, captured_count=3, title_found=true, success=true로 종료했다. 비밀·강의·영상 주소 원문은 출력하지 않았다.

1단계를 완료 체크했다. 완료된 1단계 계약 문서는 logs로 보존했고 관련 링크를 갱신했다. 전체 영상 다운로드·STT·요약은 후속 검증 항목이다.
