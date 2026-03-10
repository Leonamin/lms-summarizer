import json
import time
from faster_whisper import WhisperModel
from abc import ABC, abstractmethod
import os
import requests
from src.user_setting import UserSetting

# https://developers.rtzr.ai/docs/stt-file/


def transcribe_audio_to_text(audio_path: str, txt_path: str, engine="whisper"):
    """오디오/비디오 파일을 텍스트로 변환 (MP4 직접 입력 지원)"""
    if engine == "whisper":
        transcriber = WhisperTranscriber()
    elif engine == "returnzero":
        transcriber = ReturnZeroTranscriber()
    else:
        raise ValueError("지원하지 않는 엔진입니다")

    transcriber.transcribe(audio_path, txt_path)


# 하위 호환성 유지
transcribe_wav_to_text = transcribe_audio_to_text


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, txt_path: str):
        pass


class WhisperTranscriber(Transcriber):
    def __init__(self, model_name="base"):
        import sys

        load_start = time.time()

        # .app 번들 내부의 모델 확인
        if getattr(sys, 'frozen', False):
            model_path = os.path.join(sys._MEIPASS, 'whisper_models', model_name)
            if os.path.exists(model_path):
                print(f"[INFO] 번들된 Whisper 모델 사용: {model_path}")
                self.model = WhisperModel(model_path, compute_type="int8")
                self.model_load_sec = time.time() - load_start
                print(f"[INFO] 모델 로드 시간: {self.model_load_sec:.1f}초")
                return

        # 기본 경로에서 모델 로드 (자동 다운로드)
        print(f"[INFO] Whisper 모델 로드 중: {model_name}")
        self.model = WhisperModel(model_name, compute_type="int8")
        self.model_load_sec = time.time() - load_start
        print(f"[INFO] 모델 로드 시간: {self.model_load_sec:.1f}초")

    def transcribe(self, audio_path: str, txt_path: str):
        try:
            transcribe_start = time.time()
            segments, info = self.model.transcribe(audio_path)
            text = " ".join(segment.text for segment in segments)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.last_transcribe_sec = time.time() - transcribe_start
            print(f"[Whisper] 변환 완료 (언어: {info.language}, 확률: {info.language_probability:.2f}): {txt_path}")
            print(f"[Whisper] STT 소요 시간: {self.last_transcribe_sec:.1f}초")
        except Exception as e:
            print(f"[ERROR] 변환 실패: {e}")
            raise e


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
