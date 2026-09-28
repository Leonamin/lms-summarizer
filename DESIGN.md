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
- **모달 없음.** 부가 정보는 페이지 전환 또는 네이티브 `<details>`로 접는다(작업 로그·시도 이력·서버 진단·설정 고급).
  파괴적 전체 동작만 `window.confirm`.
- **커스텀 컨트롤.** 네이티브 `<select>`/`<datalist>` 없이 `Dropdown`(선택)과 `Combobox`(자유 입력)를 쓴다.
- **텍스트 글리프 아이콘.** 아이콘 라이브러리 없이 유니코드 글리프(▤ ⚙ ↑ ✓ × ↗ ★ ↓ →)를 쓴다.

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
- 작업실 흐름: `.overview` → `.lms-panel` → `.intake` → `.workspace-grid`.
- `.overview` = 지표 카드 2개 + `.pipeline-summary`(4열).
- `.workspace-grid` = `minmax(320px,.84fr) minmax(0,1.16fr)` 2열(작업 목록 / 작업 상세). 1180px 이하 1열(`minmax(0,1fr)`), 자식 `min-width:0`.
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
  `grid-template-columns: 96px minmax(0,1fr) 78px 46px 86px`(상태·이름·시작·시도·만든 시각) 공유.
- **자동 재생 그룹**: 재생 큐가 비어 있지 않으면 표의 머리글 아래에 `.playback-group`(brand-50 배경)으로
  `AUTO PLAY` 행을 표시한다. 행은 `재생 중`/`재생 대기` 배지 + 제목 + `재생` + `-` + 만든 시각이며
  `.playback-row`로 비인터랙티브다. 자동 재생이 작업과 같은 단일 슬롯을 쓰는 것을 화면에서 구분한다.
- **선택 행 표시 = 좌측 인디케이터**: `.job-row.selected::before`가 왼쪽에서 **8px(모바일 6px) 떨어진 위치**에
  **너비 3px·세로 중앙(상하 9px 제외)·완전 라운드** 사각형 pill을 그린다. 좌측 보더/그림자를 쓰지 않는다.
- ≤680px에서 시작·시도·시각과 헤더를 숨기고 상태·이름만 남긴다.

### Stage track
- `.stage-track`는 **연결된 4단계 트랙**: 각 `li`에 `::after` 연결선, 28px 원형 마커.
  `.completed`(positive 채움, 연결선 강조), `.running`(brand 채움 + 4px 광), 그 외 기본.

### Disclosure & Logs
- 모달 대신 `<details>`(`.server-panel`, `.attempt-history`, 설정 섹션).
- 로그 `.job-logs`(타임스탬프+메시지, 3초 폴링, 최근 200개). 마크다운 리더 `.markdown`.

### States (로딩 · 오류 · 빈 결과)
- **초기 로딩**: `.skeleton`(배경 #eceef4, radius 8px) + `prefers-reduced-motion`에서만 shimmer. 통계 카드는
  `.skeleton-num`/`.skeleton-label`, 작업 목록은 `.skeleton-row` 6행, 상세 패널은 `.result-skeleton`.
  헤더·파이프라인·입력 카드는 그대로 렌더해 레이아웃이 흔들리지 않는다.
- **서버 오류**: `.server-banner`(danger-soft 배경, 라운드, `!` 아이콘, "서버에 연결하지 못했습니다." +
  "다시 연결" 버튼)를 헤더 아래에 표시한다. 자동 재연결을 시도하고 버튼은 즉시 재시도한다.
- **검색·필터 빈 결과**: 작업 목록 `.empty`에 "조건에 맞는 작업이 없습니다." + `.secondary` "검색·필터 초기화" 버튼.
  작업 자체가 없을 때는 초기화 버튼 없이 안내만 표시한다.
- 그 외 권한·결제·부분 실패 등은 이 제품에 없는 상태라 제외한다.

## Do's and Don'ts

- 색·라디우스·타이포·모션 속도·**컨트롤 높이(`--control-h`)**·포커스 링은 `:root` 토큰을 참조한다. 원시 hex 하드코딩을 피한다.
- **좌측 accent bar/border를 쓰지 않는다.** 선택 표시가 필요하면 위의 라운드 인디케이터/점을 쓴다.
- 상태는 "진한 전경 + `-soft` 배경" 쌍을 따르고, 텍스트 라벨을 함께 쓴다(색만으로 구분 금지).
- 선택 입력은 네이티브 `<select>` 대신 `Dropdown`, 자유 입력은 `Combobox`를 쓴다. 작업 목록형 정보는 표(`.job-row`)로 표현한다.
- 새 부가 정보는 모달 대신 페이지 전환 또는 `<details>`로 표현한다.
- 포커스는 `:focus-visible` + `--ring`을 유지한다. 진입 모션은 `prefers-reduced-motion` 게이트 안에 둔다.
- Pretendard 자체 호스팅을 유지한다.

## Responsive Behavior

- **≥1500px**: `main` 좌우 패딩 72px.
- **≤1180px**: 레일 216px, `.workspace-grid` 1열(`minmax(0,1fr)`), 작업 목록 `max-height:400px`.
- **≤900px**: `.overview` 2열(파이프라인 전폭), `.intake` 1열, `.settings-grid` 1열, `.course-checks` 1열.
- **≤680px**: `.app-shell` block(레일 상단 가로 바), 브랜드 서브·캡션·하단·`private-label`·`file-types`·`nav-count` 숨김,
  `h1` 26px, 단계 트랙 2열 wrap, 작업 표 2열(상태·이름), 입력 16px.
- **`prefers-reduced-motion: no-preference`**: `rise` 진입 모션(0.4s).

## Spacing & Sizing

간격 토큰 스케일은 없다. 반복 리터럴 값을 관례로 쓴다.

- 카드 패딩: 30px(작업실), 8px 32px 30px(설정), 20px(모바일).
- 섹션 헤딩 `28px 28px 18px`, 작업 행 `12px 28px`, 리더 `0 28px`.
- 그리드 갭: 24px(작업실 2열), 20px(카드 행), 22px 26px(설정 폼), 14px(파이프라인).
- 컨트롤: 높이 46px(모든 입력·셀렉트·드롭다운), 버튼 최소 42px, 배지 5px 12px.
- 고정 치수: 레일 264px(≤1180 216px), `main` 최대 1480px, 설정 카드 최대 960px, 작업 목록 `max-height:640px`.

## Icons & Imagery

- 아이콘 라이브러리 없음. 유니코드 글리프만 사용. 이미지 자산 없음(폰트만).
- 마크다운 요약은 `react-markdown`, raw HTML 비활성화. 코드는 `--bg` 칩.

## Motion & Interaction

- 대부분 `transition: … var(--speed)`(0.16s). hover 배경/테두리/색, `:focus-visible` 링, `:active` 1px 하강.
- 선택 상태: 작업 행은 인디케이터, 내비는 밝은 오버레이, 탭은 배경/색 반전, 단계는 completed/running.
- disabled: `opacity:.5`. 로딩 스피너/스켈레톤 없음(텍스트 상태·SSE 라벨로 표현).
- 진입 애니메이션 `rise`(opacity+translateY(8px))는 `prefers-reduced-motion: no-preference`에서만.

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
- 다크 테마·모달/드로어 시스템·스켈레톤 로딩은 존재하지 않는다.
