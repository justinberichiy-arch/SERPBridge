from app.services.import_service import parse_domain_keywords_csv


def test_parse_domain_keywords_csv_expands_rows_and_deduplicates() -> None:
    csv_text = """domain,keywords
openai.com,chatgpt###gpt api###chatgpt###
"""
    rows = parse_domain_keywords_csv(csv_text)
    assert rows == [
        {"target_domain": "openai.com", "keyword": "chatgpt"},
        {"target_domain": "openai.com", "keyword": "gpt api"},
    ]
