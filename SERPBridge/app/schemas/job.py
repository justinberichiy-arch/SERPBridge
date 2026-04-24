from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImportCsvRequest(BaseModel):
    csv_text: str
    country: str = "us"
    language: str = "en"
    device: str = "desktop"
    page: int = Field(default=1, ge=1)
    max_pages: int = Field(default=1, ge=1, le=10)


class JobItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_domain: str
    keyword: str
    country: str
    language: str
    device: str
    page: int
    max_pages: int
    status: str
    retry_count: int
    error_message: str | None
    matched: bool
    best_position: int | None
    matched_url: str | None
    matched_positions: list[int] | None
    matched_urls: list[str] | None
    created_at: datetime
    finished_at: datetime | None


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    status: str
    total_items: int
    pending_items: int
    success_items: int
    failed_items: int
    export_csv_path: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
