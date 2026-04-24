import asyncio

from sqlalchemy import select

from app.core.database import SessionLocal, init_db
from app.core.enums import JobStatus
from app.db.models import Job
from app.services.job_service import JobService


async def run_pending_jobs_forever(poll_interval_seconds: int = 5) -> None:
    init_db()
    job_service = JobService()
    while True:
        with SessionLocal() as db:
            stmt = select(Job.id).where(Job.status == JobStatus.PENDING).order_by(Job.created_at)
            pending_ids = list(db.scalars(stmt).all())
        for job_id in pending_ids:
            with SessionLocal() as db:
                await job_service.run_job(db, job_id)
        await asyncio.sleep(poll_interval_seconds)


if __name__ == "__main__":
    asyncio.run(run_pending_jobs_forever())
