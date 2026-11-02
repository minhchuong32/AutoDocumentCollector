from pathlib import Path

import pytest

from src.services.downloader import DownloadError, Downloader


class FakeResponse:
    def __init__(self, body: bytes, content_type="application/pdf", status_code=200):
        self.body = body
        self.status_code = status_code
        self.headers = {"Content-Type": content_type, "Content-Length": str(len(body))}

    def iter_content(self, chunk_size):
        yield self.body

    def close(self):
        pass


class FakeSession:
    def __init__(self, response):
        self.response = response

    def get(self, *args, **kwargs):
        return self.response


def test_downloader_writes_pdf_atomically(tmp_path: Path):
    downloader = Downloader(tmp_path / "raw", 100, session=FakeSession(FakeResponse(b"%PDF-1.7 data")))
    result = downloader.download("https://example.org/file.pdf", "A paper", "pdf")
    assert result.path.read_bytes().startswith(b"%PDF")
    assert not list(result.path.parent.glob("*.part"))


def test_downloader_rejects_invalid_signature_and_cleans_part(tmp_path: Path):
    downloader = Downloader(tmp_path / "raw", 100, session=FakeSession(FakeResponse(b"not a pdf")))
    with pytest.raises(DownloadError):
        downloader.download("https://example.org/file.pdf", "A paper", "pdf")
    assert not list((tmp_path / "raw" / "pdf").glob("*.part"))


def test_downloader_rejects_oversized_content(tmp_path: Path):
    downloader = Downloader(tmp_path / "raw", 4, session=FakeSession(FakeResponse(b"%PDF-1.7")))
    with pytest.raises(DownloadError):
        downloader.download("https://example.org/file.pdf", "A paper", "pdf")
