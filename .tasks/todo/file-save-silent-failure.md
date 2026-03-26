---
id: file-save-silent-failure
title: 영상/요약 파일 저장 실패가 성공으로 표시되는 문제
labels: [bug]
priority: p1
created: 2026-03-26
---

# 영상/요약 파일 저장 실패가 성공으로 표시되는 문제

## 현상
- Mac 사용자가 영상/요약 파일이 전혀 저장되지 않는다고 보고
- 에러 없이 "작업 성공"으로 표시됨

## 원인 분석
파이프라인 각 단계에서 **예외를 catch하고 로그만 남긴 뒤 계속 진행**하여, 파일이 실제로 생성되지 않아도 성공으로 처리됨.

### 핵심 문제들

1. **디렉토리 미생성**: 파일 쓰기 전 `os.makedirs()` 호출 없음
   - `src/audio_pipeline/converter.py`: `av.open(wav_path, mode='w')` 전에 부모 디렉토리 미생성
   - `src/audio_pipeline/pipeline.py` (line ~35): txt 파일 저장 전 디렉토리 미생성
   - `src/summarize_pipeline/pipeline.py` (line ~31): 요약 파일 저장 전 디렉토리 미생성

2. **예외 삼킴 (Exception Swallowing)**:
   - `src/gui/workers/processing_worker.py` (line ~417): 요약 실패 시 catch → 로그만 → 계속 진행
   - `src/gui/workers/processing_worker.py` (line ~344): WAV 변환 실패 시 catch → 로그만 → 계속 진행

3. **파일 존재 검증 없음**: 각 단계가 "저장할 경로"를 반환하지만 실제 파일 존재 여부 미확인

4. **성공 판정 기준 부재**: `processing_worker.py` (line ~140-144)에서 파일 검증 없이 성공 emit

## 체크리스트
- [ ] 모든 파일 쓰기 위치에 `os.makedirs(parent, exist_ok=True)` 추가
- [ ] 파일 쓰기 후 `os.path.exists()` 검증 추가
- [ ] 개별 단계 실패 시 전체 결과에 실패 카운트 반영 (부분 성공 처리)
- [ ] 최종 성공 메시지에 실제 저장된 파일 수 표시
- [ ] Mac 환경에서 경로 권한/특수문자 관련 엣지케이스 확인
