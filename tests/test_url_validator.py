from src.services.url_validator import URLValidator


def test_validator_requires_https_and_allowed_domain():
    validator = URLValidator(("example.org",))
    assert validator.is_allowed("https://example.org/file.pdf")
    assert validator.is_allowed("https://sub.example.org/file.pdf")
    assert not validator.is_allowed("http://example.org/file.pdf")
    assert not validator.is_allowed("https://example.net/file.pdf")


def test_validator_allows_arxiv_download_domain_when_configured():
    validator = URLValidator(("export.arxiv.org", "arxiv.org"))
    assert validator.is_allowed("https://export.arxiv.org/abs/2401.12345")
    assert validator.is_allowed("https://arxiv.org/pdf/2401.12345.pdf")
