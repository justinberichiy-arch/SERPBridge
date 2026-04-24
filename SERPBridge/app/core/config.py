from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProviderAccount:
    provider: str
    name: str
    api_key: str
    base_url: str
    enabled: bool = True


@dataclass(frozen=True)
class Settings:
    sqlite_path: Path
    export_dir: Path
    tasks_csv_path: Path
    worker_concurrency: int
    max_retries: int
    default_gl: str
    default_hl: str
    default_page: int
    default_max_pages: int
    default_provider_account: str | None
    provider_accounts: dict[str, ProviderAccount]


def get_settings() -> Settings:
    from app.local_settings import SETTINGS

    SETTINGS.export_dir.mkdir(parents=True, exist_ok=True)
    SETTINGS.tasks_csv_path.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return SETTINGS
