import json
import re
import time
from abc import ABC, abstractmethod
import os
import requests
from src.user_setting import UserSetting

# https://developers.rtzr.ai/docs/stt-file/


def clean_transcript(text: str, repeat_threshold: int = 4) -> str:
    """반복 구문 제거 (whisper 무한 루프 hallucination 후처리)

    같은 구문이 repeat_threshold번 이상 연속 반복되면 1개로 축약.
    repeat_threshold <= 0 이면 비활성화.
    """
    if repeat_threshold <= 0:
        return text
    pattern = r'(.+?)\1{' + str(repeat_threshold) + r',}'
    return re.sub(pattern, r'\1', text)


def transcribe_audio_to_text(audio_path: str, txt_path: str, engine="whisper-cpp", model_name="base", params=None, on_log=None):
    """오디오/비디오 파일을 텍스트로 변환"""
    _log = on_log or (lambda msg: None)
    params = dict(params or {})
    repeat_threshold = int(params.pop("repeat_threshold", 4))

    if engine == "whisper-cpp":
        transcriber = WhisperCppTranscriber(model_name=model_name, params=params, on_log=on_log)
    elif engine == "faster-whisper":
        device = params.pop("device", "auto")
        compute_type = params.pop("compute_type", "auto")
        transcriber = FasterWhisperTranscriber(
            model_name=model_name, device=device, compute_type=compute_type,
            params=params, on_log=on_log,
        )
    elif engine == "returnzero":
        transcriber = ReturnZeroTranscriber()
    else:
        raise ValueError("지원하지 않는 엔진입니다")

    transcriber.transcribe(audio_path, txt_path)

    # 반복 구문 후처리 (양쪽 엔진 공통)
    if repeat_threshold > 0 and os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            raw = f.read()
        cleaned = clean_transcript(raw, repeat_threshold)
        if cleaned != raw:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(cleaned)
            _log(f"[후처리] 반복 구문 제거 완료 (임계값: {repeat_threshold}회)")


# 하위 호환성 유지
transcribe_wav_to_text = transcribe_audio_to_text


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, txt_path: str):
        pass


class WhisperCppTranscriber(Transcriber):
    def __init__(self, model_name="base", language="ko", params=None, on_log=None):
        from pywhispercpp.model import Model
        from src.audio_pipeline.model_manager import resolve_for_transcriber
        import sys

        self._language = language
        self._on_log = on_log or (lambda msg: None)
        # suppress_non_speech_tokens, repeat_threshold은 pywhispercpp C 바인딩에서 미지원 → 제거
        _exclude = {"suppress_non_speech_tokens", "repeat_threshold"}
        sanitized = {k: v for k, v in (params or {}).items() if k not in _exclude}
        self._params = sanitized
        load_start = time.time()

        # .app 번들 내부의 모델 확인
        if getattr(sys, 'frozen', False):
            model_path = os.path.join(sys._MEIPASS, 'whisper_models', f'ggml-{model_name}.bin')
            if os.path.exists(model_path):
                print(f"[INFO] 번들된 whisper.cpp 모델 사용: {model_path}")
                self.model = Model(model_path)
                self.model_load_sec = time.time() - load_start
                print(f"[INFO] 모델 로드 시간: {self.model_load_sec:.1f}초")
                return

        # model_key → (custom_path, builtin_name) 결정
        custom_path, builtin_name = resolve_for_transcriber(model_name)
        if custom_path:
            print(f"[INFO] 커스텀 whisper.cpp 모델 로드: {os.path.basename(custom_path)}")
            self.model = Model(custom_path)
        else:
            print(f"[INFO] whisper.cpp 내장 모델 로드: {builtin_name}")
            self.model = Model(builtin_name)

        self.model_load_sec = time.time() - load_start
        print(f"[INFO] 모델 로드 시간: {self.model_load_sec:.1f}초")

    def transcribe(self, audio_path: str, txt_path: str):
        import os
        import re
        import threading

        # C 라이브러리의 stdout(fd 1)을 파이프로 리다이렉트해 Progress: N% 파싱
        old_fd = os.dup(1)
        r_fd, w_fd = os.pipe()
        os.dup2(w_fd, 1)
        os.close(w_fd)

        last_pct = [-1]

        def _read_stdout():
            try:
                with os.fdopen(r_fd, "r", encoding="utf-8", errors="replace") as pipe:
                    for line in pipe:
                        m = re.search(r"Progress:\s*(\d+)%", line)
                        if m:
                            pct = int(m.group(1))
                            if pct != last_pct[0] and pct % 10 == 0:
                                last_pct[0] = pct
                                self._on_log(f"  STT 진행: {pct}%")
            except Exception:
                pass

        reader = threading.Thread(target=_read_stdout, daemon=True)
        reader.start()

        try:
            transcribe_start = time.time()
            segments = self.model.transcribe(audio_path, language=self._language, **self._params)
            text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.last_transcribe_sec = time.time() - transcribe_start
        except Exception as e:
            raise e
        finally:
            # 파이프 닫기 → reader 스레드 종료
            os.dup2(old_fd, 1)
            os.close(old_fd)
            reader.join(timeout=5)

        self._on_log(f"[whisper.cpp] 변환 완료: {txt_path}")
        self._on_log(f"[whisper.cpp] STT 소요 시간: {self.last_transcribe_sec:.1f}초")
        if self._params:
            self._on_log(f"[whisper.cpp] 적용된 파라미터: {self._params}")


class FasterWhisperTranscriber(Transcriber):
    def __init__(self, model_name="large-v3-turbo", device="auto", compute_type="auto", params=None, on_log=None):
        from faster_whisper import WhisperModel
        self._on_log = on_log or (lambda msg: None)
        self._language = (params or {}).get("language", "ko")
        self._initial_prompt = (params or {}).get("initial_prompt", "한국어 강의입니다.")
        self._vad_filter = bool((params or {}).get("vad_filter", True))

        self._on_log(f"[faster-whisper] 모델 로드 중: {model_name} (device={device})")
        load_start = time.time()
        self.model = WhisperModel(model_name, device=device, compute_type=compute_type)
        self.model_load_sec = time.time() - load_start
        self._on_log(f"[faster-whisper] 모델 로드: {self.model_load_sec:.1f}초")

    def transcribe(self, audio_path: str, txt_path: str):
        transcribe_start = time.time()
        segments, info = self.model.transcribe(
            audio_path,
            language=self._language,
            initial_prompt=self._initial_prompt,
            vad_filter=self._vad_filter,
        )
        text_parts = []
        for i, seg in enumerate(segments):
            if seg.text.strip():
                text_parts.append(seg.text.strip())
            if (i + 1) % 50 == 0:
                self._on_log(f"  처리 중... {i+1} 세그먼트")

        text = " ".join(text_parts)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        elapsed = time.time() - transcribe_start
        self._on_log(f"[faster-whisper] 변환 완료: {txt_path}")
        self._on_log(f"[faster-whisper] 소요 시간: {elapsed:.1f}초")
        self._on_log(f"[faster-whisper] 감지 언어: {info.language} ({info.language_probability:.0%})")


class ReturnZeroTranscriber(Transcriber):
    def __init__(self):
        user_setting = UserSetting()
        self.client_id = user_setting.RETURNZERO_CLIENT_ID
        self.client_secret = user_setting.RETURNZERO_CLIENT_SECRET
        self.token = self._authenticate()

    def _authenticate(self) -> str:
        # 인증 토큰 발급
        resp = requests.post(
            "https://openapi.vito.ai/v1/authenticate",
            data={"client_id": self.client_id, "client_secret": self.client_secret},
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        print("[ReturnZero] 인증 토큰 발급 성공")
        return token

    def _submit_job(self, wav_path: str) -> str:
        # 변환 요청
        with open(wav_path, "rb") as f:
            files = {
                "file": (os.path.basename(wav_path), f),
                "config": (
                    None,
                    '{"model_name":"whisper","language":"ko"}',
                    "application/json",
                ),
            }
            headers = {
                "Authorization": f"Bearer {self.token}",
                "accept": "application/json",
            }
            response = requests.post(
                "https://openapi.vito.ai/v1/transcribe",
                headers=headers,
                files=files,
            )
        response.raise_for_status()
        return response.json()["id"]  # 이게 transcribe_id

    def _poll_until_complete(self, transcribe_id: str, timeout=180, interval=5) -> dict:
        # 변환 완료 대기
        url = f"https://openapi.vito.ai/v1/transcribe/{transcribe_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        start = time.time()

        while time.time() - start < timeout:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")

            print(f"[Polling] 현재 상태: {status}")
            if status == "completed":
                return data
            elif status == "failed":
                raise RuntimeError(f"[ERROR] 변환 실패: {data.get('error')}")
            time.sleep(interval)

        raise TimeoutError("음성 변환 시간 초과")

    def _parse_text(self, data: dict) -> str:
        # 분리된 결과값을 합치기
        utterances = data.get("results", {}).get("utterances", [])
        messages = [utterance.get("msg", "") for utterance in utterances]
        return " ".join(messages)

    def transcribe(self, wav_path: str, txt_path: str):
        try:
            transcribe_id = self._submit_job(wav_path)
            data = self._poll_until_complete(transcribe_id)
            text = self._parse_text(data)

            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)

            txt_raw_path = txt_path.replace(".txt", "_raw_rtzr.txt")
            with open(txt_raw_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(data, indent=4))

            print(f"[ReturnZero] 텍스트 변환 완료: {txt_path}")

        except Exception as e:
            print(f"[ERROR] 변환 실패: {e}")
            raise e
