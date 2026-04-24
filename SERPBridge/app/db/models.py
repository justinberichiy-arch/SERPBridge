from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(50), default="serpbase")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    pending_items: Mapped[int] = mapped_column(Integer, default=0)
    success_items: Mapped[int] = mapped_column(Integer, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, default=0)
    export_csv_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["JobItem"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class JobItem(Base):
    __tablename__ = "job_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    target_domain: Mapped[str] = mapped_column(String(255), index=True)
    keyword: Mapped[str] = mapped_column(String(500), index=True)
    country: Mapped[str] = mapped_column(String(10), default="us")
    language: Mapped[str] = mapped_column(String(10), default="en")
    device: Mapped[str] = mapped_column(String(20), default="desktop")
    page: Mapped[int] = mapped_column(Integer, default=1)
    max_pages: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    matched: Mapped[bool] = mapped_column(Boolean, default=False)
    best_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    matched_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    matched_positions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    matched_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)
    provider_request_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    job: Mapped["Job"] = relationship(back_populates="items")
    raw_responses: Mapped[list["SerpRawResponse"]] = relationship(
        back_populates="job_item", cascade="all, delete-orphan"
    )
    organic_results: Mapped[list["SerpOrganicResult"]] = relationship(
        back_populates="job_item", cascade="all, delete-orphan"
    )


class SerpRawResponse(Base):
    __tablename__ = "serp_raw_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_item_id: Mapped[int] = mapped_column(ForeignKey("job_items.id"), index=True)
    provider: Mapped[str] = mapped_column(String(50))
    page_number: Mapped[int] = mapped_column(Integer, default=1)
    http_status: Mapped[int] = mapped_column(Integer)
    response_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job_item: Mapped["JobItem"] = relationship(back_populates="raw_responses")


class SerpOrganicResult(Base):
    __tablename__ = "serp_organic_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_item_id: Mapped[int] = mapped_column(ForeignKey("job_items.id"), index=True)
    page_number: Mapped[int] = mapped_column(Integer, default=1)
    rank: Mapped[int] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(1000))
    display_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)

    job_item: Mapped["JobItem"] = relationship(back_populates="organic_results")
