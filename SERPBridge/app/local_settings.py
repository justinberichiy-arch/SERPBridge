from pathlib import Path

from app.core.config import ProviderAccount, Settings


BASE_DIR = Path(__file__).resolve().parent.parent

SETTINGS = Settings(
    sqlite_path=BASE_DIR / "data" / "rank_storage.db",
    export_dir=BASE_DIR / "exports",
    tasks_csv_path=BASE_DIR / "inputs" / "tasks.csv",
    worker_concurrency=2,
    max_retries=2,
    default_gl="us",
    default_hl="en",
    default_page=1,
    default_max_pages=10,
    default_provider_account="serpbase_primary",
    provider_accounts={
        "serpbase_primary": ProviderAccount(
            provider="serpbase",
            name="serpbase_primary",
            api_key="",
            base_url="",
            enabled=True,
        ),
        "serper_primary": ProviderAccount(
            provider="serper",
            name="serper_primary",
            api_key="9",
            base_url="",
            enabled=True,
        ),
    },
)
