"""Atomic JSON storage; shared locks serialize read-modify-write in one process."""
import json
import os
import tempfile
import threading
from pathlib import Path
from copy import deepcopy

_locks: dict[str, threading.RLock] = {}
_guard = threading.Lock()

class JsonStore:
    def __init__(self, path: Path, default=None):
        self.path = Path(path)
        self.default = {} if default is None else default
        with _guard:
            self.lock = _locks.setdefault(str(self.path.resolve()), threading.RLock())

    def read(self):
        with self.lock:
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                return deepcopy(self.default)

    def write(self, value):
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(dir=self.path.parent, prefix=".json-")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    json.dump(value, stream, ensure_ascii=False, indent=2)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(name, self.path)
            finally:
                if os.path.exists(name):
                    os.unlink(name)

    def update(self, change):
        with self.lock:
            value = self.read()
            change(value)
            self.write(value)
            return value
