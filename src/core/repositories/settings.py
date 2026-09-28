"""Explicit settings, cache and history boundaries for independent app data roots."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
from src.core.repositories.json_store import JsonStore

class SettingsRepository(JsonStore):
    def __init__(self, root: Path):
        super().__init__(Path(root) / "settings.json")

class HistoryRepository(JsonStore):
    def __init__(self, root: Path):
        super().__init__(Path(root) / "history.json", [])

    def append(self, entry):
        self.update(lambda entries: entries.append(entry))

class CacheRepository:
    def __init__(self, root: Path):
        self.root = Path(root)

    def _store(self, owner_id, account, key):
        digest = sha256(f"{owner_id}\0{account}\0{key}".encode()).hexdigest()
        return JsonStore(self.root / f"{digest}.json")

    def put(self, owner_id, account, key, data):
        self._store(owner_id, account, key).write({"time": datetime.now(timezone.utc).isoformat(), "data": data})

    def get(self, owner_id, account, key, max_age_hours=24):
        record = self._store(owner_id, account, key).read()
        if not record:
            return []
        age = datetime.now(timezone.utc) - datetime.fromisoformat(record["time"])
        return record["data"] if age.total_seconds() <= max_age_hours * 3600 else []
