# Level 3: Job Market Pipeline

A small data pipeline that tracks the job market I'm trying to break into.

It pulls from two public sources, loads them into a local warehouse, cleans them with dbt, and keeps a **history** of remote data jobs so I can see when a listing opened and when it closed.

This is Level 3 of my learn-in-public data engineering series. Level 1 was a GitHub ETL, Level 2 was an RSS pipeline on AWS. This one repeats the basics and adds new skills on purpose:

- incremental loading (do not re-fetch what you already have)
- SCD Type 2 (keep history when data changes or disappears)
- deliberate data quality tests
- a new warehouse (DuckDB) and a new orchestrator (Airflow, in progress)

<img width="2250" height="1335" alt="architecture" src="https://github.com/user-attachments/assets/13280ce8-7b87-40a4-87a2-576aa43f030b" />


## The idea in 30 seconds

Think of it like two mail carriers and one filing cabinet.

1. **Hacker News carrier.** New stories show up all day. The carrier remembers the last story ID they saw, so next time they only pick up newer ones. That is *incremental loading*.
2. **RemoteOK carrier.** This source only tells you what is open *right now*. It never says "this job closed". So the carrier brings the whole current list every time.
3. **The filing cabinet (DuckDB).** Everything lands in a raw drawer first. dbt then cleans it into a tidy drawer.
4. **The history book.** Each time dbt runs a snapshot, it compares today's RemoteOK list to what it saw before. If a job vanished, it writes down *when*. That is *SCD Type 2*.

## Status

| Piece | State |
| --- | --- |
| Hacker News extractor (watermark) and loader | Built, verified on real data |
| RemoteOK extractor and loader | Built, verified on real data |
| dbt staging models | Built, verified |
| dbt tests (7) and source freshness | Built, passing |
| dbt snapshot (SCD Type 2) | Built, verified |
| Airflow DAG | **Planned, next step** |
| dbt marts (analysis tables) | Planned |

## Two sources, two loading patterns

| | Hacker News | RemoteOK |
| --- | --- | --- |
| What it gives me | A stream of new stories | The jobs open right now |
| Extract pattern | Incremental, using a watermark | Full snapshot every run |
| Landing file | `hn_stories.jsonl` (appended) | `remoteok_jobs.jsonl` (replaced) |
| Load pattern | Insert new rows, skip duplicates | Replace the whole table |
| Where history comes from | Rows are only ever added | dbt snapshot (SCD Type 2) |

The RemoteOK loader replaces the table on purpose. The raw table always means "what is open now", and the snapshot is what remembers the past.

## How SCD Type 2 works here

`remoteok_jobs_snapshot` keeps one row per version of a listing. The important setting is `hard_deletes='invalidate'`, which tells dbt: if a `job_id` is missing from today's data, close its row instead of ignoring it.

| job_id | job_title | dbt_valid_from | dbt_valid_to |
| --- | --- | --- | --- |
| 101 | Data Engineer | Oct 1 | null (still open) |
| 102 | Analytics Engineer | Oct 1 | Oct 9 (closed) |

Listings that closed:

```sql
select job_id, job_title, company, dbt_valid_from, dbt_valid_to
from snapshots.remoteok_jobs_snapshot
where dbt_valid_to is not null;
```

The snapshot watches these columns for changes: `job_title`, `company`, `tags`, `location`, `salary_min`, `salary_max`, `url`.

## Data quality

| Check | What it protects against |
| --- | --- |
| `unique` and `not_null` on `story_id` and `job_id` | Duplicate or missing IDs |
| `not_null` on `posted_at` and `job_title` | Broken dates or titles |
| `assert_remoteok_jobs_not_empty` (custom test) | The silent failure where the API breaks and the table quietly becomes empty |
| Source freshness (warn at 24h, error at 72h) | A pipeline that stopped running without anyone noticing |

The custom test exists because the RemoteOK loader replaces its table every run. If the extractor ever returned nothing, there would be no error, just an empty table. The test turns that into a loud failure.

## Tech stack

| Layer | Tool |
| --- | --- |
| Extract and load | Python (standard library for HTTP) |
| Warehouse | DuckDB (one local file, free) |
| Transform, test, snapshot | dbt with the `dbt-duckdb` adapter |
| Orchestration | Apache Airflow (planned) |

## Project structure

```
de-level3-pipeline/
├── dags/                         # Airflow DAG goes here (planned)
├── docs/
│   ├── architecture.svg
│   └── architecture.png
├── extractors/
│   ├── hackernews.py             # incremental extract, watermark file
│   ├── load_hackernews.py        # dedupe on id, insert new rows only
│   ├── remoteok.py               # tags=data pre-filter + title match
│   ├── load_remoteok.py          # replace the raw table each run
│   ├── inspect_warehouse.py      # look inside the warehouse (before/after dbt)
│   ├── simulate_closure.py       # demo helper: pretend a job was filled
│   └── data/                     # generated files and warehouse.duckdb (git-ignored)
└── dbt/
    ├── dbt_project.yml
    ├── profiles.yml              # points at ../extractors/data/warehouse.duckdb
    ├── models/staging/
    │   ├── sources.yml           # raw tables + freshness rules
    │   ├── schema.yml            # not_null / unique tests
    │   ├── stg_hackernews_stories.sql
    │   └── stg_remoteok_jobs.sql
    ├── snapshots/
    │   └── remoteok_jobs_snapshot.sql
    └── tests/
        └── assert_remoteok_jobs_not_empty.sql
```

## Run it yourself

I build this on Windows with PowerShell, so the commands use the `py` launcher. On macOS or Linux, use `python3` instead of `py`.

**1. Set up**

```powershell
git clone <this-repo-url>
cd de-level3-pipeline
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

**2. Extract and load** (run from the `extractors` folder)

```powershell
cd extractors
py hackernews.py
py load_hackernews.py
py remoteok.py
py load_remoteok.py
```

Run `hackernews.py` twice. The second run only fetches stories that appeared in between.

**3. Transform, test, snapshot** (run from the `dbt` folder)

```powershell
cd ..\dbt
py -m dbt.cli.main run --profiles-dir .
py -m dbt.cli.main test --profiles-dir .
py -m dbt.cli.main snapshot --profiles-dir .
py -m dbt.cli.main source freshness --profiles-dir .
```

I call dbt as `py -m dbt.cli.main` because on my machine pip put `dbt.exe` in a folder that is not on PATH. If `dbt` works for you, use it directly.

**4. Watch a listing close**

Run `dbt snapshot` once, then pretend a job was filled (from the `extractors` folder):

```powershell
py simulate_closure.py
```

Run `dbt snapshot` again, then check the result from the `extractors` folder (the script prints the exact query for you). That job's `dbt_valid_to` is now filled in, and every other listing is still open.

To compare the data before and after dbt, run `py inspect_warehouse.py before` and `py inspect_warehouse.py after` around your `dbt run`.

## Things that went wrong (and what I learned)

- **A source that lied.** Remotive's public API ignored every query parameter (`search`, `category`, `limit`) and always returned the same 15 generic jobs. I proved it by checking the API's own `job-count` field before blaming my code, then switched to RemoteOK.
- **A reserved word.** Hacker News gives each story a `by` field. `by` is reserved in SQL, so it has to be written as `"by"` in DuckDB. dbt renames it to `author`.
- **Server filter plus client filter.** RemoteOK's plain feed had zero matching titles on one run. Pre-filtering with `tags=data` on the server gave a bigger pool (about 100), and a strict title match on my side kept the real ones (16).
- **Cost walls are real.** I planned on BigQuery, but billing in Nigeria required a $30 prepayment. DuckDB keeps the same dbt workflow for free.

## Roadmap

- [ ] Airflow DAG: two extracts in parallel, then load, then `dbt run`, `dbt test`, `dbt snapshot`
- [ ] A marts layer, for example which skill tags appear most in open roles
- [ ] Run it on a schedule so the history builds up on its own
- [ ] Write-up of the full build for my Towards Data Science series

## Author

Ibrahim Salami, systems analyst moving into data engineering.
[ibrahimsalami.dev](https://ibrahimsalami.dev) | [YouTube](https://youtube.com/@ibbysalam)
