---
version: alpha
name: LMS 강의 작업실 (Web Dashboard)
description: "Docker 웹 대시보드(frontend/)의 실제 구현 디자인 시스템. 토큰은 frontend/src/style.css :root 에 정의되어 있다."
colors:
  brand: "#4f46b8"
  brand-strong: "#3b338f"
  brand-bright: "#635ac9"
  brand-soft: "#ecebfa"
  brand-faint: "#f5f5fd"
  violet: "#b771e5"
  positive: "#2f7a5b"
  positive-soft: "#dff1e7"
  warning: "#9a6b0a"
  warning-soft: "#fdf3d6"
  danger: "#c93b58"
  danger-soft: "#fbe6ea"
  ink: "#1b1a33"
  ink-soft: "#3a3850"
  muted: "#666579"
  faint: "#8f8ea0"
  line: "#e9eaf2"
  line-strong: "#d8d9e5"
  surface: "#f6f7fb"
  paper: "#ffffff"
  paper-soft: "#fafbfe"
  rail: "#17142f"
typography:
  display:
    fontFamily: "Pretendard Variable"
    fontSize: 33px
    fontWeight: 760
    lineHeight: 1.22
    letterSpacing: -0.6px
  title:
    fontFamily: "Pretendard Variable"
    fontSize: 21px
    fontWeight: 700
    lineHeight: 1.35
    letterSpacing: -0.3px
  subtitle:
    fontFamily: "Pretendard Variable"
    fontSize: 17px
    fontWeight: 650
    lineHeight: 1.5
  body:
    fontFamily: "Pretendard Variable"
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.6
  body-sm:
    fontFamily: "Pretendard Variable"
    fontSize: 13.5px
    fontWeight: 400
    lineHeight: 1.6
  caption:
    fontFamily: "Pretendard Variable"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.5
  eyebrow:
    fontFamily: "Pretendard Variable"
    fontSize: 11px
    fontWeight: 750
    lineHeight: 1.4
    letterSpacing: 1.8px
rounded:
  panel: 18px
  control: 12px
  input: 10px
  pill: 999px
components:
  button-primary:
    backgroundColor: "{colors.brand}"
    textColor: "{colors.paper}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "0 22px"
    height: 42px
  button-primary-hover:
    backgroundColor: "{colors.brand-strong}"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
  button-secondary:
    backgroundColor: "{colors.brand-soft}"
    textColor: "{colors.brand-strong}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.control}"
    padding: "0 18px"
  button-ghost:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.control}"
    padding: "0 16px"
  button-danger:
    backgroundColor: "{colors.danger-soft}"
    textColor: "{colors.danger}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.control}"
    padding: "0 16px"
  input:
    backgroundColor: "{colors.paper-soft}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.input}"
    padding: "11px 13px"
    height: 46px
  panel:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-soft}"
    rounded: "{rounded.panel}"
    padding: "30px"
  rail:
    backgroundColor: "{colors.rail}"
    textColor: "{colors.paper}"
    width: 264px
  nav-item:
    textColor: "{colors.paper}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "12px 14px"
  nav-item-selected:
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    padding: "12px 14px"
  badge:
    typography: "{typography.caption}"
    rounded: "{rounded.pill}"
    padding: "5px 12px"
  badge-completed:
    backgroundColor: "{colors.positive-soft}"
    textColor: "{colors.positive}"
    rounded: "{rounded.pill}"
    padding: "5px 12px"
  badge-running:
    backgroundColor: "{colors.brand}"
    textColor: "{colors.paper}"
    rounded: "{rounded.pill}"
    padding: "5px 12px"
  badge-queued:
    backgroundColor: "{colors.brand-soft}"
    textColor: "{colors.brand-strong}"
    rounded: "{rounded.pill}"
    padding: "5px 12px"
  badge-warning:
    backgroundColor: "{colors.warning-soft}"
    textColor: "{colors.warning}"
    rounded: "{rounded.pill}"
    padding: "5px 12px"
  badge-danger:
    backgroundColor: "{colors.danger-soft}"
    textColor: "{colors.danger}"
    rounded: "{rounded.pill}"
    padding: "5px 12px"
  tab:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.muted}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.pill}"
    padding: "9px 18px"
  tab-active:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.brand-strong}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.pill}"
    padding: "9px 18px"
  dropdown-trigger:
    backgroundColor: "{colors.paper-soft}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.input}"
    padding: "10px 13px"
    height: 46px
  dropdown-item:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.body}"
    rounded: "{rounded.input}"
    padding: "10px 13px"
    height: 42px
  dropdown-item-selected:
    backgroundColor: "{colors.brand-soft}"
    textColor: "{colors.brand-strong}"
    typography: "{typography.body}"
    rounded: "{rounded.input}"
    padding: "10px 13px"
  table-row:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.panel}"
    padding: "12px 28px"
---

# LMS 강의 작업실 — Web Dashboard Design System

이 문서는 이 저장소에 **이미 구현된** 웹 대시보드(`frontend/`)의 디자인 시스템을 기록한다.
현재 방향은 **B. 소프트 에디토리얼(Soft Editorial)** 이다(이전 A안의 좌측 accent bar·과한 그라디언트를 제거).

## Overview

**범위.** Vite/React 웹 대시보드 `frontend/`에만 적용된다. 설치는 `src/gui`(Flet), 서버는 `src/web`으로 별도다.
스타일 단일 소스는 `frontend/src/style.css`이며 Tailwind/PostCSS/토큰 파일은 없다.

**반복되는 시각 특성.**

- **플랫한 다크 레일 + 밝은 캔버스.** 좌측 `.rail`은 그라디언트 없는 단색 `--rail`(#17142f)에 옅은 우측 경계선,
  브랜드 마크만 인디고→바이올렛 그라디언트(절제된 accent). 캔버스는 `--bg`(#f6f7fb), 콘텐츠는 흰 카드.
- **좌측 accent bar 없음.** 카드·행·단계 어디에도 좌측 컬러 바/보더를 쓰지 않는다. 모든 카드는 **동일한 1px 헤어라인 보더**를
  쓴다(단계 카드 상단 강조 보더도 없다). 작업 목록 선택은 아래의 **인디케이터**로 표시한다.
- **넉넉한 여백 + 타이포 중심 위계.** 카드 패딩 30px, 섹션 간격 확대, 낮은 그림자, 헤어라인 경계.
- **상태는 알약 배지.** `--pill` 배지로 의미를 구분한다.
- **목적별 화면.** 작업실·강의 가져오기·처리 설정을 분리한다. 단계 집계·완료 작업의 처리 정보·로그는 `<details>`로 접는다.
  긴 결과의 전체 보기는 기존 네이티브 `<dialog>`를 사용하며 Esc·포커스 복귀를 유지한다.
- **커스텀 컨트롤.** 네이티브 `<select>`/`<datalist>` 없이 `Dropdown`(선택)과 `Combobox`(자유 입력)를 쓴다.
- **아이콘.** 내비게이션·자료 유형·처리 단계는 기존 lucide-react를 사용한다. 일부 기존 버튼의 화살표 글리프는 유지한다.

## Colors

토큰은 `:root`에 있고 값은 YAML `colors`와 같다. 상태 색은 "진한 전경 + `*-soft` 배경" 쌍으로 쓴다.

| 토큰 | 값 | 역할 |
|---|---|---|
| `--brand` | #4f46b8 | 기본 버튼, 실행 배지, 선택 인디케이터 |
| `--brand-500` | #635ac9 | hover 테두리, 브랜드 마크 그라디언트 |
| `--brand-700` | #3b338f | 링크, 보조 버튼 텍스트, queued 배지 텍스트 |
| `--brand-100` / `--brand-50` | #ecebfa / #f5f5fd | 보조 배경, 은은한 강조 |
| `--violet` | #b771e5 | 브랜드 마크 그라디언트의 보조 색(절제 사용) |
| `--positive` / `--positive-100` | #2f7a5b / #dff1e7 | 완료·단계 완료 |
| `--warning` / `--warning-100` | #9a6b0a / #fdf3d6 | 중단·중지, 안내 배너 |
| `--danger` / `--danger-100` | #c93b58 / #fbe6ea | 실패·취소·위험 버튼 |
| `--ink` / `--ink-2` | #1b1a33 / #3a3850 | 제목 / 기본 본문 |
| `--muted` / `--faint` | #666579 / #8f8ea0 | 보조 / 3차 텍스트 |
| `--line` / `--line-strong` | #e9eaf2 / #d8d9e5 | 카드 헤어라인 / 컨트롤 테두리 |
| `--bg` / `--paper` / `--paper-2` | #f6f7fb / #ffffff / #fafbfe | 캔버스 / 카드 / 입력 표면 |
| `--rail` | #17142f | 좌측 레일 배경(단색) |

## Typography

Pretendard 가변 폰트 자체 호스팅(`frontend/public/fonts/PretendardVariable.woff2`, `preload`).

- 본문 15px/1.6, `h1` `--t-2xl`(33px, -0.6px, 760), `h2` `--t-xl`(21px, 700), `h3` `--t-lg`(17px, 650).
- 스케일 토큰: `--t-2xs` 11 · `--t-xs` 12 · `--t-sm` 13.5 · `--t-md` 15 · `--t-lg` 17 · `--t-xl` 21 · `--t-2xl` 33 · `--t-display` 36.
- eyebrow: 11px / 750 / `letter-spacing: 1.8px`, `--brand`, TSX에서 대문자 문자열.
- 예외(리터럴): 브랜드 마크 22px, 업로드 심볼 22px, 빈 상태 아이콘 24px, 모바일 `h1` 26px, 모바일 입력 16px, 인라인 코드 0.92em.

## Layout

- `.app-shell` = `264px + minmax(0,1fr)`. `.rail`은 `sticky`, `height:100vh`, 단색 배경, 세로 flex.
- `main` 최대 1480px, 패딩 `44px clamp(24px,4vw,64px) 28px`(≥1500px 좌우 72px).
- 기본 화면은 `#workspace`: 제목·가져오기 버튼 → 상태 필터 → 접힌 단계 집계 → 작업 목록·상세.
- `.workspace-status-bar`의 전체·처리 중·완료·확인 필요는 실제 목록 필터다. 미완료 재생은 별도 큐 이력으로 이동한다.
- `.workspace-grid` = `minmax(360px,1fr) minmax(0,1.2fr)` 2열. 넓은 화면 상세는 `top:20px`로 sticky.
- 1180px 이하에서는 목록 또는 상세 하나만 표시한다. 행 선택 시 `#workspace/<job-id>`로 이동하고, 목록 복귀 시 검색·정렬·페이지·선택과 포커스를 유지한다.
- `#import`는 `.import-page`(최대 1000px) 안에 과목·주차 / URL 입력 / 파일 업로드 선택 버튼과 해당 폼만 표시한다.
  폼은 마운트 상태를 유지해 화면 이동 중 입력이 사라지지 않는다. 파일과 LMS의 종료 단계는 별도로 유지한다.
- `#settings`는 처리 설정과 서버 진단을 제공한다. 해시 이동으로 브라우저 뒤로가기·새로고침 시 현재 화면을 유지한다.
- `.settings-sheet` 단일 카드(최대 960px), 섹션 `fieldset`/`legend`, 필드 `.settings-grid` 2열(900px 이하 1열).
- 섹션 헤딩은 `.section-heading`(space-between).

## Elevation & Depth

- `--shadow-sm: 0 1px 2px rgba(24,22,51,.05)`(카드), `--shadow: 0 24px 48px -30px rgba(24,22,51,.4)`(드롭다운 메뉴).
- 카드는 거의 평면(헤어라인 + `--shadow-sm`). 주요 버튼은 그림자 없이 색으로만 구분. 포커스는 `--ring`.
- A안의 버튼 색 그림자·좌측 그라디언트 바는 제거했다.

## Shapes

- `--radius` 18px(카드), `--radius-sm` 12px(버튼·컨트롤), `--radius-xs` 10px(입력), `--pill` 999px(배지·탭).
- 브랜드 마크 14px(모바일 11px), 업로드 심볼 12px, 단계 마커 50%.
- 형태 언어: 카드 18px, 컨트롤 12px, 입력 10px, 상태/탭 알약. 그라디언트는 브랜드 마크에만.

## Components

근거: `frontend/src/components/*.tsx`, `frontend/src/pages/*.tsx`, `frontend/src/style.css`.

### Buttons
- `{components.button-primary}` — `.primary`. 단색 `--brand`, 흰 텍스트, 최소 높이 42px. hover `--brand-700`.
- `{components.button-secondary}` — `.secondary`(`--brand-100` 배경 + `--brand-700` 텍스트).
- `{components.button-ghost}` — `.ghost`(흰 배경 + `--line-strong` 테두리).
- `{components.button-danger}` — `.button-danger`(`--danger-100` + `--danger`).
- `.quiet`(텍스트형)와 `.danger`(색상만)가 CSS에 있으나 현재 TSX 사용처는 `.quiet`만 일부. (`.danger` 미사용)

### Inputs / Forms
- `{components.input}` — `input, select` 공통: `--paper-2`, `--line-strong`, `--radius-xs`, **고정 높이 `--control-h`(46px)**.
  `textarea`는 높이 고정 없이 `min-height:96px`. hover 브랜드 테두리, disabled `--bg`/`--faint`.
- `.settings-grid`에서 **모든 컨트롤이 동일 높이(46px)·동일 베이스라인**으로 정렬된다(라벨 상단). 체크박스만 17px.
- 비밀 입력은 `SecretField`(`.secret-field`+`.secret-actions`).
- 모바일(≤680px)에서 입력 `font-size:16px`(iOS 확대 방지).

### Cards / Panels
- `{components.panel}` — `.panel`. 흰 배경, `--line` 헤어라인, 18px, `--shadow-sm`. 패딩 30px(설정 8px 32px 30px).
- **모든 카드가 동일한 1px 헤어라인 보더**를 쓴다. 파이프라인 단계 카드도 상단 강조 보더 없이 같다.

### Navigation
- `{components.rail}` — 단색 `--rail`, `border-right: 1px solid rgba(255,255,255,.08)`.
  `{components.nav-item}` hover는 `rgba(255,255,255,.06)`, `{components.nav-item-selected}`는 `rgba(255,255,255,.1)`(좌측 바 없음).
  `.nav-count` 알약. ≤680px에서 상단 가로 바로 전환.
- **접기/펼치기**: `.rail-toggle`은 레일 **최상단**에 절대 배치(`top: 41px`)하고, 펼침은 `right: 12px`,
  접힘은 `right: 24px`로 두어 `right` 트랜지션으로 부드럽게 중앙으로 이동한다.
  접으면 `.app-shell.rail-collapsed`가 `78px`로 줄고(브랜드는 숨김) 아이콘만 남기며,
  `.app-shell`의 `grid-template-columns`에 `240ms` 트랜지션을 걸어 본문이 좌우로 부드럽게 이동한다.
  상태는 `localStorage`에 저장한다.
- **좌우 패딩 고정**: 펼침/접힘 모두 `.rail`의 좌우 패딩을 `12px`로 같게 두어 레일 내용이 좌우로 튀지 않는다.
  상하 패딩(30px)과 `nav` 위치도 같도록 접힘에서도 `.rail-caption`의 공간을 `visibility: hidden`으로 예약하고
  `.rail-head`에 `min-height: 53px`를 둔다.
- 아이콘은 중앙 정렬한 전체 폭 알약(`.rail.collapsed .nav-item`)으로 그린다. 하단 `.connection-dot`(실시간 연결 표시)은
  접힘에서 `text-align: center`로 중앙 정렬한다. 모바일(≤680px)에서는 토글을 숨기고 가로 바를 유지한다.

### Badges / Status
- `{components.badge}` — `.status` 알약(12px/650). 변형: `.completed`(positive-soft), `.running`(brand 배경+흰 글자),
  `.queued`(brand-soft), `.cancelling`·`.interrupted`(warning-soft), `.failed`·`.cancelled`(danger-soft).
- 같은 알약 형태가 `.private-label`, `.file-types`, `.nav-count`에 재사용된다.

### Tabs
- 세그먼트형 `{components.tab}`/`{components.tab-active}` — `.segmented`(알약, `--bg`) 안 버튼, 활성 흰 배경.
- 산출물 탭 `.artifact-tabs` — 알약 버튼, 기본 `--bg`/`--muted`, 활성 `--brand`+흰 글자.
  두 탭 패턴의 스타일이 서로 다르다(Known Inconsistencies).

### Dropdown & Combobox
- `components/Dropdown.tsx`: 네이티브 `<select>` 대신 쓰는 listbox. 트리거 46px, 항목 42px, `.dropdown-menu`는 `z-index:60`.
- `components/Combobox.tsx`: 자유 입력(모델 ID). 같은 `.dropdown-menu`/`.dropdown-item` 재사용, 우측 caret 토글.
- **가려짐 방지**: `.panel:has(.dropdown.open){ z-index:40 }`으로 열린 드롭다운을 가진 카드를 형제 위로 올려
  다른 카드에 메뉴가 잘리거나 가려지지 않는다.

### Data table (작업 목록)
- `.job-table-head`(sticky, 11px, `white-space:nowrap`) + `.job-row`가
  `grid-template-columns: 84px minmax(0,1fr) 70px 40px 72px`(상태·이름·단계 트랙·시도·만든 시각) 공유.
- **자동 재생 그룹**: 목록 하단 `.playback-group`(brand-50 배경)으로 `AUTO PLAY` 섹션을 표시한다.
  위치는 작업 목록·페이지네이션 다음이다. 재생 큐는 4단계 작업이 아니라 **별도 큐(PlaybackQueue)** 이며, 활성(대기/재생 중) 행은 배지 + 제목 + 시각으로
  보여준다. `지난 재생 N건` 토글을 펼치면 완료/실패/중단 이력을 상태 배지 + 제목 + 출석(출석/미출석) +
  연결 작업 수 + 시각으로 최근 20건까지 보여준다(`/playback`는 전체 상태를 반환). `.playback-row`는 flex(비인터랙티브).
  상태 영역의 **`미완료 재생` 버튼**(중단·실패 합계)을 누르면 이력을 펼치고
  `중단·실패` 필터를 켠 뒤 그룹으로 스크롤한다. 이력 필터는 `전체 / 미출석 / 중단·실패` 세그먼트(`.playback-filters`).
  `작업 N` 칩(`.playback-link`)을 누르면 연결된 작업으로 이동한다(필터·검색 초기화 → 해당 페이지로 이동 →
  선택 → 행 스크롤).
- **선택 행 표시 = 행 배경 + 현재 단계 슬롯 칩**: 별도 좌측 pill이나 대표 아이콘을 두지 않는다.
  `.job-row.selected`는 `--brand-50` 배경 + 이름 `--brand-700`, 그리고 `.stage-mini-slot.current`가
  `--brand`로 채워진 칩이 된다.
- **단계 트랙**: `.stage-mini`가 4개 단계 아이콘(14px)을 나란히 그린다. 슬롯 색 = 단계 상태
  (완료 `--positive`, 진행 `--brand`+링 펄스, 대기 `--brand-500` 50%, 실패 `--danger`, 미도달 `--line-strong`).
  각 슬롯 `title`은 `n. 단계명 · 상태`. `current_stage` 기준 현재 단계 슬롯에 `.current`가 붙는다.
- **이름 표시**: 강의 제목 아래 과목·주차를 보조 텍스트로 표시하고 세 항목을 함께 검색한다. 긴 값은 말줄임한다. URL 작업은 다운로드 완료 시 강의 제목으로 이름이 바뀐다.
- **내부 스크롤 없음**: `.job-list`는 자체 스크롤바 없이 페이지 흐름으로 늘어난다. 중간 화면(681–1600px)에서는
  `시도`·`시각` 열을 숨겨 이름 열 공간을 확보하고, ≤680px에서 트랙·시도·시각과 머리글을 숨겨 아이콘·상태·이름만 남긴다.
- **페이지네이션**: `.job-pager`가 목록 하단(`12px 28px`)에 `1–20 / 24` 범위와 `‹ 현재/전체 ›` 이동을 보여주고,
  오른쪽에 페이지당 개수 세그먼트(`10`/`20`)를 둔다. 기본 20개/페이지, 10/20 선택. 필터·검색·정렬·개수 변경 시
  1페이지로 돌아간다(`useEffect` 의존성).
- **정렬**: `.job-sortby` 세그먼트(`최신순`/`과거순`)가 `created_at` 정렬을 제어하고, 표 머리글 클릭 정렬과
  같은 `sort` 상태를 공유한다(현재 정렬 열이 `만든 시각`일 때만 세그먼트가 활성). `.segment` 공통 스타일은
  도구 행 높이 `var(--control-h)`, 페이저에서는 `34px`.

### Stage track
- `.stage-track`는 **연결된 4단계 트랙**: 각 `li`에 `::after` 연결선, 28px 원형 마커.
  `.completed`(positive 채움, 연결선 강조), `.running`(brand 채움 + 4px 광), 그 외 기본.
- 작업 상세 헤더의 `.result-subtitle`에 `과목 · 주차`(있을 때만)를 회색 한 줄로 표시하고, 넘치면 말줄임 +
  `title` 툴팁. 목록에는 표시하지 않는다.

### Disclosure & Logs
- 모달 대신 `<details>`(`.server-panel`, `.attempt-history`, 설정 섹션).
- 로그 `.job-logs`(타임스탬프+메시지, 3초 폴링, 최근 200개). 마크다운 리더 `.markdown`.

### 이어서 처리 (Continue)
- 작업 상세의 `.continue-row`: 완료(`completed`)이고 `end_stage < 4`인 작업에 `Dropdown`(오디오 변환까지/
  음성 인식까지/요약까지) + `.secondary` `이어서 처리` 버튼을 노출한다. **끝난 단계 다음부터** 실행하며
  이미 만든 산출물을 재사용한다(`retry`는 원래 시작 단계부터 재실행).

### 이어서 재개 (Resume)
- 실패·취소·중단(`retryable`) 작업에서 **마지막 완료 단계의 산출물이 남아 있으면** `.secondary` `이어서 재개`
  버튼과 `.quiet` `처음부터` 버튼을 함께 노출한다. 이어서 재개는 `continue_job`처럼 마지막 완료 단계+1부터
  실행해 재다운로드를 피한다(`POST /jobs/{id}/resume`). 산출물이 없으면 `no_resume_point`로 거부하고
  `다시 시도`(retry)만 노출한다. 서버 재시작으로 중단된 작업을 값싸게 복구하는 용도다.

### States (로딩 · 오류 · 빈 결과)
- **초기 로딩**: `.skeleton`(배경 #eceef4, radius 8px) + `prefers-reduced-motion`에서만 shimmer. 통계 카드는
  `.skeleton-num`/`.skeleton-label`, 작업 목록은 `.skeleton-row` 6행, 상세 패널은 `.result-skeleton`.
  현재 화면의 헤더와 프레임을 유지한다. 가져오기 폼은 작업실의 로딩 상태에 노출하지 않는다.
- **서버 오류**: `.server-banner`(danger-soft 배경, 라운드, `!` 아이콘, "서버에 연결하지 못했습니다." +
  "다시 연결" 버튼)를 헤더 아래에 표시한다. 자동 재연결을 시도하고 버튼은 즉시 재시도한다.
- **검색·필터 빈 결과**: 작업 목록 `.empty`에 "조건에 맞는 작업이 없습니다." + `.secondary` "검색·필터 초기화" 버튼.
  작업 자체가 없을 때는 초기화 버튼 없이 안내만 표시한다.
- **AI 오류 사유**: 요약(4단계) 실패는 워커가 원문·키를 버리고 안전 코드로만 환원한다 —
  `ai_unavailable`(5xx/네트워크) · `ai_quota`(429) · `ai_auth`(401/403) · `ai_timeout`(408/타임아웃).
  `_terminal`이 코드별 한국어 `safe_message`를 넣고 상세 `.inline-error`에 표시한다.
- 그 외 권한·결제·부분 실패 등은 이 제품에 없는 상태라 제외한다.

## Do's and Don'ts

- 색·라디우스·타이포·모션 속도·**컨트롤 높이(`--control-h`)**·포커스 링은 `:root` 토큰을 참조한다. 원시 hex 하드코딩을 피한다.
- **좌측 accent bar/border를 쓰지 않는다.** 선택 표시가 필요하면 위의 라운드 인디케이터/점을 쓴다.
- 상태는 "진한 전경 + `-soft` 배경" 쌍을 따르고, 텍스트 라벨을 함께 쓴다(색만으로 구분 금지).
- 선택 입력은 네이티브 `<select>` 대신 `Dropdown`, 자유 입력은 `Combobox`를 쓴다. 작업 목록형 정보는 표(`.job-row`)로 표현한다.
- 새 부가 정보는 페이지 전환 또는 `<details>`로 표현한다. 기존 결과 전체 보기의 네이티브 `<dialog>`는 유지한다.
- 포커스는 `:focus-visible` + `--ring`을 유지한다. 진입 모션은 `prefers-reduced-motion` 게이트 안에 둔다.
- Pretendard 자체 호스팅을 유지한다.

## Responsive Behavior

- **≥1500px**: `main` 좌우 패딩 72px.
- **≤1180px**: 레일 216px, 목록과 상세를 한 번에 하나씩 보여준다. 상세에서 목록 복귀 버튼을 제공한다.
- **≤900px**: `.settings-grid`·`.course-checks` 1열. 가져오기는 모든 폭에서 폼 하나만 보여준다.
- **≤680px**: `.app-shell` block(레일 브랜드 + 가로 메뉴), 브랜드 서브·캡션·하단·`private-label`·`file-types`·`nav-count` 숨김,
  `h1` 26px, 단계 트랙 2열 wrap, 작업 표 2열(상태·이름), 입력 16px.
- 화면 전환에는 지연 등장 모션을 적용하지 않는다. 상태 필터와 목록이 즉시 보이게 한다.

## Spacing & Sizing

간격 토큰 스케일은 없다. 반복 리터럴 값을 관례로 쓴다.

- 카드 패딩: 30px(작업실), 8px 32px 30px(설정), 20px(모바일).
- 섹션 헤딩 `28px 28px 18px`, 작업 행 `12px 24px`, 작업 도구·페이저 `28px`, 리더 `0 28px`.
- 그리드 갭: 24px(작업실 2열), 20px(카드 행), 22px 26px(설정 폼), 14px(파이프라인).
- 컨트롤: 높이 46px(모든 입력·셀렉트·드롭다운), 버튼 최소 42px, 배지 5px 12px.
- 고정 치수: 레일 264px(≤1180 216px), `main` 최대 1480px, 설정 카드 최대 960px.

## Icons & Imagery

- 아이콘은 **lucide-react**(shadcn 기본 셋, MIT·트리셰이킹)를 쓴다. 이모지는 쓰지 않는다.
  단계 아이콘 = 다운로드 `ArrowDownToLine`, 오디오 변환 `AudioLines`, 음성 인식 `Mic`, 요약 `Sparkles` (`lib/stageIcons.ts`).
  상세 `StageTrack`과 목록 `.stage-mini`가 같은 아이콘을 공유한다.
- 마크다운 요약은 `react-markdown`, raw HTML 비활성화. 코드는 `--bg` 칩.

## Motion & Interaction

- 대부분 `transition: … var(--speed)`(0.16s). hover 배경/테두리/색, `:focus-visible` 링, `:active` 1px 하강.
- 선택 상태: 작업 행은 현재 단계 슬롯 칩(`--brand` 채움) + `--brand-50` 배경, 내비는 밝은 오버레이, 탭은 배경/색 반전, 단계는 completed/running.
- disabled: `opacity:.5`. 초기 목록·상세는 스켈레톤으로 표현하고 SSE 연결 상태는 텍스트로 표시한다.
- 화면 전체 진입 애니메이션은 사용하지 않는다. 개별 컨트롤의 기존 짧은 hover 전환은 유지한다.

## Known Inconsistencies

1. **미사용 토큰/클래스**: `.danger`(색상만) 미사용. `.field-hint`도 미사용. (색 토큰 orphan은 lint 참고.)
2. **유사 역할의 두 탭 패턴**: `.segmented`(흰 활성)와 `.artifact-tabs`(brand 활성)가 다르다.
3. **배지 대비 편차**: `.running`만 채도 배경+흰 글자, 나머지는 틴트+진한 글자.
4. **간격 토큰 부재**: 여백이 리터럴 px로 흩어져 있다.
5. **타이포 예외**: 브랜드 마크·업로드 심볼·빈 상태 아이콘·모바일 `h1`·인라인 코드가 리터럴 px.
6. **일부 의미색 대비**: lint 측정상 `danger`/`warning` on `*-soft`는 WCAG AA 미달일 수 있어, 새 화면에서 색 쌍을 쓸 때 대비를 고려한다.
7. **`color-scheme: light` 고정**(다크 모드 없음).

## Known Gaps

- 데스크톱 GUI(`src/gui`) 시각 시스템은 범위 밖.
- 접근성 등급은 lint로 확인한 대비만 기록했고 나머지는 측정값이 없다.
- 다크 테마·일반 모달/드로어 시스템은 없다. 결과 전체 보기만 네이티브 dialog를 사용한다.

## Workspace Design Rationale

2026-10-04 개편은 기능 수를 줄이지 않고 가져오기와 처리·결과 확인의 화면 목적을 분리한다.
NN/g의 점진적 공개 원칙은 단계 집계·완료 작업의 처리 정보 접기에 적용한다.
Material의 목록–상세 레이아웃은 넓은 화면 병렬 배치와 좁은 화면 전환에 적용한다.
Linear Peek의 목록 맥락 유지 방식을 참고해 검색·선택·페이지를 보존한다. Linear의 단축키 전용 진입 방식은 복제하지 않는다.
관찰 근거·출처·검증 범위는 [작업실 개편 기록](docs/workspace-redesign.md)에 정리한다.
