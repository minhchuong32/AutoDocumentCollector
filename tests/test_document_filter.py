from src.services.document_filter import DocumentFilter, document_type
from src.services.document_resolver import DocumentResolver
from src.services.rss_reader import FeedItem


def test_document_type_and_keyword_filter():
    item = FeedItem("Business Models", "https://example.org/paper.pdf")
    assert document_type(item.url) == "pdf"
    assert DocumentFilter(("business",)).matches(item)
    assert not DocumentFilter(("biology",)).matches(item)
    assert not DocumentFilter().matches(FeedItem("Other", "https://example.org/page"))


def test_arxiv_abstract_is_resolved_to_pdf():
    item = FeedItem("An arXiv paper", "https://arxiv.org/abs/2401.12345v2")
    assert DocumentFilter().matches(item)
    assert DocumentResolver().resolve(item.url) == (
        "https://export.arxiv.org/pdf/2401.12345v2",
        "pdf",
    )
