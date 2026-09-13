---
type: Log
title: "Settings Dialog Categories and Password Persistence"
description: "설정 다이얼로그 카테고리 내비게이션 개편 + 비밀번호 평문 저장"
timestamp: 2026-09-14
okf_version: "0.1"
---

# Settings Dialog Categories and Password Persistence

## 1. 설정 다이얼로그 카테고리 내비게이션

### 배경

기존 설정 다이얼로그가 요약 프롬프트 + Chrome 경로 + 고급 설정을 하나의 수직 스크롤에 넣어 길고 찾기 어려웠음. macOS 시스템 설정처럼 카테고리로 분리하기로 결정.

### 구현

`SettingsDialog` 클래스로 재작성 (`gui/views/settings_view.py`):

- 좌측 카테고리 목록 / 우측 상세 구조 (640×460)
- 카테고리 3개:
  - **요약 프롬프트**: 모드, 강의 분야, 직접 입력, 프롬프트 프리뷰, 기본값 복원
  - **브라우저**: Chrome 경로, 찾아보기, 자동 감지 경로
  - **동작**: 디버그 모드, 완료 후 폴더 자동 열기 (토글 스위치)
- 카테고리 전환 시 좌측 버튼 스타일 갱신 + 우측 콘텐츠 visible 토글

## 2. 비밀번호 평문 저장

### 배경

학번은 저장되지만 비밀번호는 매번 재입력 필요. 사용자가 평문 저장을 선택함.

### 구현

- `_PERSISTABLE_FIELDS`에 `password` 추가 (`gui/core/file_manager.py`)
- `settings.json`에 학번과 함께 저장, 앱 시작 시 자동 복원
- README 문구 갱신: "비밀번호는 로컬 설정 파일에 저장되며 외부로 전송되지 않습니다"

### 보안 참고

- settings.json은 사용자 AppData 디렉토리에 위치 (프로젝트 외부)
- 평문이므로 파일 접근 권한이 있는 로컬 사용자/프로그램은 열람 가능
- OS 자격증명 저장(DPAPI/Keychain)은 추후 전환 가능한 구조 (저장/복원이 file_manager에 집중됨)

## 검증

- 임시 디렉토리에서 save/load 라운드트립 테스트 통과 (student_id + password)
- SettingsDialog import 및 카테고리 전환 로직 확인
