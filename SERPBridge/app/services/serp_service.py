import asyncio
from typing import Callable

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import JobItem, SerpOrganicResult, SerpRawResponse
from app.providers.base import BaseSerpProvider
from app.providers.registry import build_provider
from app.schemas.serp import OrganicResult, QueryRequest
from app.services.rank_service import find_domain_matches
from app.utils.domains import extract_domain


class SerpService:
    def __init__(self, provider: BaseSerpProvider | None = None, provider_account: str | None = None) -> None:
        self.provider = provider or build_provider(provider_account)

    def provider_request_to_query(self, item: JobItem) -> QueryRequest:
        return QueryRequest(
            keyword=item.keyword,
            country=item.country,
            language=item.language,
            device=item.device,
            page=item.page,
        )

    async def fetch_multi_page(
        self,
        request: QueryRequest,
        max_pages: int,
        page_callback: Callable[[int], None] | None = None,
    ) -> tuple[list[tuple[int, int, dict, list[OrganicResult]]], list[OrganicResult]]:
        settings = get_settings()
        semaphore = asyncio.Semaphore(settings.worker_concurrency)

        async def fetch_page(page_number: int) -> tuple[int, int, dict, list[OrganicResult]]:
            page_request = QueryRequest(
                keyword=request.keyword,
                country=request.country,
                language=request.language,
                device=request.device,
                page=page_number,
            )
            async with semaphore:
                status_code, raw = await self.provider.fetch(page_request)
            if page_callback:
                page_callback(page_number)
            page_organic = self.provider.extract_organic(raw)
            return page_number, status_code, raw, page_organic

        raw_page_payloads = await asyncio.gather(
            *(fetch_page(page_number) for page_number in range(request.page, request.page + max_pages))
        )
        raw_page_payloads.sort(key=lambda item: item[0])

        page_payloads: list[tuple[int, int, dict, list[OrganicResult]]] = []
        all_organic: list[OrganicResult] = []
        organic_counter = 0
        for page_number, status_code, raw, page_organic_raw in raw_page_payloads:
            page_organic: list[OrganicResult] = []
            for result in page_organic_raw:
                organic_counter += 1
                page_organic.append(
                    OrganicResult(
                        rank=organic_counter,
                        title=result.title,
                        link=result.link,
                        display_link=result.display_link,
                        snippet=result.snippet,
                    )
                )
            page_payloads.append((page_number, status_code, raw, page_organic))
            all_organic.extend(page_organic)

        return page_payloads, all_organic

    def persist_results(
        self,
        db: Session,
        item: JobItem,
        page_payloads: list[tuple[int, int, dict, list[OrganicResult]]],
        organic: list[OrganicResult],
    ) -> None:
        for page_number, status_code, raw, page_organic in page_payloads:
            db.add(
                SerpRawResponse(
                    job_item_id=item.id,
                    provider=self.provider.name,
                    page_number=page_number,
                    http_status=status_code,
                    response_json=raw,
                )
            )

            for result in page_organic:
                db.add(
                    SerpOrganicResult(
                        job_item_id=item.id,
                        page_number=page_number,
                        rank=result.rank,
                        title=result.title,
                        url=result.link,
                        display_link=result.display_link,
                        snippet=result.snippet,
                        raw_domain=extract_domain(result.link),
                    )
                )

        matched, best_position, matched_url, matched_positions, matched_urls = find_domain_matches(
            item.target_domain, organic
        )
        item.matched = matched
        item.best_position = best_position
        item.matched_url = matched_url
        item.matched_positions = matched_positions
        item.matched_urls = matched_urls

    async def process_item(self, db: Session, item: JobItem) -> None:
        request = self.provider_request_to_query(item)
        item.provider_request_payload = {
            "q": request.keyword,
            "hl": request.language,
            "gl": request.country,
            "page": request.page,
            "max_pages": item.max_pages,
        }
        page_payloads, organic = await self.fetch_multi_page(request, item.max_pages)
        self.persist_results(db, item, page_payloads, organic)
