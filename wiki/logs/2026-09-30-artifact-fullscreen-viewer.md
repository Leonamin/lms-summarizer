---
type: Log
title: "산출물 풀스크린 뷰어와 카드 스크롤"
description: "작업 상세의 STT·요약 본문 높이 제한과 라이트박스형 전체 보기 다이얼로그 추가"
timestamp: 2026-09-30
okf_version: "0.1"
---

# 산출물 풀스크린 뷰어

## 배경

작업 상세 카드의 요약(마크다운)과 STT 원문이 길어지면 카드가 수직으로 계속 길어져 가독성이 떨어졌다.
요약 마크다운은 높이 제한 없이 렌더됐고(`.markdown`), 원문은 `rows={12}` textarea로 카드가 커졌다.

## 구현

- **공용 본문 렌더러** `frontend/src/components/ArtifactBody.tsx` — `summary`는 마크다운, 그 외는 선택 가능한
  원문 textarea. 카드와 뷰어가 같은 렌더러를 공유.
- **카드 내부 제한 스크롤**: `.reader-body { max-height: min(46vh, 520px); overflow: auto }`,
  `.reader .source-text { height: 340px }`.
- **풀스크린 뷰어**: 네이티브 `<dialog class="viewer-dialog">` + `::backdrop` 라이트박스.
  - `showModal()`로 **포커스 트랩·Esc 닫기**를 브라우저가 처리, 백드롭 클릭 닫기.
  - 리더 툴바에 `전체 보기` 버튼, 뷰어 상단에 `복사·다운로드·닫기`.
  - 열림/닫힘 상태 관리, 표시 아티팩트가 바뀌면 자동 닫힘.
- 복사 로직을 `navigator.clipboard` + 레거시 textarea 폴백으로 정리해 카드/뷰어가 공용 사용.

## 검증

- 프런트엔드 빌드 통과, 배포 healthy.
- 실 배포 UI에서 확인: `.reader-body` max-height 265px·scrollable=true, `전체 보기` →
  `<dialog>` open=true·`:modal`, Esc → open=false.
