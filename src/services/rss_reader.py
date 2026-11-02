from __future__ import annotations

from dataclasses import dataclass

import feedparser
import requests


@dataclass(frozen=True)
class FeedItem:
    title: str
    url: str
    published: str | None = None


class RSSReader:
    def __init__(self, timeout: int = 30, session=None):
        self.timeout = timeout
        self.session = session or requests.Session()

    def read(self, feed_url: str) -> list[FeedItem]:
        response = self.session.get(feed_url, timeout=self.timeout)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        if parsed.bozo:
            raise ValueError(f"Invalid RSS feed: {feed_url}")
        return [
            FeedItem(
                title=(entry.get("title") or "Untitled").strip(),
                url=(entry.get("link") or "").strip(),
                published=entry.get("published") or entry.get("updated"),
            )
            for entry in parsed.entries
        ]
