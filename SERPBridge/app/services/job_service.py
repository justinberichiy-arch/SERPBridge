from datetime import datetime
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.enums import JobItemStatus, JobStatus
from app.db.models import Job, JobItem
from app.providers.registry import get_provider_account
from app.services.export_service import export_job_to_csv
from app.services.import_service import parse_domain_keywords_csv
from app.services.serp_service import SerpService


class JobService:
    def create_job_from_csv(
        self,
        db: Session,
        csv_text: str,
        country: str,
        language: str,
        device: str,
        page: int,
        max_pages: int,
        provider_account: str | None,
    ) -> Job:
        rows = parse_domain_keywords_csv(csv_text)
        selected_account = get_provider_account(provider_account)
        job = Job(
            provider=selected_account.name,
            status=JobStatus.PENDING,
            total_items=len(rows),
            pending_items=len(rows),
        )
        db.add(job)
        db.flush()

        for row in rows:
            db.add(
                JobItem(
                    job_id=job.id,
                    target_domain=row["target_domain"],
                    keyword=row["keyword"],
                    country=country,
                    language=language,
                    device=device,
                    page=page,
                    max_pages=max_pages,
                    status=JobItemStatus.PENDING,
                )
            )
        db.commit()
        db.refresh(job)
        return job

    def get_job(self, db: Session, job_id: int) -> Job | None:
        stmt = select(Job).where(Job.id == job_id).options(selectinload(Job.items))
        return db.scalars(stmt).first()

    def list_job_items(self, db: Session, job_id: int) -> list[JobItem]:
        stmt = select(JobItem).where(JobItem.job_id == job_id).order_by(JobItem.id)
        return list(db.scalars(stmt).all())

    async def run_job(
        self,
        db: Session,
        job_id: int,
        progress_callback: Callable[[str], None] | None = None,
    ) -> Job:
        job = self.get_job(db, job_id)
        if job is None:
            raise ValueError("Job not found")

        job.status = JobStatus.RUNNING
        job.started_at = job.started_at or datetime.utcnow()
        db.commit()

        serp_service = SerpService(provider_account=job.provider)
        any_success = False
        any_failure = False
        settings = get_settings()

        groups: dict[tuple[str, str, str, str, int, int], list[JobItem]] = {}
        for item in job.items:
            if item.status == JobItemStatus.SUCCESS:
                continue
            group_key = (item.keyword, item.country, item.language, item.device, item.page, item.max_pages)
            groups.setdefault(group_key, []).append(item)

        total_groups = len(groups)
        for group_index, (group_key, items) in enumerate(groups.items(), start=1):
            for item in items:
                item.status = JobItemStatus.RUNNING
                item.started_at = datetime.utcnow()
            db.commit()

            request_item = items[0]
            request_payload = {
                "q": request_item.keyword,
                "hl": request_item.language,
                "gl": request_item.country,
                "page": request_item.page,
                "max_pages": request_item.max_pages,
            }

            last_error: str | None = None
            succeeded = False
            for attempt in range(1, settings.max_retries + 2):
                try:
                    current_page = request_item.page - 1

                    def on_page_done(page_number: int) -> None:
                        nonlocal current_page
                        current_page = page_number
                        if progress_callback:
                            progress_callback(
                                f"Running keyword='{request_item.keyword}' for {len(items)} domain(s), pages={page_number}"
                            )

                    if progress_callback and attempt > 1:
                        progress_callback(f"Retry {attempt - 1}/{settings.max_retries}: keyword='{request_item.keyword}'")
                    page_payloads, organic = await serp_service.fetch_multi_page(
                        request=serp_service.provider_request_to_query(request_item),
                        max_pages=request_item.max_pages,
                        page_callback=on_page_done,
                    )
                    for item in items:
                        item.provider_request_payload = request_payload
                        item.retry_count = attempt - 1
                        serp_service.persist_results(db, item, page_payloads, organic)
                        item.status = JobItemStatus.SUCCESS
                        item.error_message = None
                        item.finished_at = datetime.utcnow()
                        any_success = True
                    db.commit()
                    succeeded = True
                    if progress_callback:
                        for item in items:
                            if item.matched and item.matched_positions and item.matched_urls:
                                for position, url in zip(item.matched_positions, item.matched_urls):
                                    progress_callback(f"{item.target_domain}, {item.keyword}, {position}, {url}")
                    break
                except Exception as exc:  # noqa: BLE001
                    last_error = str(exc)
                    if attempt <= settings.max_retries:
                        continue

            if not succeeded:
                for item in items:
                    item.retry_count = settings.max_retries
                    item.status = JobItemStatus.FAILED
                    item.error_message = last_error
                    item.finished_at = datetime.utcnow()
                any_failure = True
                db.commit()
                if progress_callback:
                    failed_page = current_page + 1 if current_page < request_item.page + request_item.max_pages - 1 else current_page
                    progress_callback(
                        f"FAILED: keyword='{request_item.keyword}', pages={failed_page}, error={last_error}"
                    )

        self._refresh_job_counts(job)
        if any_failure and any_success:
            job.status = JobStatus.PARTIAL
        elif any_failure:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.COMPLETED
        job.finished_at = datetime.utcnow()

        output_path = export_job_to_csv(db, job)
        job.export_csv_path = str(output_path)
        db.commit()
        db.refresh(job)
        return job

    def _refresh_job_counts(self, job: Job) -> None:
        pending = 0
        success = 0
        failed = 0
        for item in job.items:
            if item.status == JobItemStatus.PENDING:
                pending += 1
            elif item.status == JobItemStatus.SUCCESS:
                success += 1
            elif item.status == JobItemStatus.FAILED:
                failed += 1
        job.pending_items = pending
        job.success_items = success
        job.failed_items = failed
