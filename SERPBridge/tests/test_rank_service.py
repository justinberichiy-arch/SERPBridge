from app.schemas.serp import OrganicResult
from app.services.rank_service import find_domain_matches


def test_find_domain_matches_returns_all_positions_and_urls() -> None:
    organic = [
        OrganicResult(rank=2, link="https://example.com/page-a"),
        OrganicResult(rank=5, link="https://other.com/page"),
        OrganicResult(rank=9, link="https://blog.example.com/page-b"),
    ]

    matched, best_position, matched_url, matched_positions, matched_urls = find_domain_matches(
        "example.com", organic
    )

    assert matched is True
    assert best_position == 2
    assert matched_url == "https://example.com/page-a"
    assert matched_positions == [2, 9]
    assert matched_urls == [
        "https://example.com/page-a",
        "https://blog.example.com/page-b",
    ]
