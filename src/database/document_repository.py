from __future__ import annotations

import sqlite3
from datetime import datetime, timezone


class DocumentRepository:
    def __init__(self, database):
        self.database = database

    def add_discovered(self, title: str, source_url: str) -> int | None:
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO documents (title, source_url) VALUES (?, ?)",
                (title, source_url),
            )
            return cursor.lastrowid or None

    def is_processed(self, source_url: str) -> bool:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT status FROM documents WHERE source_url = ?", (source_url,)
            ).fetchone()
        return row is not None and row["status"] in {"DOWNLOADED", "VALIDATED", "SKIPPED"}

    def update(self, source_url: str, **fields) -> None:
        allowed = {"download_url", "file_type", "file_path", "status", "downloaded_at"}
        values = {key: value for key, value in fields.items() if key in allowed}
        if not values:
            return
        assignments = ", ".join(f"{key} = ?" for key in values)
        with self.database.connect() as connection:
            connection.execute(
                f"UPDATE documents SET {assignments} WHERE source_url = ?",
                (*values.values(), source_url),
            )

    def mark_downloaded(self, source_url: str, file_path: str) -> None:
        self.update(
            source_url,
            status="DOWNLOADED",
            file_path=file_path,
            downloaded_at=datetime.now(timezone.utc).isoformat(),
        )

    def mark_failed(self, source_url: str) -> None:
        self.update(source_url, status="FAILED")
