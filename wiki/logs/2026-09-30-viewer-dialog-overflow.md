---
type: Log
title: "풀스크린 뷰어 닫힘 상태 오버플로우 수정"
description: "닫힌 <dialog>가 display:flex로 남아 페이지 가로 오버플로우를 만들던 문제 수정"
timestamp: 2026-09-30
okf_version: "0.1"
---

# 풀스크린 뷰어 오버플로우

## 증상

작업 상세에서 페이지에 **가로 오버플로우**가 생기고 마크다운 내용이 화면 오른쪽으로 밀려 잘렸다. 뷰어를 열지 않은 상태에서도 발생했다.

## 원인

`.viewer-dialog { display: flex }`가 브라우저 기본 스타일 `dialog:not([open]) { display: none }`을 덮어썼다. 그래서 **닫힌 `<dialog>`가 `position: absolute` 1100px 상자로 레이아웃에 남아** 페이지 스크롤 폭을 늘렸다. `showModal()`로 열면 `:modal`의 fixed/중앙 정렬이 적용돼 정상이지만, 닫힌 뒤에도 상자가 남는 것이 문제였다.

## 조치

- `.viewer-dialog`에서 `display: flex` 제거, **`.viewer-dialog[open]`에만** `display: flex` 적용 → 닫히면 UA 규칙으로 `display: none`.
- 보강: `.markdown .katex-display { max-width: 100%; overflow-x: auto; overflow-y: hidden }` — 넓은 블록 수식이 카드를 가로로 밀지 않도록.

## 검증

- 배포 UI: 뷰어 닫힘 시 `dialog display: none`, `pageScrollWidth == viewportWidth`.
- `전체 보기` 시 `open=true`·`:modal=true`·좌우 90/1190(중앙 정렬), 페이지 오버플로우 없음.
- Esc 닫힘 후 오버플로우 없음. 프런트엔드 빌드 통과.
