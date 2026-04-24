from app.schemas.serp import OrganicResult
from app.utils.domains import domains_match, extract_domain


def find_domain_matches(
    target_domain: str, organic_results: list[OrganicResult]
) -> tuple[bool, int | None, str | None, list[int], list[str]]:
    matched_pairs: list[tuple[int, str]] = []

    for result in organic_results:
        result_domain = extract_domain(result.link)
        if result_domain and domains_match(target_domain, result_domain):
            matched_pairs.append((result.rank, result.link))

    matched_pairs.sort(key=lambda item: item[0])
    matched_positions = [rank for rank, _ in matched_pairs]
    matched_urls = [url for _, url in matched_pairs]
    best_position = matched_positions[0] if matched_positions else None
    matched_url = matched_urls[0] if matched_urls else None

    return best_position is not None, best_position, matched_url, matched_positions, matched_urls
