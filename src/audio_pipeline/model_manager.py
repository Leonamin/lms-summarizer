"""
STT 모델 관리: Faster-Whisper 레지스트리
"""


# ── Faster-Whisper 모델 레지스트리 ─────────────────────────────────

FW_MODEL_REGISTRY: dict[str, dict] = {
    "large-v3-turbo": {
        "label": "표준 모드",
        "emoji": "⚖️",
        "description": "정확도와 속도의 균형 (권장)",
        "size_mb": 800,
        "source": "hf_auto",
        "hf_model": "large-v3-turbo",
    },
    "small": {
        "label": "경량 모드",
        "emoji": "🪶",
        "description": "빠른 인식, 저사양/CPU 환경에 적합 (461MB)",
        "size_mb": 461,
        "source": "hf_auto",
        "hf_model": "small",
    },
    "large-v3": {
        "label": "고정밀 모드",
        "emoji": "💎",
        "description": "최고 정확도 (속도 느림, 3.1GB)",
        "size_mb": 3100,
        "source": "hf_auto",
        "hf_model": "large-v3",
    },
}

FW_MODE_ORDER = ["large-v3-turbo", "small", "large-v3"]


def is_available(model_key: str, engine: str = "faster-whisper") -> bool:
    """모델을 즉시 사용할 수 있는지 확인.
    faster-whisper는 huggingface_hub이 첫 실행 시 자동 다운로드하므로 항상 True.
    """
    return True
