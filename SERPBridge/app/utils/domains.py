from urllib.parse import urlparse


def normalize_domain(value: str) -> str:
    candidate = value.strip().lower()
    if "://" in candidate:
        candidate = urlparse(candidate).hostname or ""
    if candidate.startswith("www."):
        candidate = candidate[4:]
    return candidate.strip(".")


def extract_domain(url: str) -> str | None:
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return None
    return normalize_domain(hostname)


def domains_match(target_domain: str, result_domain: str) -> bool:
    target = normalize_domain(target_domain)
    result = normalize_domain(result_domain)
    return result == target or result.endswith(f".{target}")
