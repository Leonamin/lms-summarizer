"""Versioned local secrets, independent of public settings and transport DTOs."""
import os
from pathlib import Path
from uuid import uuid4
from src.core.repositories.json_store import JsonStore

class SecretRepository:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)

    def _store(self, version: str):
        # Only generated UUIDs are valid file references.
        from uuid import UUID
        if str(UUID(version)) != version:
            raise ValueError("Invalid secret reference")
        return JsonStore(self.root / f"{version}.json")

    def put(self, owner_id: str, provider: str, value: str) -> str:
        version = str(uuid4())
        store = self._store(version)
        store.write({"owner_id": owner_id, "provider": provider, "value": value})
        os.chmod(store.path, 0o600)
        return version

    def get(self, owner_id: str, version: str) -> str:
        record = self._store(version).read()
        if record.get("owner_id") != owner_id:
            raise KeyError("credentials_missing")
        return record["value"]
