from app.utils.domains import domains_match, extract_domain, normalize_domain


def test_normalize_domain_handles_scheme_and_www() -> None:
    assert normalize_domain("https://www.openai.com/path") == "openai.com"


def test_extract_domain_reads_hostname() -> None:
    assert extract_domain("https://platform.openai.com/docs") == "platform.openai.com"


def test_domains_match_allows_subdomains() -> None:
    assert domains_match("openai.com", "platform.openai.com") is True
    assert domains_match("openai.com", "exampleopenai.com") is False
