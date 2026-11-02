from __future__ import annotations

from urllib.parse import urlparse


class URLValidator:
    def __init__(self, allowed_domains: tuple[str, ...] = ()):
        self.allowed_domains = tuple(domain.lstrip(".").lower() for domain in allowed_domains)

    def is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            return False
        if not self.allowed_domains:
            return False
        host = parsed.hostname.lower().rstrip(".")
        return any(host == domain or host.endswith(f".{domain}") for domain in self.allowed_domains)
