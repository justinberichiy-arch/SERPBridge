import csv
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Job


def export_job_to_csv(db: Session, job: Job) -> Path:
    settings = get_settings()
    output_path = settings.export_dir / f"job_{job.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"

    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "job_id",
                "job_item_id",
                "provider",
                "target_domain",
                "keyword",
                "matched",
                "best_position",
                "matched_url",
                "matched_entries",
                "country",
                "language",
                "device",
                "status",
                "error_message",
                "checked_at",
            ],
        )
        writer.writeheader()
        for item in job.items:
            matched_entries = json.dumps(
                [
                    {"position": position, "url": url}
                    for position, url in zip(item.matched_positions or [], item.matched_urls or [])
                ],
                ensure_ascii=False,
            )
            writer.writerow(
                {
                    "job_id": job.id,
                    "job_item_id": item.id,
                    "provider": job.provider,
                    "target_domain": item.target_domain,
                    "keyword": item.keyword,
                    "matched": item.matched,
                    "best_position": item.best_position,
                    "matched_url": item.matched_url,
                    "matched_entries": matched_entries,
                    "country": item.country,
                    "language": item.language,
                    "device": item.device,
                    "status": item.status,
                    "error_message": item.error_message,
                    "checked_at": item.finished_at.isoformat() if item.finished_at else "",
                }
            )

    return output_path
