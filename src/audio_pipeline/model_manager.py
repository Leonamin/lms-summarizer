"""
whisper.cpp 모델 관리: 레지스트리, 로컬 경로 확인, HuggingFace 다운로드
"""

import os
import threading
from typing import Optional, Callable


# ── 모델 레지스트리 ──────────────────────────────────────────────
MODEL_REGISTRY: dict[str, dict] = {
    "base": {
        "label": "번개 모드",
        "emoji": "⚡",
        "description": "성능보다 속도가 중요할 때",
        "size_mb": 74,
        "source": "builtin",
        "model_id": "base",  # pywhispercpp에 직접 전달할 이름
    },
    "turbo-q4k": {
        "label": "표준 모드",
        "emoji": "⚖️",
        "description": "가장 추천하는 균형 잡힌 성능",
        "size_mb": 474,
        "source": "huggingface",
        "filename": "ggml-large-v3-turbo-q4_k.bin",
        "url": "https://huggingface.co/Pomni/whisper-large-v3-turbo-ggml-allquants/resolve/main/ggml-large-v3-turbo-q4_k.bin",
    },
    "korean": {
        "label": "고정밀 모드",
        "emoji": "💎",
        "description": "가장 정확한 한국어 인식",
        "size_mb": 1620,
        "source": "huggingface",
        "filename": "whisper-large-v3-turbo-korean.bin",
        "url": "https://huggingface.co/royshilkrot/whisper-large-v3-turbo-korean-ggml/resolve/main/whisper-large-v3-turbo-korean.bin",
    },
}

# 기본 모드 순서 (UI 표시용)
MODE_ORDER = ["base", "turbo-q4k", "korean"]


# ── 경로 관리 ────────────────────────────────────────────────────

def get_models_dir() -> str:
    """앱 데이터 디렉토리 내 models/ 폴더 경로"""
    from src.gui.core.file_manager import get_app_data_dir
    models_dir = os.path.join(get_app_data_dir(), "models")
    os.makedirs(models_dir, exist_ok=True)
    return models_dir


def get_local_path(model_key: str) -> Optional[str]:
    """
    model_key에 해당하는 로컬 파일 경로 반환.
    - builtin: None (pywhispercpp 자동 처리)
    - HF 모델: 다운로드된 경우 경로, 없으면 None
    - 직접 경로: 존재하면 그대로 반환
    """
    info = MODEL_REGISTRY.get(model_key)
    if info is None:
        # 직접 파일 경로로 취급
        return model_key if os.path.isfile(model_key) else None

    if info["source"] == "builtin":
        return None  # pywhispercpp이 처리

    path = os.path.join(get_models_dir(), info["filename"])
    return path if os.path.exists(path) else None


def get_expected_path(model_key: str) -> Optional[str]:
    """다운로드 대상 경로 (존재 여부 무관). builtin은 None."""
    info = MODEL_REGISTRY.get(model_key)
    if not info or info["source"] == "builtin":
        return None
    return os.path.join(get_models_dir(), info["filename"])


def is_available(model_key: str) -> bool:
    """모델을 즉시 사용할 수 있는지 확인 (builtin은 항상 True)"""
    info = MODEL_REGISTRY.get(model_key)
    if info is None:
        return os.path.isfile(model_key)
    if info["source"] == "builtin":
        return True
    return get_local_path(model_key) is not None


def resolve_for_transcriber(model_key: str) -> tuple[Optional[str], str]:
    """
    Transcriber에 전달할 (custom_path, builtin_name) 반환.
    - builtin: (None, "base")
    - HF 다운로드: (경로, "")
    - 직접 경로: (경로, "")
    사용 불가능한 경우 FileNotFoundError 발생.
    """
    info = MODEL_REGISTRY.get(model_key)

    if info is None:
        # 직접 파일 경로
        if os.path.isfile(model_key):
            return model_key, ""
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_key}")

    if info["source"] == "builtin":
        return None, info["model_id"]

    path = get_local_path(model_key)
    if not path:
        label = info["label"]
        size = info["size_mb"]
        raise FileNotFoundError(
            f"'{label}' 모델이 다운로드되지 않았습니다. "
            f"설정 > 고급 설정 > STT 엔진에서 다운로드하세요. (약 {size}MB)"
        )
    return path, ""


# ── 다운로드 ─────────────────────────────────────────────────────

class DownloadCancelled(Exception):
    pass


def download_model(
    model_key: str,
    on_progress: Optional[Callable[[int, int], None]] = None,
    cancel_event: Optional[threading.Event] = None,
) -> str:
    """
    HF에서 모델 다운로드. 완료된 로컬 경로 반환.
    on_progress(downloaded_bytes, total_bytes) 콜백 지원.
    cancel_event.set() 시 DownloadCancelled 발생.
    """
    import requests

    info = MODEL_REGISTRY.get(model_key)
    if not info or info["source"] == "builtin":
        raise ValueError(f"다운로드 불필요한 모델: {model_key}")

    dest = os.path.join(get_models_dir(), info["filename"])
    if os.path.exists(dest):
        return dest

    tmp = dest + ".part"
    url = info["url"]

    try:
        resp = requests.get(url, stream=True, timeout=30)
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(tmp, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):  # 1MB
                if cancel_event and cancel_event.is_set():
                    raise DownloadCancelled()
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if on_progress:
                        on_progress(downloaded, total)

        os.rename(tmp, dest)
        return dest

    except DownloadCancelled:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
