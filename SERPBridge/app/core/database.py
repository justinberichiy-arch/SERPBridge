from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(
    f"sqlite:///{settings.sqlite_path}",
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.db.models import Job, JobItem, SerpOrganicResult, SerpRawResponse  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _run_sqlite_migrations()


def _run_sqlite_migrations() -> None:
    migrations = {
        "job_items": {
            "max_pages": "ALTER TABLE job_items ADD COLUMN max_pages INTEGER DEFAULT 1",
            "matched_positions": "ALTER TABLE job_items ADD COLUMN matched_positions JSON",
            "matched_urls": "ALTER TABLE job_items ADD COLUMN matched_urls JSON",
        },
        "serp_raw_responses": {
            "page_number": "ALTER TABLE serp_raw_responses ADD COLUMN page_number INTEGER DEFAULT 1",
        },
        "serp_organic_results": {
            "page_number": "ALTER TABLE serp_organic_results ADD COLUMN page_number INTEGER DEFAULT 1",
        },
    }

    with engine.begin() as conn:
        for table_name, table_migrations in migrations.items():
            existing_columns = {
                row[1]
                for row in conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            }
            for column_name, sql in table_migrations.items():
                if column_name not in existing_columns:
                    conn.execute(text(sql))
