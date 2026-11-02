from __future__ import annotations

from urllib.parse import urlparse

from .rss_reader import FeedItem


SUPPORTED_TYPES = {"pdf", "epub"}


def document_type(url: str) -> str | None:
    suffix = urlparse(url).path.lower().rsplit(".", 1)
    return suffix[1] if len(suffix) == 2 and suffix[1] in SUPPORTED_TYPES else None


class DocumentFilter:
    def __init__(self, keywords: tuple[str, ...] = ()):
        self.keywords = tuple(keyword.lower() for keyword in keywords)

    def matches(self, item: FeedItem) -> bool:
        if not item.url or document_type(item.url) is None:
            return False
        if not self.keywords:
            return True
        haystack = f"{item.title} {item.url}".lower()
        return any(keyword in haystack for keyword in self.keywords)
