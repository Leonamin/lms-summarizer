"""Server-owned configuration. Desktop storage is never consulted."""
from dataclasses import dataclass, field
import os
from pathlib import Path

@dataclass
class WebConfig:
    data_dir: Path = field(default_factory=lambda: Path(os.getenv('LMS_DATA_DIR', '.local/web-data')))
    models_dir: Path = field(default_factory=lambda: Path(os.getenv('LMS_MODELS_DIR', '.local/web-models')))
    static_dir: Path = field(default_factory=lambda: Path(os.getenv('LMS_STATIC_DIR', 'frontend/dist')))
    allowed_hosts: tuple[str, ...] = field(default_factory=lambda: tuple(os.getenv('LMS_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1]').split(',')))
    allowed_origins: tuple[str, ...] = field(default_factory=lambda: tuple(filter(None, os.getenv('LMS_ALLOWED_ORIGINS', '').split(','))))
    max_upload_bytes: int = field(default_factory=lambda: int(os.getenv('LMS_MAX_UPLOAD_BYTES', str(4 * 1024**3))))
    min_free_bytes: int = field(default_factory=lambda: int(os.getenv('LMS_MIN_FREE_BYTES', str(2 * 1024**3))))
    max_text_bytes: int = 16 * 1024**2
    content_limit: int = 2 * 1024**2
    chrome_path: str = '/usr/bin/google-chrome'
