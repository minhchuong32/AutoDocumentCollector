from __future__ import annotations

from urllib.parse import urlparse

from .document_filter import document_type


class DocumentResolver:
    """Resolve direct links and public arXiv abstract links."""

    def resolve(self, url: str) -> tuple[str, str] | None:
        file_type = document_type(url)
        if file_type:
            return url, file_type
        parsed = urlparse(url)
        if (
            parsed.scheme == "https"
            and parsed.netloc.lower() in {"arxiv.org", "export.arxiv.org"}
            and parsed.path.startswith("/abs/")
            and len(parsed.path) > len("/abs/")
        ):
            identifier = parsed.path.removeprefix("/abs/")
            return f"https://export.arxiv.org/pdf/{identifier}", "pdf"
        return None
