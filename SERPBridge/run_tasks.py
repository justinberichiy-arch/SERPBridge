import asyncio
import json
from time import perf_counter

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.services.job_service import JobService


def log_progress(message: str) -> None:
    print(message, flush=True)


def main() -> None:
    started_at = perf_counter()
    settings = get_settings()
    csv_path = settings.tasks_csv_path
    if not csv_path.exists():
        raise FileNotFoundError(f"Task file not found: {csv_path}")

    csv_text = csv_path.read_text(encoding="utf-8")

    init_db()
    service = JobService()
    with SessionLocal() as db:
        job = service.create_job_from_csv(
            db=db,
            csv_text=csv_text,
            country=settings.default_gl,
            language=settings.default_hl,
            device="desktop",
            page=settings.default_page,
            max_pages=settings.default_max_pages,
            provider_account=settings.default_provider_account,
        )
        print(f"Started job: id={job.id} provider={job.provider}", flush=True)
        print(
            f"Task file: {csv_path} | total_items={job.total_items} | "
            f"pages={settings.default_page}-{settings.default_page + settings.default_max_pages - 1}",
            flush=True,
        )
        job = asyncio.run(service.run_job(db, job.id, progress_callback=log_progress))
        elapsed_seconds = perf_counter() - started_at
        items = service.list_job_items(db, job.id)

        print(f"Job finished: id={job.id} status={job.status}")
        print(f"Provider account: {job.provider}")
        print(f"Task file: {csv_path}")
        print(f"Elapsed: {elapsed_seconds:.2f}s")
        print(f"Export CSV: {job.export_csv_path}")

        matched_count = 0
        failed_count = 0
        for item in items:
            if item.status == "failed":
                failed_count += 1
                print(f"FAILED: {item.target_domain} | {item.keyword} | {item.error_message}")
                continue

            if item.matched:
                matched_count += 1
                matched_entries = [
                    {"position": position, "url": url}
                    for position, url in zip(item.matched_positions or [], item.matched_urls or [])
                ]
                print(
                    f"MATCHED: {item.target_domain} | {item.keyword} | "
                    f"entries={json.dumps(matched_entries, ensure_ascii=False)}"
                )

        print(f"Matched items: {matched_count}")
        print(f"Failed items: {failed_count}")


if __name__ == "__main__":
    main()
