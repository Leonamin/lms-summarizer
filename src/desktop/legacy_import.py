"""Read-only import of legacy JSON. Never rewrites or moves the source file."""
import json
from pathlib import Path
from dataclasses import dataclass, field
from src.core.models.settings import PromptSettings

@dataclass
class LegacyData:
    settings: dict
    secrets: dict = field(repr=False)
    courses: list = field(default_factory=list)
    history: list = field(default_factory=list)

def read_legacy(path: Path) -> LegacyData:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    inputs = raw.get("user_inputs", {})
    api_keys = raw.get("api_keys", inputs.get("api_keys", {}))
    if not api_keys and inputs.get("api_key"):
        api_keys = {"gemini": inputs["api_key"]}
    stt_keys = raw.get("stt_api_keys", {})
    engine = inputs.get("ai_engine", "gemini")
    prompt_mode = "structured" if raw.get("summary_mode") or not raw.get("summary_prompt") else "custom"
    prompt = PromptSettings(mode=prompt_mode, summary_mode=raw.get("summary_mode", "normal"),
                            subject_category=raw.get("subject_category", "자동 감지"),
                            subject_custom=raw.get("subject_custom", ""),
                            custom_prompt=raw.get("summary_prompt", ""))
    settings = {
        "student_id": inputs.get("student_id", ""), "ai_engine": engine,
        "ai_model": inputs.get("ai_model", ""),
        "base_url": raw.get("base_urls", inputs.get("base_urls", {})).get(engine, inputs.get("base_url", "")),
        "stt_engine": raw.get("stt_engine", "faster-whisper"),
        "stt_model": raw.get("stt_model", "large-v3-turbo"),
        "stt_base_url": stt_keys.get("openai-compatible-base-url", ""),
        "stt_compatible_model": stt_keys.get("openai-compatible-model", ""),
        "stt_params": raw.get("stt_params", {}),
        "prompt_mode": prompt_mode, "resolved_prompt": prompt.resolve(),
        "downloads_dir": raw.get("downloads_dir", ""),
    }
    secrets = {f"summary:{k}": v for k, v in api_keys.items() if v}
    secrets.update({f"stt:{k}": v for k, v in stt_keys.items()
                    if v and k not in ("openai-compatible-base-url", "openai-compatible-model")})
    for key in ("password", "returnzero_client_id", "returnzero_client_secret"):
        value = inputs.get(key, raw.get(key, ""))
        if value:
            secrets[key] = value
    if raw.get("stt_api_key"):
        # Unknown single ReturnZero key is retained, never guessed into a credential pair.
        secrets["legacy:stt_api_key"] = raw["stt_api_key"]
    return LegacyData(settings, secrets, raw.get("course_cache", {}).get("courses", []), raw.get("history", []))
