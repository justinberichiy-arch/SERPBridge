import httpx

from app.providers.base import BaseSerpProvider
from app.schemas.serp import OrganicResult, QueryRequest


class SerpBaseProvider(BaseSerpProvider):
    name = "serpbase"

    async def fetch(self, request: QueryRequest) -> tuple[int, dict]:
        payload = {
            "q": request.keyword,
            "hl": request.language,
            "gl": request.country,
            "page": request.page,
        }
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.account.api_key,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.account.base_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.status_code, response.json()

    def extract_organic(self, raw: dict) -> list[OrganicResult]:
        items: list[OrganicResult] = []
        for entry in raw.get("organic", []):
            link = entry.get("link")
            rank = entry.get("rank")
            if not link or rank is None:
                continue
            items.append(
                OrganicResult(
                    rank=int(rank),
                    title=entry.get("title"),
                    link=link,
                    display_link=entry.get("display_link"),
                    snippet=entry.get("snippet"),
                )
            )
        return items
