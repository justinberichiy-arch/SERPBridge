# SERPBridge

Python service for batch SERP rank checks using provider adapters.

## Current scope

- SerpBase as the first provider
- Google organic result matching
- CSV import format: `domain,keywords`
- SQLite persistence
- CSV export per finished job

## Task file

```csv
domain,keywords
openai.com,chatgpt###gpt api###ai chatbot
notion.so,notion ai###docs app
```

Put the actual task file here:

- [tasks.csv](/Users/sdlk/Documents/cursor_projects/SERPBridge/inputs/tasks.csv)

Example template:

- [tasks.csv.example](/Users/sdlk/Documents/cursor_projects/SERPBridge/inputs/tasks.csv.example)

## Config file

All local config is inside:

- [local_settings.py](/Users/sdlk/Documents/cursor_projects/SERPBridge/app/local_settings.py)

You can edit:

- API key
- database file path
- export directory
- task CSV path
- default country and language
- default start page
- default max pages

## Run simple batch mode

```bash
python3 run_tasks.py
```

This mode reads:

- [tasks.csv](/Users/sdlk/Documents/cursor_projects/SERPBridge/inputs/tasks.csv)

And writes:

- [rank_storage.db](/Users/sdlk/Documents/cursor_projects/SERPBridge/data/rank_storage.db)
- [exports](/Users/sdlk/Documents/cursor_projects/SERPBridge/exports)

## Run API

```bash
uvicorn app.main:app --reload
```

## Run worker

```bash
python3 -m app.worker.runner
```

## Main endpoints

- `POST /jobs/import-csv`
- `GET /jobs/{job_id}`
- `GET /jobs/{job_id}/items`
- `POST /jobs/{job_id}/run`
- `GET /jobs/{job_id}/export`

## Notes

- `max_pages` can be set when creating a job, for example `10` means fetch pages `1-10`.
- Within a single job, identical keyword queries with the same locale/device/page settings are fetched once and then matched against all requested domains.
