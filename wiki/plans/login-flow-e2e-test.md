---
type: Plan
title: "새 로그인 플로우 실환경 E2E 테스트"
description: "재구현된 숭실대 SSO 로그인 플로우의 브라우저 실환경 검증"
status: in-progress
priority: p1
created: 2026-09-13
okf_version: "0.1"
---

# 새 로그인 플로우 실환경 E2E 테스트

## 배경

숭실대 LMS 로그인 사이트 변경에 따라 `src/video_pipeline/login.py`를 3단계 조건부 플로우로 재구현함
(discovery `.btn-ssu-main` → gw.php `.login_btn a` 통합 로그인 → smartid 폼).
실제 페이지 구조 기반으로 작성했으나 브라우저 E2E 검증이 남아 있음.

## 체크리스트

- [ ] 실제 LMS에서 브라우저 로그인 E2E 테스트 (headless=False 실행 필요)
