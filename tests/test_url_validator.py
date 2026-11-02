from src.services.url_validator import URLValidator


def test_validator_requires_https_and_allowed_domain():
    validator = URLValidator(("example.org",))
    assert validator.is_allowed("https://example.org/file.pdf")
    assert validator.is_allowed("https://sub.example.org/file.pdf")
    assert not validator.is_allowed("http://example.org/file.pdf")
    assert not validator.is_allowed("https://example.net/file.pdf")
