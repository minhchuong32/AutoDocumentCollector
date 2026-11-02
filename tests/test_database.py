from src.database.db import Database
from src.database.document_repository import DocumentRepository


def test_repository_deduplicates_and_updates_status(tmp_path):
    database = Database(tmp_path / "collector.db")
    database.initialize()
    repository = DocumentRepository(database)
    assert repository.add_discovered("Paper", "https://example.org/paper.pdf")
    assert repository.add_discovered("Paper", "https://example.org/paper.pdf") is None
    assert not repository.is_processed("https://example.org/paper.pdf")
    repository.update("https://example.org/paper.pdf", status="DOWNLOADED")
    assert repository.is_processed("https://example.org/paper.pdf")
