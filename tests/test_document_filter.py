from src.services.document_filter import DocumentFilter, document_type
from src.services.rss_reader import FeedItem


def test_document_type_and_keyword_filter():
    item = FeedItem("Business Models", "https://example.org/paper.pdf")
    assert document_type(item.url) == "pdf"
    assert DocumentFilter(("business",)).matches(item)
    assert not DocumentFilter(("biology",)).matches(item)
    assert not DocumentFilter().matches(FeedItem("Other", "https://example.org/page"))
