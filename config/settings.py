from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip().lower() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    rss_urls: tuple[str, ...]
    allowed_domains: tuple[str, ...]
    keywords: tuple[str, ...]
    download_dir: Path
    database_path: Path
    log_path: Path
    max_file_size: int
    request_timeout: int

    @classmethod
    def from_env(cls) -> "Settings":
        download_dir = BASE_DIR / os.getenv("DOWNLOAD_DIR", "downloads/raw")
        return cls(
            rss_urls=_csv(os.getenv("RSS_URLS", os.getenv("RSS_URL", ""))),
            allowed_domains=_csv(os.getenv("ALLOWED_DOMAINS", "")),
            keywords=_csv(os.getenv("KEYWORDS", "")),
            download_dir=download_dir,
            database_path=BASE_DIR / os.getenv("DATABASE_PATH", "data/collector.db"),
            log_path=BASE_DIR / os.getenv("LOG_PATH", "logs/collector.log"),
            max_file_size=int(os.getenv("MAX_FILE_SIZE", "31457280")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
        )

    def ensure_directories(self) -> None:
        self.download_dir.joinpath("pdf").mkdir(parents=True, exist_ok=True)
        self.download_dir.joinpath("epub").mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
