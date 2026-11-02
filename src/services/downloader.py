from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests


MIME_TYPES = {"pdf": "application/pdf", "epub": "application/epub+zip"}


@dataclass(frozen=True)
class DownloadResult:
    path: Path
    file_type: str


class DownloadError(Exception):
    pass


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", value).strip(" .")
    return (cleaned[:120] or "document")


class Downloader:
    def __init__(self, destination: Path, max_file_size: int, timeout: int = 30, session=None):
        self.destination = destination
        self.max_file_size = max_file_size
        self.timeout = timeout
        self.session = session or requests.Session()

    def download(self, url: str, title: str, file_type: str) -> DownloadResult:
        if file_type not in MIME_TYPES:
            raise DownloadError(f"Unsupported document type: {file_type}")
        response = self.session.get(url, stream=True, timeout=self.timeout, allow_redirects=False)
        try:
            if response.status_code >= 300:
                raise DownloadError(f"HTTP status {response.status_code}")
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if content_type and content_type not in {MIME_TYPES[file_type], "application/octet-stream"}:
                raise DownloadError(f"Unexpected Content-Type: {content_type}")
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > self.max_file_size:
                raise DownloadError("File exceeds configured size limit")
            return self._write_response(response, url, title, file_type)
        finally:
            response.close()

    def _write_response(self, response, url: str, title: str, file_type: str) -> DownloadResult:
        target_dir = self.destination / file_type
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = _safe_name(title)
        if not filename.lower().endswith(f".{file_type}"):
            filename = f"{filename}.{file_type}"
        target = target_dir / filename
        temporary = target.with_suffix(target.suffix + ".part")
        total = 0
        first_chunk = b""
        try:
            with temporary.open("wb") as output:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    if not first_chunk:
                        first_chunk = chunk[:8]
                    total += len(chunk)
                    if total > self.max_file_size:
                        raise DownloadError("File exceeds configured size limit")
                    output.write(chunk)
            if file_type == "pdf" and not first_chunk.startswith(b"%PDF"):
                raise DownloadError("Response is not a PDF")
            if file_type == "epub" and not first_chunk.startswith(b"PK"):
                raise DownloadError("Response is not an EPUB archive")
            temporary.replace(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return DownloadResult(path=target, file_type=file_type)
