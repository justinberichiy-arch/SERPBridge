# SERPBridge Project Plan

## 1. Goal

Build a Python-based SERP aggregation and rank checking service with these initial constraints:

- First provider: SerpBase
- Search engine scope: Google web search
- Batch size: hundreds of keywords per job
- Input format: `domain,keywords` where `keywords` uses `###` as separator
- Persistence: SQLite
- Export: each completed job also writes a CSV file
- Extensibility: additional providers can be added later without rewriting core logic

## 2. Current Provider Assumption

Based on the current public SerpBase example:

- Endpoint: `POST https://api.serpbase.dev/google/search`
- Headers:
  - `Content-Type: application/json`
  - `X-API-Key: <api_key>`
- Example body:
  - `q`
  - `hl`
  - `gl`
  - `page`
- Example response fields include:
  - `status`
  - `query`
  - `page`
  - `organic[]`
  - `organic[].rank`
  - `organic[].title`
  - `organic[].link`
  - `organic[].snippet`

Implementation should treat this as the provider contract to start with, while keeping the adapter isolated in case the docs expand or change later.

Sources:
- [SerpBase marketing page](https://www.serpcore.dev/)
- [Requested docs URL](https://serpbase.dev/docs)

## 3. Recommended Stack

- Language: Python 3.11+
- API layer: FastAPI
- Validation: Pydantic
- HTTP client: httpx
- Database: SQLite
- ORM/data access: SQLAlchemy 2.0
- Background execution: custom worker using SQLite-backed jobs plus `asyncio`
- Tests: pytest

## 4. Why This Shape

### FastAPI

Even if batch execution happens in the background, the project still benefits from an API layer:

- submit batch jobs
- inspect progress
- download results
- support future frontend or internal automation

### SQLite

SQLite is sufficient for the first version if we keep deployment single-machine and use a modest number of workers. The important constraint is to avoid many competing writer processes. A single worker process with controlled concurrency is the safe default.

### No Redis / No Celery for v1

For this scale, the simpler system is better:

- one API process
- one worker process
- SQLite as the job store
- bounded async HTTP concurrency for provider calls

This keeps the operational surface small while still supporting hundreds of keywords per job.

## 5. Core User Flow

1. User uploads or submits a batch in this format:

```csv
domain,keywords
openai.com,chatgpt###gpt api###ai chatbot
notion.so,notion ai###docs app###note taking app
```

2. System expands each row into multiple job items:

```text
openai.com + chatgpt
openai.com + gpt api
openai.com + ai chatbot
```

3. A batch job is created in SQLite.

4. Worker picks pending items and sends requests to SerpBase with provider-level concurrency limits.

5. For each keyword:

- raw provider response is saved
- normalized SERP rows are saved
- target domain rank is computed

6. When the full job finishes:

- job status becomes `completed` or `partial`
- a CSV export file is written to disk

## 6. Input Rules

Initial batch import format:

```csv
domain,keywords
example.com,keyword1###keyword2###keyword3
```

Parsing rules:

- `domain` is required
- `keywords` is required
- split `keywords` by `###`
- trim spaces around each keyword
- remove empty keywords
- de-duplicate identical keywords within the same row
- normalize domain before storage

Optional later extension:

```csv
domain,country,language,device,keywords
example.com,us,en,desktop,keyword1###keyword2
```

## 7. Matching Rules

Rank matching should use normalized domain comparison.

Default v1 rule:

- extract result hostname from each organic result URL
- compare against submitted `domain`
- treat subdomains as match only if they belong to the same registrable domain

Examples for `openai.com`:

- `openai.com` -> match
- `www.openai.com` -> match
- `platform.openai.com` -> match
- `help.openai.com` -> match
- `exampleopenai.com` -> no match

Store both:

- `best_position`
- `matched_url`

If no result matches the target domain in the fetched page range, mark as not found.

## 8. Execution Model

Because jobs may contain hundreds of keywords, request execution should not be fully synchronous.

Recommended model:

- API server accepts job creation
- worker process polls pending job items
- worker uses `asyncio.Semaphore` for bounded concurrency
- concurrency should be configurable, default around `5`

Why bounded concurrency:

- avoids provider rate limit issues
- reduces retry storms
- keeps SQLite writes manageable

## 9. Retry Model

Per job item:

- `max_retries = 2` by default
- retry on transient errors:
  - timeout
  - 429 / rate limit
  - 5xx provider errors
- do not retry on validation or auth failures

Store on each item:

- retry count
- last error message
- last attempted at

## 10. Data Model

### jobs

Represents one submitted batch.

Suggested fields:

- `id`
- `provider`
- `status` (`pending`, `running`, `completed`, `partial`, `failed`)
- `total_items`
- `pending_items`
- `success_items`
- `failed_items`
- `created_at`
- `started_at`
- `finished_at`
- `export_csv_path`

### job_items

Represents one domain + keyword task.

Suggested fields:

- `id`
- `job_id`
- `target_domain`
- `keyword`
- `country`
- `language`
- `device`
- `page`
- `status` (`pending`, `running`, `success`, `failed`)
- `retry_count`
- `error_message`
- `matched`
- `best_position`
- `matched_url`
- `provider_request_payload`
- `created_at`
- `started_at`
- `finished_at`

### serp_raw_responses

Stores full raw provider payloads for traceability.

Suggested fields:

- `id`
- `job_item_id`
- `provider`
- `http_status`
- `response_json`
- `created_at`

### serp_organic_results

Stores normalized organic rows.

Suggested fields:

- `id`
- `job_item_id`
- `rank`
- `title`
- `url`
- `display_link`
- `snippet`
- `raw_domain`

## 11. CSV Export

Each completed job should write a CSV file under a local export directory, for example:

```text
exports/job_<job_id>_<timestamp>.csv
```

Recommended exported columns:

- `job_id`
- `job_item_id`
- `provider`
- `target_domain`
- `keyword`
- `matched`
- `best_position`
- `matched_url`
- `country`
- `language`
- `device`
- `status`
- `error_message`
- `checked_at`

Why export CSV in addition to SQLite:

- easy delivery to non-technical users
- convenient for spreadsheet analysis
- useful as a job artifact

## 12. Project Structure

```text
app/
  api/
    routes/
      jobs.py
      exports.py
  core/
    config.py
    database.py
    enums.py
    logging.py
  db/
    models.py
    session.py
  providers/
    base.py
    serpbase/
      client.py
      normalizer.py
  schemas/
    job.py
    serp.py
  services/
    import_service.py
    job_service.py
    serp_service.py
    rank_service.py
    export_service.py
  worker/
    runner.py
    scheduler.py
  utils/
    domains.py
    csv_io.py
tests/
docs/
exports/
```

## 13. Provider Abstraction

Even with only one provider at the start, define a provider interface now:

```python
class BaseSerpProvider:
    name: str

    async def fetch(self, request: QueryRequest) -> dict:
        ...

    def extract_organic(self, raw: dict) -> list[OrganicResult]:
        ...
```

This prevents the core job flow from depending on SerpBase-specific response shapes.

## 14. API Design

Recommended first endpoints:

- `POST /jobs/import-csv`
  - upload CSV
  - create batch job

- `GET /jobs/{job_id}`
  - return job status and counts

- `GET /jobs/{job_id}/items`
  - paginated item results

- `POST /jobs/{job_id}/run`
  - optional manual trigger if worker is not auto-polling

- `GET /jobs/{job_id}/export`
  - download exported CSV

For smaller ad hoc checks:

- `POST /rank-check`

## 15. Processing Logic Per Item

Per `job_item`:

1. build SerpBase request
2. call provider
3. save raw response
4. normalize `organic[]`
5. save normalized rows
6. compute target domain match
7. update item result

If provider response has no `organic`, treat as empty result set, not immediate failure, unless the provider indicates an error state.

## 16. Configuration

Environment variables:

- `SERPBASE_API_KEY`
- `SQLITE_PATH`
- `EXPORT_DIR`
- `WORKER_CONCURRENCY`
- `MAX_RETRIES`
- `DEFAULT_GL`
- `DEFAULT_HL`
- `DEFAULT_PAGE`

## 17. Operational Constraints

Initial safe defaults:

- one worker process
- concurrency `5`
- single SQLite database file
- local filesystem export directory

If volume grows later:

- move from SQLite to PostgreSQL
- move from local worker loop to Redis-backed queue
- add provider-level rate limit policies

## 18. MVP Scope

Version 1 should include only:

- SerpBase provider integration
- batch import with `domain,keywords`
- background execution
- SQLite persistence
- CSV export
- job status APIs
- organic result rank matching

Not required for v1:

- multi-provider routing
- caching
- frontend UI
- scheduled recurring jobs
- multi-user auth
- distributed workers

## 19. Next Build Order

1. scaffold Python project structure
2. define SQLite schema
3. implement CSV import and row expansion
4. implement SerpBase client
5. implement rank matching
6. implement worker loop
7. implement CSV export
8. implement FastAPI endpoints
9. add tests around parsing, matching, and job state transitions
