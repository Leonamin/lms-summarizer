"""Create immutable, transport-safe submission settings with secret references."""
import json
from uuid import uuid4
from src.core.models.settings import PromptSettings, SettingsRevision

def snapshot_settings(owner_id: str, settings: dict, prompt: PromptSettings,
                      secret_versions: dict[str, str]) -> SettingsRevision:
    forbidden = {"password", "api_key", "api_keys", "stt_api_key", "stt_api_keys", "client_secret", "returnzero_client_secret"}
    def check(value):
        if isinstance(value, dict):
            if forbidden.intersection(value):
                raise ValueError("Secret values belong in the secret repository")
            for item in value.values():
                check(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                check(item)
    check(settings)
    return SettingsRevision(str(uuid4()), owner_id, prompt.resolve(),
                            json.dumps(settings, ensure_ascii=False, sort_keys=True),
                            tuple(sorted(secret_versions.items())))
