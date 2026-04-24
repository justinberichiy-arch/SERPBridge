import csv
from io import StringIO

from app.utils.domains import normalize_domain


def parse_domain_keywords_csv(csv_text: str) -> list[dict]:
    reader = csv.DictReader(StringIO(csv_text))
    if not reader.fieldnames:
        raise ValueError("CSV is empty")

    expected = {"domain", "keywords"}
    if set(reader.fieldnames) != expected:
        raise ValueError("CSV headers must be exactly: domain,keywords")

    expanded: list[dict] = []
    for row_number, row in enumerate(reader, start=2):
        raw_domain = (row.get("domain") or "").strip()
        raw_keywords = (row.get("keywords") or "").strip()
        if not raw_domain:
            raise ValueError(f"Row {row_number}: domain is required")
        if not raw_keywords:
            raise ValueError(f"Row {row_number}: keywords is required")

        domain = normalize_domain(raw_domain)
        seen: set[str] = set()
        for keyword in raw_keywords.split("###"):
            normalized_keyword = keyword.strip()
            if not normalized_keyword or normalized_keyword in seen:
                continue
            seen.add(normalized_keyword)
            expanded.append({"target_domain": domain, "keyword": normalized_keyword})

    if not expanded:
        raise ValueError("CSV did not produce any job items")

    return expanded
