---
type: Log
title: "SenseVoice vs faster-whisper CPU 벤치마크 — 속도·한국어 정확도"
description: "배포된 선대 강의 3편으로 SenseVoiceSmall(CPU·int8)과 faster-whisper large-v3-turbo를 비교. SenseVoice는 약 10배 빠르지만 한국어 정확도와 영어·외래어 보존이 크게 낮아 기본 엔진 교체는 부적합하다."
timestamp: 2026-10-01
okf_version: "0.1"
---

# SenseVoice vs faster-whisper CPU 벤치마크

## 질문

Whisper(faster-whisper) 대신 **SenseVoice**를 STT 대안으로 쓰면 CPU 환경에서

1. 얼마나 빨라지는가?
2. 한국어 정확도(강의 속 영어·외래어 포함)는 유지되는가?

## 결론 (한 줄)

**SenseVoiceSmall(int8·CPU)은 faster-whisper `large-v3-turbo`보다 약 10배 빠르지만, 한국어 정확도가 유의미하게 낮고 영어·외래어를 라틴 문자로 보존하지 못하므로 기본 엔진을 교체할 근거는 없다.** CPU 속도가 급하면 SenseVoice보다 `faster-whisper small`이 더 나은 절충이다.

| 항목 | faster-whisper large-v3-turbo (현행) | SenseVoiceSmall int8 | 판정 |
|---|---|---|---|
| 속도 (3편 합계, CPU 8스레드) | 728s / 6.9× 실시간 | 72.6s / 68.8× 실시간 | SenseVoice **약 10배 빠름** |
| CER (Whisper 전사본 기준) | 0.067 / 0.002 / 0.090 | 0.324 / 0.373 / 0.322 | SenseVoice **약 4~200배 나쁨** |
| 라틴 토큰(AX·LU·matrix 등) | 72 / 175 / 336 | 1 / 1 / 0 | SenseVoice **영어 음차 붕괴** |
| 띄어쓰기 아티팩트 | 7 / 8 / 45 | 82 / 72 / 136 | SenseVoice **약 3~10배 많음** |

## 방법

- **환경**: AMD Ryzen 7 8745HS(8C/16T, AVX512+VNNI), 26GB RAM, **CUDA 없음** → 순수 CPU
- **격리 실행**: 컨테이너 밖 독립 venv(`/tmp/opencode/stt-bench/.venv`, Python 3.11), 프로덕션 코드·컨테이너 무변경
- **공정성**: 두 엔진 모두 `num_threads=8`, int8, `nice -n 10`(웹 컨테이너 여유 확보)
- **faster-whisper 설정(프로덕션과 동일)**: `device=cpu`, `compute_type=int8`, `beam_size=1`, `vad_filter=True`, `language=ko`, `initial_prompt="한국어 강의입니다."`
- **SenseVoice 설정**: `sherpa-onnx` int8 ONNX(2024-07-17 변환), silero VAD로 분절 후 세그먼트별 디코딩, `use_itn=True`, `language=ko`
- **입력**: 배포된 선대 4장 강의의 STT 단계 산출물 `audio.wav`(16kHz mono s16)
- **정확도 기준(reference)**: 현재 프로덕션 전사본(faster-whisper large-v3-turbo)

| 태그 | 길이 | 내용 |
|---|---|---|
| 선대_4_1 | 1222.6s (20분) | 4장 역행렬·LU |
| 선대_4_2 | 1113.2s (18분) | 역행렬의 활용 |
| 선대_4_3 | 2661.6s (44분) | LU 분해·삼각행렬 |

## 결과

### 1) 속도

| 태그 | 엔진/모델 | 오디오(s) | 로드(s) | 추론(s) | RTF | 배속 | 세그먼트 | 글자 |
|---|---|---|---|---|---|---|---|---|
| 선대_4_1 | fw large-v3-turbo | 1222.6 | 3.09 | 174.03 | 0.1423 | 7.03× | 489 | 5,958 |
| 선대_4_1 | fw small | 1222.6 | 209.13\* | 85.18 | 0.0697 | 14.35× | 333 | 5,224 |
| 선대_4_1 | SenseVoice ko | 1222.6 | 0.81 | 17.33 | 0.0142 | 70.55× | 273 | 5,381 |
| 선대_4_1 | SenseVoice ko (no-itn) | 1222.6 | 0.76 | 16.66 | 0.0136 | 73.38× | 273 | 5,083 |
| 선대_4_1 | SenseVoice auto | 1222.6 | 0.75 | 16.76 | 0.0137 | 72.95× | 273 | 5,302 |
| 선대_4_1 | SenseVoice 2025-09-09 | 1222.6 | 0.73 | 16.55 | 0.0135 | 73.87× | 273 | 1,114 |
| 선대_4_2 | fw large-v3-turbo | 1113.2 | 2.44 | 139.12 | 0.1250 | 8.00× | 399 | 5,900 |
| 선대_4_2 | SenseVoice ko | 1113.2 | 0.75 | 16.14 | 0.0145 | 68.97× | 229 | 5,242 |
| 선대_4_3 | fw large-v3-turbo | 2661.6 | 2.41 | 415.07 | 0.1559 | 6.41× | 947 | 12,342 |
| 선대_4_3 | SenseVoice ko | 2661.6 | 0.72 | 39.14 | 0.0147 | 68.00× | 654 | 11,758 |

\* fw small의 로드 시간은 최초 모델 다운로드를 포함한 값(추론 시간에는 영향 없음).

- 3편 합계: fw large-v3-turbo **728.2s (6.9×)**, SenseVoice **72.6s (68.8×)** → **약 10.0배** 차이.
- SenseVoice의 RTF는 오디오 길이와 무관하게 ~0.014로 안정적(비자기회귀 CTC).
- 모델 로드는 두 엔진 모두 미미(fw 2.4~3.1s, SV 0.7~0.8s)하고 파이프라인은 모델을 재사용하므로 실질 영향 없음.

### 2) 정확도 (기준: 프로덕션 Whisper 전사본)

| 태그 | 엔진/모델 | CER | WER |
|---|---|---|---|
| 선대_4_1 | fw large-v3-turbo (자기일치) | 0.0669 | 0.0966 |
| 선대_4_1 | fw small | 0.2863 | 0.4507 |
| 선대_4_1 | SenseVoice ko | **0.3242** | 0.7205 |
| 선대_4_1 | SenseVoice ko (no-itn) | 0.3225 | 0.7281 |
| 선대_4_1 | SenseVoice auto | 0.3518 | 0.7322 |
| 선대_4_1 | SenseVoice 2025-09-09 | 0.9756 | 0.9897 |
| 선대_4_2 | fw large-v3-turbo (자기일치) | 0.0015 | 0.0044 |
| 선대_4_2 | SenseVoice ko | **0.3725** | 0.7102 |
| 선대_4_3 | fw large-v3-turbo (자기일치) | 0.0898 | 0.1333 |
| 선대_4_3 | SenseVoice ko | **0.3220** | 0.6699 |

- 한국어는 음절 단위 **CER**이 더 유효하다. SenseVoice는 기준 대비 **CER 0.32~0.37**(약 1/3 음절 불일치).
- `large-v3-turbo`의 자기일치 CER은 4_2에서 0.0015로 사실상 동일(= 기준 전사본이 같은 모델·설정 산출). 4_1(0.067)·4_3(0.090)은 프로덕션 후처리(`clean_transcript` 반복 제거)와 벤치마크 원출력의 차이에서 비롯된 것으로, SenseVoice의 0.32와는 자릿수가 다르다.

### 3) 영어·외래어 처리 (라틴 문자 보존)

각 전사본에서 뽑은 라틴 알파벳 토큰 수:

| 태그 | fw large-v3-turbo | SenseVoice ko | SenseVoice auto |
|---|---|---|---|
| 선대_4_1 | **72** (AX, B, LU, echelon, reduced, raw …) | **1** (`yeah.`) | 19 (대부분 `oh`, `you`, `yeah` 등 오검출) |
| 선대_4_2 | **175** (matrix, inverse, solution, trivial, homogeneous …) | **1** | – |
| 선대_4_3 | **336** (LU, decomposition, identity, triangular, upper, augmented …) | **0** | – |

- SenseVoice(`language=ko`)는 `AX`→`에이엑스`, `A`→`에이`, `X`→`엑스`처럼 **영어를 한글 음차로 붕괴**시킨다. 라틴 문자 보존율이 사실상 0이다.
- `language=auto`는 라틴 토큰이 19개로 늘지만 실제 용어가 아니라 `oh/you/yeah` 같은 **허위 영어 삽입**이며, CER은 오히려 악화(0.324→0.352).

### 4) 도메인 용어 정확도 (선대_4_1)

| 용어 | 기준 | fw-turbo | SenseVoice |
|---|---|---|---|
| 행렬 | 63 | 65 | 40 |
| 역행렬 | 15 | 19 | 6 |
| 선형대수학 | 2 | 2 | 0 |
| 가역 | 4 | 4 | 2 |
| LU | 1 | 1 | 0 |
| echelon | 1 | 2 | 0 |

- SenseVoice는 핵심 용어를 놓치거나 변형한다: `행렬`→`갱렬`, `역행렬`→`행적행렬`/`역균 요리리`, `선형대수학`→`천영대 수학`, `연립선형방정식`→`열리손님의 방식식`.
- `행렬` 언급량 자체가 65 → 40으로 줄어(반복·오인식으로 누락) 내용 손실을 시사한다.

### 5) 한글 음차(영어→한글) 탐지 (선대_4_1)

| 전사본 | 음차 토큰 |
|---|---|
| 기준 | 에이 1, 매트릭스 16, 인버스 4, 디컴포지션 1, 아이덴티티 11 |
| fw-turbo | 매트릭스 16, 인버스 4, 디컴포지션 1, 아이덴티티 11 (`A`/`X`/`LU`는 라틴 유지) |
| SenseVoice | **에이엑스 1, 에이 16, 엑스 3**, 매트릭스 11, 인버스 2, 아이덴티티 1 |

- Whisper도 `아이덴티티`처럼 관용 표기는 한글로 쓰지만, 수식·기호(`A`, `X`, `LU`)는 라틴 문자로 유지한다. SenseVoice는 이를 구분하지 못한다.

### 6) 아티팩트

- **띄어쓰기**(단일 음절 + 조사 분리 패턴 수): fw 7 / 8 / 45, SenseVoice **82 / 72 / 136** → 약 3~10배 많음. 예: `구하 는지 뿐 만 아 니라`.
- **반복(4-gram 최대 중복)**: fw 4_3은 32회(Whisper 특유의 무한 반복 hallucination), SenseVoice는 2~3회로 적음 → SenseVoice가 반복에는 오히려 강함.

### 7) 변형 실험

- **ITN off**(`no-itn`): 구두점이 사라져(`.`→공백) 가독성 저하. 단어 오류는 동일(CER 0.3225).
- **language auto**: CER 악화(0.352), 허위 영어 삽입.
- **2025-09-09 변환 모델**: 한국어에서 **사용 불가**. 한자·깨진 토큰이 섞이고 글자 수가 1,114로 급감(정상 ~5,381). 해당 변환은 광둥어 파인튜닝 기반이라 한국어에 부적합.
- **VAD 없음(전체 1청크)**: 실험 중단으로 미완료(20분 단일 청크는 비현실적·과도한 연산 우려). VAD 분절 사용을 전제로 한다.

### 8) 불일치 예시 (fw-turbo vs SenseVoice)

| 구간 | faster-whisper | SenseVoice |
|---|---|---|
| 4_1 도입 | 선형대수학에서 **AX는 B**. 연립선형 방정식을 푸는 것은 … | **천영대 수학**에서. **에이엑스는 비**. 연립선형 방정식을 푸는 것은? … |
| 4_1 | 이 매트릭스 A의 **역행렬**이라는 개념은 … | 이 매트릭스. **갱렬**이라는 개념은 … (`갱렬`=행렬 오인식) |
| 4_2 도입 | 4.2 … 역행렬의 활용입니다. | 네4점이 … **역균 요리리 활용**입니다. |
| 4_2 | 역행렬과 **연립선형방정식**의 해라는 … | 역행렬과 **연립선년방정시** 해라는 … |

## 해석

- **속도 가설은 사실이다.** SenseVoice는 비자기회귀 CTC라 CPU에서 Whisper 대비 ~10배 빠르다. 이 부분은 명확한 장점이다.
- **그러나 이 강의 도메인에서는 정확도 손실이 크다.** 특히 한국어 강의에 섞인 수식 기호·영어 용어(AX, LU, matrix, echelon, homogeneous …)를 라틴 문자로 남기지 못하는 문제는 선형대수·공학 강의에서 치명적이다. 요약 단계 프롬프트의 STT 보정 지침이 음차(`에이엑스`) 정도는 되돌릴 수 있어도, `갱렬`/`천영대 수학`/`열리손님` 같은 붕괴는 복원이 어렵다.
- **속도가 정말 필요하면 대안은 SenseVoice가 아니라 `faster-whisper small`이다.** 14.35×로 SenseVoice(70×)보다 느리지만, CER(4_1 0.286 vs 0.324)이 더 낮고 **라틴 토큰 73개로 영어를 그대로 보존**한다. "정확도 손실 없는 2배 가속"에 가깝다.

## 권장

1. **기본 엔진은 `faster-whisper large-v3-turbo` 유지.**
2. SenseVoice를 굳이 도입한다면 **"초고속·정확도 낮음" 별도 옵션**으로만, 그리고 영어 없는 순수 한국어 콘텐츠로 한정. 기본값으로 두지 않는다.
3. CPU 저사양 대안이 필요하면 **`faster-whisper small`**을 우선 검토(SenseVoice보다 정확도 우위, 2배 가속).
4. 도입 전 최종 검증으로 **동일 강의의 요약 산출물(Gemini) A/B**를 권장 — 전사 오류가 최종 요약 품질에 실제로 영향을 주는지 확인해야 한다(미실시).

## 한계

- 사람 정답 전사(ground truth)가 없어 기준은 프로덕션 Whisper 전사본이다. CER은 "Whisper와 얼마나 다른가"에 가깝다. 다만 라틴 토큰·도메인 용어·음차 지표는 방향이 명확해 결론을 뒤집기 어렵다.
- 강의 3편, 단일 CPU, VAD·int8 설정에 한정된 결과다. GPU나 다른 양자화에서는 속도 비가 달라질 수 있다.
- 요약 단계(AI 보정·요약)까지의 최종 영향은 검증하지 않았다.

## 재현

하네스는 `/tmp/opencode/stt-bench/`에 있다(휘발성).

```
bench.py         # 엔진별 실행 + results.jsonl 기록
analyze.py       # 속도표 / CER·WER / 영어 토큰 / 불일치 구간
deep_analyze.py  # 도메인 용어 / 띄어쓰기·반복 아티팩트 / 한글 음차
run_all.sh       # 전체 매트릭스
```

```bash
cd /tmp/opencode/stt-bench
bash run_all.sh
.venv/bin/python analyze.py
.venv/bin/python deep_analyze.py
```

## 참고

- SenseVoiceSmall: 중국어·광둥어·영어·일본어·**한국어** 지원, 비자기회귀라 저지연([FunAudioLLM/SenseVoiceSmall](https://huggingface.co/FunAudioLLM/SenseVoiceSmall)).
- sherpa-onnx 변환 모델: `sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17`(사용), `...-int8-2025-09-09`(한국어 부적합).
