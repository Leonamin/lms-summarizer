import json
import re
import subprocess
import sys
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


def transcribe_audio_to_text(
    audio_path: str,
    txt_path: str,
    engine="faster-whisper",
    model_name="large-v3-turbo",
    params=None,
    on_log=None,
    _reuse_transcriber=None,
):
    """오디오/비디오 파일을 텍스트로 변환.

    Args:
        _reuse_transcriber: 이전 호출에서 반환된 Transcriber 인스턴스.
            전달하면 모델 재로드를 생략하여 성능이 크게 향상됩니다.

    Returns:
        사용된 Transcriber 인스턴스 (다음 호출 시 _reuse_transcriber로 전달)
    """
    _log = on_log or (lambda msg: None)
    params = dict(params or {})
    repeat_threshold = int(params.pop("repeat_threshold", 4))

    if engine == "faster-whisper":
        if _reuse_transcriber is not None:
            transcriber = _reuse_transcriber
        else:
            device = params.pop("device", "auto")
            compute_type = params.pop("compute_type", "auto")
            transcriber = FasterWhisperTranscriber(
                model_name=model_name, device=device, compute_type=compute_type,
                params=params, on_log=on_log,
            )
    elif engine == "openai-whisper":
        if _reuse_transcriber is not None:
            transcriber = _reuse_transcriber
        else:
            api_key = params.pop("api_key", None)
            transcriber = OpenAIWhisperTranscriber(api_key=api_key, on_log=on_log)
    elif engine == "returnzero":
        if _reuse_transcriber is not None:
            transcriber = _reuse_transcriber
        else:
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

    return transcriber


# 하위 호환성 유지
transcribe_wav_to_text = transcribe_audio_to_text


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, txt_path: str):
        pass



class FasterWhisperTranscriber(Transcriber):
    def __init__(self, model_name="large-v3-turbo", device="auto", compute_type="auto", params=None, on_log=None):
        from faster_whisper import WhisperModel
        self._on_log = on_log or (lambda msg: None)
        self._language = (params or {}).get("language", "ko")
        self._initial_prompt = (params or {}).get("initial_prompt", "한국어 강의입니다.")
        self._vad_filter = bool((params or {}).get("vad_filter", True))

        # VAD(silero) ONNX 파일 가용성 확인 — PyInstaller 빌드 환경에서 누락 가능
        if self._vad_filter:
            vad_available = self._check_vad_available()
            if not vad_available:
                self._vad_filter = False
                self._on_log(
                    "⚠️ [faster-whisper] silero VAD 모델 파일 없음 — VAD 필터 비활성화됨\n"
                    "   (음성 구간 탐지가 꺼져서 전체 구간을 처리하므로 속도가 느려질 수 있습니다)\n"
                    "   PyInstaller 빌드 시 faster_whisper/assets/ 디렉토리를 포함하면 VAD가 활성화됩니다."
                )

        resolved_device, resolved_compute = self._resolve_device(device, compute_type, self._on_log)
        self._on_log(f"[faster-whisper] 모델 로드 중: {model_name} (device={resolved_device}, compute_type={resolved_compute})")
        self._on_log("[faster-whisper] 첫 실행이면 모델 다운로드가 자동으로 진행됩니다. 잠시 기다려주세요...")
        load_start = time.time()

        try:
            self.model = WhisperModel(model_name, device=resolved_device, compute_type=resolved_compute)
        except Exception as e:
            if resolved_device != "cpu":
                self._on_log(f"⚠️ GPU 초기화 실패: {e}")
                self._on_log("[faster-whisper] CPU 모드로 전환합니다...")
                resolved_device = "cpu"
                resolved_compute = "int8"
                self.model = WhisperModel(model_name, device="cpu", compute_type="int8")
            else:
                raise

        self.model_load_sec = time.time() - load_start
        self._on_log(f"[faster-whisper] 모델 로드 완료: {self.model_load_sec:.1f}초 (device={resolved_device})")

    @staticmethod
    def _check_vad_available() -> bool:
        """silero VAD ONNX 모델 파일이 존재하는지 확인.

        PyInstaller 빌드 환경에서 faster_whisper/assets/ 디렉토리가 누락될 수 있어
        VAD 활성화 전에 파일 존재 여부를 검사합니다.
        """
        try:
            import faster_whisper
            assets_dir = os.path.join(os.path.dirname(faster_whisper.__file__), "assets")
            silero_path = os.path.join(assets_dir, "silero_vad_v6.onnx")
            return os.path.isfile(silero_path)
        except Exception:
            return False

    @staticmethod
    def _resolve_device(device: str, compute_type: str, on_log=None) -> tuple:
        """device='auto'일 때 CUDA 가용 여부를 판단하여 실제 디바이스를 결정.

        faster-whisper(CTranslate2)는 CUDA(NVIDIA)만 GPU 가속을 지원함.
        Apple Silicon(M1~M5), Intel Arc, AMD 내장 GPU는 CUDA 미지원 → CPU 폴백.

        감지 우선순위:
        1. ctranslate2 내장 CUDA 지원 확인 (가장 신뢰도 높음)
        2. torch.cuda.is_available() (torch 설치 시)
        3. nvidia-smi 시스템 명령 (드라이버만 있어도 감지)
        """
        _log = on_log or print

        if device != "auto":
            return device, compute_type

        # 1. ctranslate2 자체 CUDA 감지 (가장 신뢰도 높음 — 실제 사용 라이브러리)
        try:
            import ctranslate2
            compute_types = ctranslate2.get_supported_compute_types("cuda")
            if compute_types:
                gpu_info = f"CTranslate2 CUDA 지원 (types: {', '.join(compute_types)})"
                _log(f"[faster-whisper] CUDA GPU 감지: {gpu_info}")
                return "cuda", compute_type if compute_type != "auto" else "float16"
        except (ValueError, RuntimeError):
            # ctranslate2 CUDA 빌드가 아닌 경우 ValueError 발생
            pass
        except Exception as e:
            _log(f"[faster-whisper] ctranslate2 CUDA 확인 중 예외 (무시): {e}")

        # 2. PyTorch CUDA 감지 (torch 설치 시)
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                _log(f"[faster-whisper] CUDA GPU 감지 (torch): {gpu_name}")
                return "cuda", compute_type if compute_type != "auto" else "float16"
        except ImportError:
            pass

        # 3. nvidia-smi 시스템 명령 (드라이버 설치 여부만 확인)
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                gpu_name = result.stdout.strip().split("\n")[0]
                _log(f"[faster-whisper] NVIDIA GPU 감지 (nvidia-smi): {gpu_name}")
                _log("[faster-whisper] ⚠️ ctranslate2/torch에서 CUDA를 감지하지 못했습니다.")
                _log("[faster-whisper] CUDA Toolkit 또는 ctranslate2 CUDA 빌드 버전이 필요합니다.")
                _log("[faster-whisper] → https://developer.nvidia.com/cuda-downloads 참조")
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

        if sys.platform == "darwin":
            _log("[faster-whisper] macOS 감지 — Apple Silicon은 CUDA 미지원, CPU 모드 사용")
        else:
            _log("[faster-whisper] CUDA GPU 미감지 — CPU 모드 사용")

        return "cpu", compute_type if compute_type != "auto" else "int8"

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


class OpenAIWhisperTranscriber(Transcriber):
    """OpenAI Whisper API 기반 클라우드 STT (로컬 모델 다운로드 불필요)"""

    def __init__(self, api_key: str = None, on_log=None):
        from openai import OpenAI
        self._on_log = on_log or (lambda msg: None)
        if not api_key:
            raise ValueError("OpenAI Whisper API 키가 필요합니다.")
        self.client = OpenAI(api_key=api_key)
        self._on_log("[openai-whisper] 클라우드 STT 엔진 초기화 완료")

    def transcribe(self, audio_path: str, txt_path: str):
        self._on_log(f"[openai-whisper] 클라우드 STT 시작: {audio_path}")
        transcribe_start = time.time()

        with open(audio_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ko",
                response_format="text",
            )

        text = response if isinstance(response, str) else response.text

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        elapsed = time.time() - transcribe_start
        self._on_log(f"[openai-whisper] 변환 완료: {txt_path}")
        self._on_log(f"[openai-whisper] 소요 시간: {elapsed:.1f}초")


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
