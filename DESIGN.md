---
version: alpha
name: LMS 강의 작업실 (Web Dashboard)
description: "Docker 웹 대시보드(frontend/)의 실제 구현 디자인 시스템. 토큰은 frontend/src/style.css :root 에 정의되어 있다."
colors:
  brand: "#4635b1"
  brand-strong: "#372a8c"
  brand-bright: "#5b47c9"
  brand-soft: "#eceafa"
  brand-faint: "#f5f4fd"
  violet: "#b771e5"
  positive: "#337357"
  positive-soft: "#dcf0e4"
  warning: "#b9820a"
  warning-soft: "#fff4cc"
  danger: "#d93a5b"
  danger-soft: "#fde7ec"
  ink: "#181633"
  ink-soft: "#33314d"
  muted: "#5f6377"
  faint: "#8b8fa3"
  line: "#e7e8f1"
  line-strong: "#d4d6e4"
  surface: "#f4f5fa"
  paper: "#ffffff"
  paper-soft: "#fafbff"
  rail-top: "#2a1e6e"
  rail-mid: "#1b1442"
  rail-bottom: "#161029"
typography:
  display:
    fontFamily: "Pretendard Variable"
    fontSize: 32px
    fontWeight: 760
    lineHeight: 1.24
    letterSpacing: -0.5px
  title:
    fontFamily: "Pretendard Variable"
    fontSize: 20px
    fontWeight: 700
    lineHeight: 1.35
    letterSpacing: -0.2px
  subtitle:
    fontFamily: "Pretendard Variable"
    fontSize: 17px
    fontWeight: 650
    lineHeight: 1.5
  body:
    fontFamily: "Pretendard Variable"
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.55
  body-sm:
    fontFamily: "Pretendard Variable"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.55
  caption:
    fontFamily: "Pretendard Variable"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.4
  eyebrow:
    fontFamily: "Pretendard Variable"
    fontSize: 11px
    fontWeight: 750
    lineHeight: 1.4
    letterSpacing: 1.6px
rounded:
  panel: 16px
  control: 10px
  input: 8px
  pill: 999px
components:
  button-primary:
    backgroundColor: "{colors.brand}"
    textColor: "{colors.paper}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "12px 20px"
    height: 44px
  button-primary-hover:
    backgroundColor: "{colors.brand-strong}"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
  button-secondary:
    backgroundColor: "{colors.brand-soft}"
    textColor: "{colors.brand-strong}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.control}"
    padding: "10px 16px"
  button-ghost:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.control}"
    padding: "9px 14px"
  button-danger:
    backgroundColor: "{colors.danger-soft}"
    textColor: "{colors.danger}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.control}"
    padding: "9px 14px"
  input:
    backgroundColor: "{colors.paper-soft}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.input}"
    padding: "11px 12px"
  panel:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-soft}"
    rounded: "{rounded.panel}"
    padding: "24px"
  rail:
    backgroundColor: "{colors.rail-mid}"
    textColor: "{colors.paper}"
    width: 248px
  nav-item:
    textColor: "{colors.paper}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "12px 13px"
  nav-item-selected:
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    padding: "12px 13px"
  badge:
    typography: "{typography.caption}"
    rounded: "{rounded.pill}"
    padding: "5px 11px"
  badge-completed:
    backgroundColor: "{colors.positive-soft}"
    textColor: "{colors.positive}"
    rounded: "{rounded.pill}"
    padding: "5px 11px"
  badge-running:
    backgroundColor: "{colors.brand}"
    textColor: "{colors.paper}"
    rounded: "{rounded.pill}"
    padding: "5px 11px"
  badge-queued:
    backgroundColor: "{colors.brand-soft}"
    textColor: "{colors.brand-strong}"
    rounded: "{rounded.pill}"
    padding: "5px 11px"
  badge-warning:
    backgroundColor: "{colors.warning-soft}"
    textColor: "{colors.warning}"
    rounded: "{rounded.pill}"
    padding: "5px 11px"
  badge-danger:
    backgroundColor: "{colors.danger-soft}"
    textColor: "{colors.danger}"
    rounded: "{rounded.pill}"
    padding: "5px 11px"
  tab:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.muted}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.pill}"
    padding: "8px 16px"
  tab-active:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.brand-strong}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.pill}"
    padding: "8px 16px"
  dropdown-trigger:
    backgroundColor: "{colors.paper-soft}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.input}"
    padding: "10px 12px"
    height: 44px
  dropdown-item:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.body}"
    rounded: "{rounded.input}"
    padding: "10px 12px"
    height: 42px
  dropdown-item-selected:
    backgroundColor: "{colors.brand-soft}"
    textColor: "{colors.brand-strong}"
    typography: "{typography.body}"
    rounded: "{rounded.input}"
    padding: "10px 12px"
    height: 42px
  table-row:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.panel}"
    padding: "10px 24px"
---

# LMS 강의 작업실 — Web Dashboard Design System

이 문서는 이 저장소에 **이미 구현된** 웹 대시보드(`frontend/`)의 디자인 시스템을 기록한다.
새 화면을 추가할 때 이 규칙을 그대로 재현하기 위한 것이며, 새로운 디자인 언어를 제안하지 않는다.

## Overview

**범위.** 이 문서는 Vite/React 웹 대시보드 `frontend/`에만 적용된다. 설치는 `src/gui`(Flet 데스크톱)와
`src/web`(FastAPI 서버)은 별도의 시각 체계이며 이 문서가 다루지 않는다. 스타일의 단일 소스는
`frontend/src/style.css` 한 파일이고, 별도 Tailwind/PostCSS/토큰 파일은 없다(저장소 조사로 확인: CSS 파일은
`frontend/src/style.css` 하나뿐, `tailwind.config.*`·`postcss.config.*` 없음).

**반복되는 시각 특성(근거: `style.css`, `frontend/src/components/*`, `frontend/src/pages/*`).**

- **밝은 캔버스 + 흰 카드.** `body`는 `--bg`(#f4f5fa) 위에 우상단 `--brand-50` 방사형 그라디언트를 얹고,
  콘텐츠는 1px 헤어라인 테두리의 흰 `.panel` 카드에 담긴다.
- **딥 인디고/바이올렛 브랜드.** 좌측 `.rail`은 딥 인디고 그라디언트(#2a1e6e→#1b1442→#161029), 주요 액션은
  `--brand`(#4635b1)~`--brand-500`(#5b47c9) 그라디언트. 보조 강조는 `--violet`(#b771e5).
- **Pretendard + 조밀한 음수 자간의 제목.** 본문/제목 모두 `"Pretendard Variable"` 자체 호스팅. 제목은
  `letter-spacing` 음수(-0.2~-0.5px)로 조밀하게 조판한다.
- **상태는 알약 배지.** 작업 상태·개수·라벨은 `rounded.pill` 배지로 표현하고, 색으로 의미를 구분한다.
- **커스텀 드롭다운 + 컴팩트 표.** 네이티브 `<select>` 없이 커스텀 listbox `Dropdown`을 쓰고, 작업 목록은
  헤더가 있는 조밀한 표(`.job-table-head`/`.job-row`)로 표현해 세로 스크롤 누적을 줄인다.
- **모달 없음.** 웹 UI에는 dialog/modal 시스템이 없다. 부가 정보는 페이지 전환 또는 네이티브 `<details>`
  접기로 처리한다(`ServerPanel`, `JobLogs`, `attempt-history`, 설정의 `details`). 파괴적 전체 동작만
  `window.confirm`을 쓴다(`App.tsx`의 `stopAll`).
- **텍스트 글리프 아이콘.** 아이콘 라이브러리 없이 유니코드 글리프(▤ ⚙ ↑ ✓ × ↗ ★ ↓ →)를 쓴다.
- **절제된 진입 모션.** 카드 섹션이 아래에서 8px 올라오며 페이드 인한다(`rise`, `prefers-reduced-motion` 게이트).

## Colors

모든 색은 `frontend/src/style.css` `:root`에 토큰으로 정의되어 있고, 컴포넌트는 `var(--token)`으로 참조한다.
토큰 이름과 값은 YAML `colors`와 동일하다. 색상 출처는 ColorHunt 팔레트 2종이며 코드 주석에 기록되어 있다.

| 토큰 | 값 | 역할 (근거) |
|---|---|---|
| `--brand` | #4635b1 | 기본 버튼 배경, `.status.running` 배경, 강조 텍스트 |
| `--brand-500` | #5b47c9 | 버튼/브랜드 그라디언트 상단, hover 테두리 |
| `--brand-700` | #372a8c | 링크, 보조 버튼 텍스트, `.status.queued` 텍스트 |
| `--brand-100` | #eceafa | 보조 버튼/은은한 배지 배경, `.private-label` |
| `--brand-50` | #f5f4fd | `body` 방사형 그라디언트, 선택된 행 배경 |
| `--violet` | #b771e5 | 브랜드 마크·버튼 그라디언트의 보조 색 |
| `--positive` / `--positive-100` | #337357 / #dcf0e4 | 완료 배지, 단계 완료 상태 |
| `--warning` / `--warning-100` | #b9820a / #fff4cc | 중단·중지 배지, 안내 배너 |
| `--danger` / `--danger-100` | #d93a5b / #fde7ec | 실패·취소·위험 버튼, 오류 배너 |
| `--ink` | #181633 | 제목 |
| `--ink-2` | #33314d | 기본 본문 텍스트 (`body` 색) |
| `--muted` | #5f6377 | 보조 텍스트, 라벨 |
| `--faint` | #8b8fa3 | 3차 텍스트, 비활성 아이콘 |
| `--line` | #e7e8f1 | 카드/구분선 기본 테두리 |
| `--line-strong` | #d4d6e4 | 입력·고스트 버튼 테두리 |
| `--bg` | #f4f5fa | 페이지 배경, hover 배경 |
| `--paper` / `--paper-2` | #ffffff / #fafbff | 카드 표면 / 입력·중첩 표면 |

**의미색 사용 규칙(반복 패턴).** 상태 색은 항상 "진한 색 = 전경, `*-100`/`*-soft` = 배경" 쌍으로 쓴다
(`.status.*`, `.message.*`, `.button-danger`). `--brand`는 유일하게 배경 위에 흰 텍스트를 얹는 채도 색이다.

## Typography

폰트는 `@font-face`로 자체 호스팅한 가변 Pretendard이며(`frontend/public/fonts/PretendardVariable.woff2`,
`font-weight: 45 920`, `font-display: swap`, `index.html`에서 `preload`), 폴백은
`Pretendard, -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif`다.

- **본문**: `body` 15px / 1.55 / 400, 색 `--ink-2`.
- **제목**: `h1` 32px / 1.24 / 760 / -0.5px(모바일 680px 이하 25px), `h2` 20px / 700 / -0.2px, `h3` 17px / 650.
- **스케일 토큰**: `--t-xs` 12px, `--t-sm` 13px, `--t-md` 15px, `--t-lg` 17px. 이 4개가 대부분의 UI 텍스트를 담당한다.
- **eyebrow**: 11px / 750 / `letter-spacing: 1.6px`, `--brand` 색, TSX에서 대문자 문자열(LECTURE WORKSPACE 등)로 사용.
- **폴백/예외**: 제목(`h1` `--t-2xl`, `h2` `--t-xl`, `h3` `--t-lg`)·eyebrow(`--t-2xs`)·지표 숫자(`--t-display`)는
  토큰을 쓰지만, 브랜드 마크(22px)·업로드 심볼(22px)·빈 상태 아이콘(24px)·모바일 `h1`(25px)·모바일 입력(16px)·
  인라인 코드(`0.92em`)는 리터럴 px다. 아래 Known Inconsistencies 참고.

## Layout

- **앱 셸**: `.app-shell`은 `grid-template-columns: 248px minmax(0, 1fr)` 2열.
- **레일**: `.rail`은 `position: sticky; top: 0; height: 100vh`, 딥 인디고 그라디언트, 세로 flex
  (브랜드 → 캡션 → `nav` → 하단 연결 상태는 `margin-top: auto`).
- **메인**: `main`은 `max-width: 1500px`, `margin: 0 auto`, 패딩 `34px clamp(20px, 3vw, 48px) 24px`;
  1500px 이상에서 좌우 패딩 64px.
- **작업실 흐름**: `.overview`(통계+파이프라인) → `.lms-panel` → `.intake` → `.workspace-grid`.
- **`.overview`**: `grid-template-columns: repeat(2, minmax(0,150px)) minmax(0,1fr)` — 좌측에 지표 카드 2개,
  우측에 `.pipeline-summary`(4열).
- **`.workspace-grid`**: `minmax(300px, .82fr) minmax(0, 1.28fr)` 2열(작업 목록/결과). 1180px 이하 1열.
- **`.settings-sheet`**: 단일 컬럼 카드, `max-width: 900px`, 섹션은 `fieldset`/`legend`, 필드는 `.settings-grid` 2열
  (900px 이하 1열).
- **정렬 관례**: 섹션 헤딩은 `.section-heading`(space-between, 좌측 eyebrow+h2 / 우측 액션·배지). 좌측 정렬 기본.

## Elevation & Depth

- 토큰: `--shadow-sm: 0 1px 2px rgba(24,22,51,.06)`(카드 기본), `--shadow: 0 18px 40px -28px rgba(24,22,51,.45)`
  (정의되어 있으나 **현재 사용처 없음**).
- **기본 카드**(`.panel`, `.stat-card`, `.pipeline-step`)는 `--shadow-sm` + 1px 테두리로 거의 평면이다.
- **주요 버튼**만 색 그림자로 떠 보이게 한다: `box-shadow: 0 10px 20px -12px rgba(70,53,177,.9)`.
- **포커스 링**은 `--ring: 0 0 0 3px rgba(70,53,177,.22)`를 `:focus-visible`에 적용한다.
- 레일·배지·입력에는 그림자가 없다(평면 + 테두리/배경색으로 구분).

## Shapes

- 라디우스 토큰: `--radius` 16px(카드/패널), `--radius-sm` 10px(버튼·컨트롤·배지 없는 칩), `--radius-xs` 8px
  (입력·작은 버튼), `--pill` 999px(배지·세그먼트·알약형 라벨).
- 원형: 단계 트랙의 단계 마커(26px), `.connection-dot`(8px), 아바타류는 `border-radius: 50%`.
- 개별 예외: 브랜드 마크 13px, 모바일 레일 하단 `0 0 20px 20px`, 일부 5px(아이콘 칩).
- 형태 언어: 카드=둥근 16px 사각, 컨트롤=10px, 입력=8px, 상태/탭=알약. 그라디언트는 브랜드(레일·주요 버튼·
  업로드 심볼·브랜드 마크)에만 제한적으로 쓴다.

## Components

근거 파일: `frontend/src/components/*.tsx`, `frontend/src/pages/*.tsx`, `frontend/src/style.css`.

### Buttons
- `{components.button-primary}` — `.primary`. 인디고 그라디언트(180deg `--brand-500`→`--brand`), 흰 텍스트,
  `font-weight: 650`. hover는 `--brand`→`--brand-700`으로 어두워지고, active는 `translateY(1px)`.
- `{components.button-secondary}` — `.secondary`. `--brand-100` 배경 + `--brand-700` 텍스트 + 연보라 테두리(#ddd7f6).
- `{components.button-ghost}` — `.ghost`. 흰 배경 + `--line-strong` 테두리, hover 시 브랜드 테두리·텍스트.
- `{components.button-danger}` — `.button-danger`. `--danger-100` 배경 + `--danger` 텍스트 + #f3c6d1 테두리.
- `.quiet`(텍스트형)와 `.danger`(색상만) 클래스가 CSS에 정의되어 있으나 현재 TSX에서 사용되지 않는다(Known Inconsistencies).

### Inputs / Forms
- `{components.input}` — `input, textarea` 공통: `--paper-2` 배경, `--line-strong` 1px 테두리,
  `--radius-xs`, 패딩 `11px 12px`, `--ink` 텍스트. hover 시 브랜드 테두리, disabled 시 `--bg`/`--faint`.
  선택 입력은 네이티브 `<select>` 대신 `Dropdown`(위 항목)을 쓴다. 모델 ID 입력만 예외적으로
  `input` + `<datalist>`(자유 입력 콤보박스)를 유지한다.
- 라벨은 `label`에 `display:flex; flex-direction:column; gap:8px`, `--muted` 13px. 체크박스는 `.check`(행 정렬,
  `accent-color: var(--brand)`).
- 비밀 입력은 `SecretField`(`.secret-field` + `.secret-actions`)로 저장/교체/삭제 버튼과 "입력 값 보기" 체크를 묶는다.
- 모바일(≤680px)에서 모든 입력은 iOS 확대 방지를 위해 `font-size: 16px`로 강제된다.

### Cards / Panels
- `{components.panel}` — `.panel`. 흰 배경, `--line` 1px 테두리, `--radius`, `--shadow-sm`.
  콘텐츠 패딩은 24px(일부 패널 26~28px), 헤딩은 `.section-heading`이 담당.

### Navigation
- `{components.rail}` — `.rail` 좌측 고정. `{components.nav-item}`은 `.nav-item`(투명 배경, 밝은 보라 텍스트).
  `.nav-item:hover`는 `rgba(255,255,255,.08)`, `{components.nav-item-selected}`(`.nav-item.selected`)는
  `rgba(255,255,255,.14)` + 1px inset 흰 테두리. 활성 항목에 `.nav-count` 알약(작업 수)이 붙는다.
- 데스크톱은 세로 레일, ≤680px에서 가로 상단 바로 전환된다.

### Badges / Status
- `{components.badge}` — `.status` 알약(12px/650). 변형: `.completed`(positive), `.running`(브랜드 배경+흰 글자),
  `.queued`(brand-soft), `.cancelling`·`.interrupted`(warning-soft), `.failed`·`.cancelled`(danger-soft, 텍스트 #a32749).
- 같은 알약 형태가 `.private-label`, `.file-types`, `.nav-count`, `.step-index`류 라벨에 재사용된다.

### Tabs
- 세그먼트형 `{components.tab}`/`{components.tab-active}` — `.segmented` 컨테이너(알약, `--bg` 배경, 4px 패딩) 안의
  버튼. 활성은 흰 배경 + `--shadow-sm`. LMS 가져오기의 `URL 입력 / 과목·주차`.
- 산출물 탭 `.artifact-tabs` — 알약 버튼, 기본 `--bg`/`--muted`, 활성은 `--brand` 배경 + 흰 글자.
  두 탭 패턴의 스타일이 서로 다르다(Known Inconsistencies).

### Dropdown (listbox)
- `components/Dropdown.tsx`의 `Dropdown`. **네이티브 `<select>`를 쓰지 않는다**(앱 전체에 `<select>` 없음).
  버튼 트리거(`{components.dropdown-trigger}`, 최소 높이 44px) + `role="listbox"` 팝업 메뉴
  (`role="option"` 항목, `{components.dropdown-item}`, 최소 높이 42px)로 구성한다.
- 선택 항목은 `{components.dropdown-item-selected}`(brand-soft 배경 + brand-strong 텍스트 + ✓), 활성/호버는 brand-50.
- 키보드: 트리거 ArrowUp/Down/Enter/Space로 열고, 메뉴 ArrowUp/Down/Home/End/Enter/Escape/Tab과 첫 글자 type-ahead를
  지원한다. 메뉴는 트리거 폭에 맞춰 아래로 열리고 `--shadow`, 최대 높이 300px(모바일 50vh)로 스크롤된다.
- 용도: LMS 마지막 처리 단계, 학기, 과목, 상태 필터, 요약/음성 방식, 장치·정밀도, 프롬프트 방식, 요약 모드, 과목 분야.

### Data table
- 작업 목록(`JobList`)은 컴팩트 표다. `.job-table-head`(sticky 헤더, 11px 대문자)와 `.job-row`가
  `grid-template-columns: 92px minmax(0,1fr) 76px 84px`(상태·이름·시작·만든 시각)을 공유한다.
- 각 행은 선택 가능한 `<button>`(`{components.table-row}`)이며 선택 시 `.selected`(brand-50 + 좌측 3px 브랜드 바).
  이름은 한 줄 말줄임, 시각은 `tabular-nums`. ≤680px에서 시작·시각 열과 헤더를 숨기고 상태·이름만 남긴다.

### Stage track
- `.stage-track` 4열 그리드, 각 단계는 `--paper-2` 배경 + `--line` 테두리 카드, 26px 원형 마커.
  `li.completed`(positive-soft, 채워진 마커), `li.running`(brand-soft, 브랜드 마커 + 4px 광), 그 외 기본.

### Disclosure & Logs
- 모달 대신 `<details>`/`<summary>`(`.server-panel`, `.attempt-history`, 설정 섹션)로 접는다.
- 로그는 `.job-logs`(타임스탬프 + 메시지 행, 3초 폴링, 최근 200개).
- 마크다운 요약 리더는 `.markdown`(15px/1.8), 원문은 `.result-text`/`.source-text` 텍스트영역.

## Do's and Don'ts

- 색·라디우스·타이포·모션 속도·포커스 링은 `style.css` `:root` 토큰을 참조한다. 새 원시 hex를 하드코딩하지 않는다.
- 새 상태/강조는 "진한 전경 + `-100`/`-soft` 배경" 쌍을 따른다. 브랜드 채도 배경에 흰 글자를 쓰는 것은 주요 액션/실행 상태에 한정한다.
- 새 카드는 `.panel`(16px, `--line`, `--shadow-sm`)을, 새 컨트롤은 10px 라디우스와 위 버튼 변형을 재사용한다.
- 선택 입력은 네이티브 `<select>`를 새로 쓰지 말고 `Dropdown` 컴포넌트를 쓴다. 작업 목록형 정보는 표(`.job-row`)로 표현한다.
- 새 부가 정보는 모달을 만들지 말고 페이지 전환 또는 `<details>`로 표현한다(현재 UI에 모달 시스템이 없다).
- 포커스는 `:focus-visible` + `--ring`을 유지한다. 기본 outline을 되살리지 않는다.
- 진입 애니메이션을 추가할 때는 `prefers-reduced-motion: no-preference` 게이트 안에 둔다.
- 상태를 색만으로 구분하지 말고 텍스트 라벨(`statusLabels`)을 함께 쓴다.
- Pretendard 자체 호스팅을 유지한다. 외부 폰트 CDN을 추가하지 않는다.

## Responsive Behavior

`style.css`의 실제 미디어 쿼리(문서 순서):

- **≥1500px**: `main` 좌우 패딩 64px.
- **≤1180px**: `.app-shell` 210px+1fr; `.overview` 2열+파이프라인; `.workspace-grid` 1열; `.job-list` `max-height: 360px`.
- **≤900px**: `.overview` 2열(파이프라인 전폭), `.intake` 1열, `.settings-grid` 1열.
- **≤680px(모바일)**: `.app-shell` block(레일이 가로 상단 바, `border-radius: 0 0 20px 20px`),
  브랜드 서브/캡션/하단/`private-label`/`file-types`/`nav-count`/nav 아이콘 숨김, `h1` 25px,
  `.pipeline-summary`·`.stage-track` 2열, 각종 패딩 18px, 입력 16px, `.page-footer` 자간 0.
- **`prefers-reduced-motion: no-preference`**: `rise` 진입 애니메이션(0.42s, 지연 0.04~0.16s)을 켠다.

## Spacing & Sizing

현재 구현에는 **간격 토큰 스케일이 없다**(`:root`에 spacing 변수가 없음). 아래는 반복 관찰된 리터럴 값이며,
새 화면에서도 이 값들을 관례로 재사용한다.

- **카드/섹션 패딩**: 24px(대부분의 `.panel` 하위 요소), 26px(`.lms-panel`, `.intake`), 28px(`.settings-sheet`).
- **섹션 헤딩 패딩**: `24px 24px 18px`(`.section-heading`), 작업 행 `13px 24px`(`.job-row`), 리더 `0 24px`.
- **그리드 갭**: 20px(`.workspace-grid`), 18px(`.overview`, `.settings-grid`), 12px(`.pipeline-summary`, `.course-tools`), 8px(`nav`, `.segmented`, `.file-list`).
- **컨트롤 패딩**: 12px 20px(primary) · 10px 16px(secondary) · 9px 14px(ghost/danger) · 8px 10px(quiet) · 11px 12px(input) · 5px 11px(badge).
- **고정 치수**: 레일 248px(≤1180 210px), `main` max 1500px, 설정 카드 max 900px, 작업 목록 max-height 620px,
  브랜드 마크 42px(모바일 34px), 업로드 심볼 44px, 단계 마커 26px, 파일 글리프 34px.
- 입력·셀렉트는 `min-width: 0`으로 그리드 축소를 허용한다.

## Icons & Imagery

- **아이콘 라이브러리 없음.** `package.json` 의존성은 react, react-dom, react-markdown, pretendard뿐이며,
  UI는 유니코드 텍스트 글리프를 쓴다: ▤(작업), ⚙(설정), ↑(업로드), ✓(완료), ×(닫기/제거), ↗(외부/결과),
  ★(즐겨찾기), ↓(다운로드), →(제출). 크기는 주변 `font-size`를 상속한다.
- **이미지·일러스트 없음.** 웹 UI에는 이미지 자산이 없고, 폰트 파일만 정적 자산이다. 데스크톱 앱 아이콘
  (`assets/icon.*`)은 웹 범위 밖이다.
- 마크다운 요약은 `react-markdown`으로 렌더하며 raw HTML을 실행하지 않는다. 코드/인라인 코드는 `--bg` 배경 칩.

## Motion & Interaction

- **트랜지션**: 대부분의 상호작용 요소가 `transition: … var(--speed)`(=0.16s)를 쓴다. 변화 대상은 `background`,
  `border-color`, `box-shadow`, `color`, `transform`이다.
- **hover**: 버튼은 배경/테두리/색이 바뀌고, `.nav-item`/`.job-row`/`.lecture-row`는 배경 틴트, 입력은 브랜드 테두리.
- **focus**: `:focus-visible`에서 `--ring`(3px 브랜드 반투명) + 8px 라디우스, 기본 outline 제거. 드롭존은
  `label.drop-zone:focus-within`으로 링.
- **active/selected**: `.primary:active`는 1px 하강. 선택 상태는 `.job-row.selected`(brand-50 배경 + 좌측 3px 브랜드 바),
  `.nav-item.selected`(밝은 오버레이), 탭 `.active`(배경/색 반전), 단계 `.completed`/`.running`.
- **disabled**: `button:disabled { opacity: .5; cursor: default }`, `.drop-zone.disabled`도 opacity .5.
- **로딩 피드백**: 스피너/스켈레톤은 없다. 텍스트 상태("업로드 중…", "제출 중…", "결과를 불러오는 중…",
  "설정 저장 중…")과 실시간 SSE 연결 라벨로 표현한다.
- **진입 애니메이션**: `@keyframes rise`(opacity 0→1, translateY 8px→0), 0.42s
  `cubic-bezier(.22,.61,.36,1)`, `prefers-reduced-motion: no-preference`에서만, 요소별 0.04~0.16s 지연.

## Known Inconsistencies

근거와 함께 현재 구현이 서로 다른 관행을 쓰는 지점을 기록한다(정규화하지 않음).

1. **사용되지 않는 토큰/클래스.** `--violet-100`, `--accent-cream`은 정의만 있고 사용처가 없다.
   `.quiet`, `.danger`, `.field-hint` 클래스도 CSS에 있으나 TSX에서 쓰이지 않는다. (`--shadow`는 드롭다운 메뉴에서 사용된다.)
2. **토큰을 우회하는 원시 색.** 레일 그라디언트(#2a1e6e/#1b1442/#161029)와 그 위 텍스트(#ded9f6/#b9b1e6/#8b83c4/
   #cdc7ee/#cbc6ee/#948cce), hover·테두리 틴트(#ddd7f6/#e3dffb/#cfc7f2/#c6e3d3/#f2f9f5), 오류/경고/위험 텍스트
   (#8f2340/#7a5c06/#a32749)는 `:root` 토큰이 아니라 리터럴 hex다.
3. **타이포 스케일 불완전(축소됨).** `h1`/`h2`/eyebrow/지표 숫자는 `--t-2xs`~`--t-display` 토큰으로 옮겼으나,
   브랜드 마크·업로드 심볼(22px), 빈 상태 아이콘(24px), 모바일 `h1`(25px), 모바일 입력(16px), 인라인 코드(`0.92em`)는
   여전히 리터럴 px다.
4. **라디우스 예외.** 대부분 토큰이나 브랜드 마크 13px, 일부 5px, 모바일 레일 20px, 원형 50%가 리터럴이다.
5. **인라인 스타일 3곳.** `ResultPanel.tsx`(manual-note margin), `LmsImportPanel.tsx`(flex:1),
   `IntakePanel.tsx`(inline-error margin)가 클래스 대신 `style={{}}`를 쓴다.
6. **간격 토큰 부재.** spacing 스케일이 없어 여백이 리터럴 px로 흩어져 있다(위 Spacing 참고).
7. **유사 역할의 두 탭 패턴.** `.segmented`(흰 활성)와 `.artifact-tabs`(브랜드 활성)가 같은 "탭" 역할을 다른 스타일로 표현한다.
8. **배지 대비 편차.** `.status.running`만 채도 배경+흰 글자이고 나머지 상태는 틴트 배경+진한 글자다(Primary 액션 계열과 동일 규칙).
9. **`color-scheme: light` 고정.** 다크 모드 규칙은 없다.
10. **`body` 배경이 그라디언트 + 단색의 합성**이라 배경색 토큰(`--bg`)만으로는 화면 상단 색을 재현할 수 없다.
11. **`reveal` 애니메이션이 `no-preference`에만 존재**하므로, 애니메이션을 줄이는 사용자는 진입 모션이 전혀 없다(의도된 접근성 게이트이지만 동작 차이로 기록).
12. **일부 의미색 대비가 WCAG AA 미달.** `@google/design.md lint` 측정값: `--danger`(#d93a5b) on `--danger-100`(#fde7ec)
    = 3.79:1, `--warning`(#b9820a) on `--warning-100`(#fff4cc) = 3.05:1로 일반 텍스트 기준 4.5:1에 못 미친다
    (`.button-danger`, `.status` 계열 배지). `--positive`(#337357) on `--positive-100`(#dcf0e4)는 통과한다. 구현은 그대로이며,
    새 화면에서 이 색 쌍을 쓸 때는 대비를 고려해야 한다.

## Known Gaps

- 데스크톱 GUI(`src/gui`, Flet)의 시각 시스템은 이 문서 범위 밖이며 별도 토큰이 없다.
- 접근성은 lint로 측정한 색 대비 2건(위 Known Inconsistencies 12)만 확인했다. 그 밖의 WCAG 등급·대비는 측정·기록된 값이 없어 단정하지 않는다.
- 아이콘 세트의 광학 크기·정렬 규칙은 텍스트 글리프라 명문화된 기준이 없다.
- 다크 테마, 모달/드로어 시스템, 스켈레톤 로딩은 현재 존재하지 않는다.
