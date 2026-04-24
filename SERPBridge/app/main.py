from fastapi import FastAPI

from app.api.routes.jobs import router as jobs_router
from app.core.database import init_db


app = FastAPI(title="SERPBridge", version="0.1.0")
app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])


@app.on_event("startup")
def on_startup() -> None:
    init_db()
