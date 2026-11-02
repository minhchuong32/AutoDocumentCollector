from __future__ import annotations

import logging

from config.settings import Settings
from src.database.db import Database
from src.database.document_repository import DocumentRepository
from src.services.document_filter import DocumentFilter
from src.services.document_resolver import DocumentResolver
from src.services.downloader import Downloader
from src.services.rss_reader import RSSReader
from src.services.url_validator import URLValidator
from src.utils.logger import configure_logging


def run(settings: Settings | None = None) -> dict[str, int]:
    settings = settings or Settings.from_env()
    settings.ensure_directories()
    logger = configure_logging(settings.log_path)
    database = Database(settings.database_path)
    database.initialize()
    repository = DocumentRepository(database)
    reader = RSSReader(settings.request_timeout)
    document_filter = DocumentFilter(settings.keywords)
    validator = URLValidator(settings.allowed_domains)
    resolver = DocumentResolver()
    downloader = Downloader(settings.download_dir, settings.max_file_size, settings.request_timeout)
    counters = {"feeds": 0, "discovered": 0, "downloaded": 0, "skipped": 0, "failed": 0}

    for feed_url in settings.rss_urls:
        try:
            items = reader.read(feed_url)
            counters["feeds"] += 1
            logger.info("Read %s entries from %s", len(items), feed_url)
        except Exception:
            counters["failed"] += 1
            logger.exception("RSS read failed: %s", feed_url)
            continue
        for item in items:
            if not item.url:
                counters["skipped"] += 1
                continue
            repository.add_discovered(item.title, item.url)
            counters["discovered"] += 1
            if repository.is_processed(item.url):
                counters["skipped"] += 1
                continue
            try:
                if not document_filter.matches(item) or not validator.is_allowed(item.url):
                    repository.update(item.url, status="SKIPPED")
                    counters["skipped"] += 1
                    continue
                resolved = resolver.resolve(item.url)
                if not resolved:
                    repository.update(item.url, status="SKIPPED")
                    counters["skipped"] += 1
                    continue
                download_url, file_type = resolved
                repository.update(item.url, download_url=download_url, file_type=file_type, status="VALIDATED")
                result = downloader.download(download_url, item.title, file_type)
                repository.mark_downloaded(item.url, str(result.path))
                counters["downloaded"] += 1
                logger.info("Downloaded %s", result.path)
            except Exception:
                repository.mark_failed(item.url)
                counters["failed"] += 1
                logger.exception("Document processing failed: %s", item.url)
    logger.info("Run complete: %s", counters)
    return counters


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
