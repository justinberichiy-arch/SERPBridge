from app.core.config import get_settings
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.job import ImportCsvRequest, JobItemRead, JobRead
from app.services.job_service import JobService


router = APIRouter()
job_service = JobService()


@router.post("/import-csv", response_model=JobRead)
def import_csv(request: ImportCsvRequest, db: Session = Depends(get_db)) -> JobRead:
    try:
        job = job_service.create_job_from_csv(
            db=db,
            csv_text=request.csv_text,
            country=request.country,
            language=request.language,
            device=request.device,
            page=request.page,
            max_pages=request.max_pages,
            provider_account=get_settings().default_provider_account,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JobRead.model_validate(job)


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db)) -> JobRead:
    job = job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobRead.model_validate(job)


@router.get("/{job_id}/items", response_model=list[JobItemRead])
def get_job_items(job_id: int, db: Session = Depends(get_db)) -> list[JobItemRead]:
    job = job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return [JobItemRead.model_validate(item) for item in job_service.list_job_items(db, job_id)]


@router.post("/{job_id}/run", response_model=JobRead)
async def run_job(job_id: int, db: Session = Depends(get_db)) -> JobRead:
    try:
        job = await job_service.run_job(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JobRead.model_validate(job)


@router.get("/{job_id}/export")
def get_export(job_id: int, db: Session = Depends(get_db)) -> FileResponse:
    job = job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.export_csv_path:
        raise HTTPException(status_code=404, detail="Export not found")
    path = Path(job.export_csv_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Export file missing")
    return FileResponse(path=path, filename=path.name, media_type="text/csv")
