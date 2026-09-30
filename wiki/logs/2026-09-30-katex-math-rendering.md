---
type: Log
title: "마크다운 뷰어 LaTeX(KaTeX) 렌더링"
description: "요약 마크다운의 $...$ 수식이 리터럴로 보이던 문제를 remark-math·rehype-katex로 해결"
timestamp: 2026-09-30
okf_version: "0.1"
---

# 마크다운 뷰어 KaTeX 렌더링

## 증상

요약 마크다운의 `$A$`, `$AX=B$`, `$A^{-1}$` 같은 LaTeX가 렌더되지 않고 **리터럴 `$...$` 텍스트**로 표시됐다.

## 원인

`react-markdown`을 수식 플러그인 없이 기본 설정으로만 사용했다.

## 조치

- 의존성 추가: `remark-math`, `rehype-katex`, `katex`.
- `frontend/src/components/ArtifactBody.tsx`의 `ReactMarkdown`에
  `remarkPlugins={[remarkMath]}`, `rehypePlugins={[rehypeKatex]}`와 `katex/dist/katex.min.css` 적용.
- 카드와 풀스크린 뷰어가 같은 `ArtifactBody`를 공유하므로 양쪽 모두 렌더링된다.

## 검증

- 배포 UI의 수식 포함 요약에서 `.katex` 노드 41개, `.katex-error` 0개, 리터럴 `$...$` 잔여 0.
- 프런트엔드 빌드 통과(KaTeX 폰트 자동 번들).

## 비용·후속

- KaTeX 번들로 JS가 411KB → 690KB(gzip 212KB)로 증가. 필요 시 뷰어에서 동적 import로 지연 로딩 가능.
