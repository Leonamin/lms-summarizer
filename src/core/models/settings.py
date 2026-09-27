"""Framework independent execution settings. Secret values are never represented."""
from dataclasses import dataclass, field
from typing import Mapping
from src.core.prompts import DEFAULT_PROMPT, build_prompt

@dataclass(frozen=True)
class UserContext:
    owner_id: str = "local"

@dataclass(frozen=True)
class LMSCredentials:
    user_id: str
    password: str = field(repr=False)

@dataclass(frozen=True)
class PromptSettings:
    mode: str = "structured"
    summary_mode: str = "normal"
    subject_category: str = "자동 감지"
    subject_custom: str = ""
    custom_prompt: str = DEFAULT_PROMPT

    def resolve(self) -> str:
        if self.mode == "custom":
            if not self.custom_prompt.strip():
                raise ValueError("Custom prompt is empty")
            return self.custom_prompt
        if self.mode != "structured":
            raise ValueError("Unknown prompt mode")
        return build_prompt(self.summary_mode, self.subject_category, self.subject_custom)

@dataclass(frozen=True)
class SettingsRevision:
    id: str
    owner_id: str
    resolved_prompt: str
    # Serialized copies prevent callers from mutating submitted settings.
    settings_json: str
    secret_versions: tuple[tuple[str, str], ...] = ()
