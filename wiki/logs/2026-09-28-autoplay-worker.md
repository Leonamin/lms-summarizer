---
type: Log
title: "8-B 자동 재생 워커 구현·검증"
description: "재생 큐·팝업 처리·출석 확인 워커 구현과 실제 LMS 끝까지 재생 검증"
timestamp: 2026-09-28
okf_version: "0.1"
---

# 8-B 자동 재생 워커 구현·검증

## 구현

- `src/video_pipeline/playback.py`
  - `classify_popup(text)`: 공유 팝업(`.confirm-msg-box`)을 텍스트로 `resume`/`simultaneous`/`other`로 구분.
  - `play_to_end(...)`: 재생 시작 → 팝업을 긍정 버튼(`.confirm-ok-btn`)으로 처리 → 실제 미디어가 끝까지 재생되면 완료.
    같은 시도에서 팝업이 3회면 `popup_repeat`으로 중단(ADR-004). 인트로(`intro.mp4`/`preloader.mp4`, 길이 < 6초)는
    완료 판정에서 제외한다.
  - `execute_playback(command)`: 로그인 → 강의 열기 → 재생 → 출석 확인(`attendance.verify_attendance`, 타임아웃 시 새로고침)
    → `StageResult(kind='playback', data={attended, popup_repeats, ...})`.
- `src/core/services/playback.py` `PlaybackQueue`: 영속 큐(`playback.json`). 같은 강의 중복 방지,
  `recover()`로 실행 중 → 중단, `dispatch(slot)`/`finish(command, result)`. 출석이 확인되면 설정 범위에 따라
  자동 저장 작업을 `autosave:<url>` 멱등 키로 제출한다.
- `src/core/services/jobs.py`: 다운로드 슬롯에서 **재생 → 과목 조회 → 다운로드** 우선순위로 디스패치하고,
  재생 명령에는 긴 재생 제한 시간(`playback_timeout`, 기본 3시간)을 적용한다. `_discard`가 재생 명령에서
  임시 디렉터리를 지우지 않도록 가드했다.
- `src/core/runtime/executor.py`: `command.playback`이면 `asyncio.run(execute_playback(...))`.
- `src/web/autoplay.py`: 신규 영상을 **재생 큐에 넣고**, 실패한 재생에 `popup_repeat`이 있으면 자동 재생을 일시중지한다.
- API/UI: `GET /playback`, 자동 감지 상태에 `playing` 수 추가.

## 검증

- 단위 테스트: `tests/test_playback.py`(분류·끝까지 재생·팝업 처리·3회 반복·큐 디스패치/중복/자동 저장/복구),
  `tests/test_autoplay.py` 갱신(재생 큐 적재). **전체 82개 통과.**
- **실제 LMS 스모크**: 9분 6초 movie 강의를 `execute_playback`으로 실행 → 568초 동안 끝까지 재생
  (`t=546.6/547.1`, `intro=false`), 팝업 없음(이미 완료된 콘텐츠), **출석 확인 `attended=true`**.
  로그: `[RESULT] 568s kind=playback error=- data={"completed": true, ..., "attended": true}`.
- 구현 중 발견·수정: `play_to_end`가 인트로(4.7초) 종료를 완료로 오인 → 진행 판정에
  인트로/프리로더 및 길이<6초 제외를 추가.

## 전체 흐름 검증 (2026-09-28)

신규 미완료 강의(movie 16:49)로 **자동 감지 → 재생 → 출석 → 자동 저장** 전체를 실제 LMS에서 확인했다.

- 자동 감지를 켜고(선택 과목·주기 5분·범위 다운로드) 강제 확인 → 재생 큐에 적재되어 `running`.
- 약 1020초(17분) 동안 끝까지 재생되어 **`attended=true`**로 완료.
- 출석 확인 후 자동 저장 작업이 `autosave:<url>` 멱등 키로 제출되어 **완료**(`end_stage=1`,
  `result_kind=stage_artifact`, video 88.5MB).
- 주의: Docker 기본 `LMS_CHROME_HEADLESS=true`에서는 영상 재생이 안 되므로 자동 재생은
  **`LMS_CHROME_HEADLESS=false`(Xvfb·headed)**로 실행해야 한다. headless로 시작한 시도는 중단으로 복구됐고,
  headed로 전환 후 정상 완료했다.
- 긴 강의(52:02)는 검증 대상에서 제외(감지 기록에 미리 seen 처리)해 흐름만 확인했다.

## 팝업 처리·headed 정책 확인 (2026-09-28)

- **팝업 처리 실제 확인(아이템 1)**: 진도가 남은 readystream 콘텐츠로 재생 워커를 실행해
  `.confirm-msg-box`의 이어보기 팝업을 감지·분류(`resume`)하고 긍정 버튼으로 처리함을 확인했다
  (결과 `popups=["resume"]`, `popup_repeats=1`; 75초 제한 초과는 예상된 결과).
- **3회 반복**: LMS 버그로 같은 시도에서 3회 반복을 인위적으로 재현하지는 못했다. 카운터·중단·자동 감지
  일시중지는 단위 테스트(`test_playback`)와 배선으로 검증했다.
- **headed 운영 정책(아이템 4)**: 서버가 항상 Xvfb를 기동하고(`src/web/__main__.py`), 재생 워커는
  headed로 고정하며(`headless=False`), 다운로드·조회는 `LMS_CHROME_HEADLESS`(기본 headless)를 따른다.
  headless 모드에서도 Xvfb가 기동됨을 실제 컨테이너에서 확인했다.

## 남은 검증

- readystream(슬라이드+오디오) 유형 **끝까지 재생·진도 100%·출석**(이번엔 팝업 처리만 확인).
- 팝업 3회 반복 실제 재현(가능하면).
- 여러 편 연속 재생과 다운로드와의 슬롯 경합, 장시간 운영.

합성/실제 산출물은 `/tmp/lms-stage7`에 두며 Git에 포함하지 않는다. 계정·과목명·제목·URL은 기록하지 않았다.

[자동 재생 상세 계획](../plans/auto-play-new-lectures.md) · [DOM 조사](2026-09-28-autoplay-dom-investigation.md) · [ADR-004](../decisions/004-auto-play-and-ux-improvements.md)
