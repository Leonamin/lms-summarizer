---
type: Log
title: "8-B 자동 재생 팝업 DOM 조사"
description: "실제 LMS에서 재생 시작·인트로·이어보기/재생 중 팝업의 DOM 선택자와 구분 방법을 확인"
timestamp: 2026-09-28
okf_version: "0.1"
---

# 8-B 자동 재생 팝업 DOM 조사

## 목적과 방법

[신규 강의 감지·자동 재생·자동 저장](../plans/auto-play-new-lectures.md)의 남은 조사 중
"이어보기/재생 중 팝업의 실제 DOM 선택자와 HTML 파싱 가능 여부"를 실제 LMS로 확인했다.
Docker 이미지의 시스템 Chrome을 **headed + Xvfb**로 띄우고 기존 로그인 흐름
(`video_pipeline/login.py`)을 재사용해 실제 계정으로 강의 페이지를 열고 재생·이탈·재진입,
그리고 두 강의 동시 재생을 실행했다. 관찰은 프레임 DOM 평가로 수행했다.

## 프레임 구조

- 강의 항목 페이지 → `iframe#tool_content` = `.../learningx/lti/lecture_attendance/items/view/{id}`.
- 그 안의 내부 iframe = `https://commons.ssu.ac.kr/em/{content_id}?...` (실제 플레이어).
- 플레이어 내부 iframe URL의 `TargetUrl`이 진도 보고 엔드포인트다:
  `.../learningx/api/v1/courses/{course}/sections/0/components/{component}/progress?...&content_type=movie`.
  즉 재생 시간이 이 API로 진도로 보고된다(자동 재생이 출석을 만족하는 근거).

## 재생 시작

- 정지 화면의 재생 버튼: `.vc-front-screen-play-btn` (내부 commons 프레임에서 보임).
  Playwright `evaluate`로 `click()`하면 재생이 시작된다(액션 가능성 검사가 있는 `locator.click()`보다 안정적).
- 클릭 직후 **인트로 영상**(`settings/viewer/uniplayer/intro.mp4`, 약 5초)이 재생되고,
  이후 실제 미디어로 전환된다.
  - `movie` 유형: `video.vc-vplay-video1`의 src가 실제 mp4로 교체되고 시간이 증가한다(확인).
  - `readystream` 유형: 슬라이드 + `audio.vc-sdaudio-audio`. 인트로 후 팝업이 뜨면 재생이 멈춘다.
- 시간 표시: `.vc-pctrl-play-time-text-area` (예: `00:08 / 09:06`). 일시정지 버튼 상태 클래스
  `vc-pctrl-on-pause` / `vc-pctrl-on-playing`으로 재생 여부를 판별할 수 있다.

## 팝업 (핵심 결과)

이어보기와 "재생 중" 팝업은 **같은 DOM 요소**를 쓰고 `.confirm-msg-text` 내용으로 구분된다.

- 컨테이너: `.confirm-dialog-wrapper` 안의 `.confirm-msg-box`.
- 텍스트: `.confirm-msg-text` (초기/비표시 시 빈 문자열).
- 버튼: `.confirm-ok-btn`(긍정) / `.confirm-cancel-btn`(부정). 둘 다 `role="button"`.
- 팝업이 떠 있는 동안 재생은 멈춘다(인트로 종료 지점에서 대기).

관찰된 두 문구:

| 유형 | `.confirm-msg-text` | 긍정 버튼 |
|---|---|---|
| 이어보기 | `이전에 시청했던 {MM:SS}부터 이어서 보시겠습니까?` (예/아니오) | `.confirm-ok-btn`=예 → 이어서 재생 |
| 재생 중(동시) | `본 콘텐츠의 진도체크를 시작합니다. 실행중인 다른 콘텐츠의 진도체크는 중단됩니다.` (확인/취소) | `.confirm-ok-btn`=확인 → 이 콘텐츠 시작, 다른 콘텐츠 중단 |

- 동시 재생은 **두 번째 콘텐츠에서** 발생하며, 두 콘텐츠가 각각 `.confirm-msg-box`를 가진다.
  첫 콘텐츠는 두 번째가 확인을 누르면 진도체크가 중단된다.
- 완료(진행 100%)된 콘텐츠는 이어보기 팝업이 뜨지 않았다. 진행이 일부 남은 콘텐츠에서만 뜬다.

## 기존 코드와의 관계

`video_parser.py`의 `try_dismiss_confirm_dialog`는 이미 `.confirm-msg-box` + `.confirm-ok-btn`/
`.confirm-cancel-btn`을 처리한다(이어보기 예/아니오). 이번 조사로 **같은 박스가 동시 재생 팝업에도
쓰이며 텍스트로 구분**함을 확인했다. 8-B 재생 워커는 `.confirm-msg-text`를 읽어
`이어서 보시겠습니까`/`진도체크`를 판별하고, 긍정 버튼을 눌러 진행하면 된다. ADR-004의
"동일 시도 3회 반복 시 일시중지"는 이 팝업 처리 루프에 카운터로 넣는다.

## 반영할 설계

- 팝업 처리: `.confirm-msg-text` 키워드로 이어보기/재생 중을 구분하고 `.confirm-ok-btn` 클릭으로 진행.
- 재생은 인트로(`intro.mp4`, 약 5초) 이후 실제 미디어 시간이 증가하는지로 확인한다.
- 재생·감지·다운로드가 모두 같은 Chrome/CDP를 쓰므로 단일 슬롯 직렬화가 필요하다(락 순서는 다음 항목).

## 남은 조사

- [ ] 감지·재생·다운로드의 Chrome/CDP 락 순서 확정
- [ ] 출석 인정을 위한 재생 시간 기준(끝까지/일부 임계)
- [ ] 실제 자동 재생 워커 구현과 실제 LMS 검증

합성/실제 산출물(스크린샷·로그)은 `/tmp/lms-stage7`에 두며 Git에 포함하지 않는다.
계정·비밀번호·과목명·강의 제목·URL은 기록하지 않았다.

[자동 재생 상세 계획](../plans/auto-play-new-lectures.md) · [ADR-004](../decisions/004-auto-play-and-ux-improvements.md)
