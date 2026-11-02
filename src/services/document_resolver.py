from __future__ import annotations

from .document_filter import document_type


class DocumentResolver:
    """Version 1 resolves direct PDF/EPUB links only."""

    def resolve(self, url: str) -> tuple[str, str] | None:
        file_type = document_type(url)
        return (url, file_type) if file_type else None
