import asyncio

from app.core.config import ProviderAccount
from app.providers.base import BaseSerpProvider
from app.schemas.serp import OrganicResult, QueryRequest
from app.services.serp_service import SerpService


class FakeProvider(BaseSerpProvider):
    name = "fake"

    def __init__(self) -> None:
        super().__init__(ProviderAccount(provider="fake", name="fake", api_key="", base_url=""))

    async def fetch(self, request: QueryRequest) -> tuple[int, dict]:
        return 200, {"page": request.page}

    def extract_organic(self, raw: dict) -> list[OrganicResult]:
        page = raw["page"]
        if page == 1:
            return [
                OrganicResult(rank=1, link="https://a.com/1"),
                OrganicResult(rank=2, link="https://a.com/2"),
            ]
        return [
            OrganicResult(rank=1, link="https://a.com/3"),
            OrganicResult(rank=2, link="https://a.com/4"),
        ]


def test_fetch_multi_page_rewrites_local_page_ranks_to_global_ranks() -> None:
    service = SerpService(provider=FakeProvider())
    payloads, organic = asyncio.run(
        service.fetch_multi_page(
            QueryRequest(keyword="test", country="us", language="en", device="desktop", page=1),
            max_pages=2,
        )
    )

    assert [result.rank for result in organic] == [1, 2, 3, 4]
    assert [result.rank for result in payloads[0][3]] == [1, 2]
    assert [result.rank for result in payloads[1][3]] == [3, 4]
