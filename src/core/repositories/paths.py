from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DataPaths:
    root: Path
    models: Path

    def file(self, relative: str) -> Path:
        root = self.root.resolve()
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Path escapes data directory")
        return path
