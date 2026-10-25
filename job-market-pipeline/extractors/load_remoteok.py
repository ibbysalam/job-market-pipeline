"""
Loads data/remoteok_jobs.jsonl into the local DuckDB warehouse.

Same pattern as load_remotive.py was: REPLACES the whole table every
run, since remoteok_jobs.jsonl always holds the full current snapshot
of matching listings. History of what opened/closed over time is dbt
snapshot's job, built on top of this table.

Usage:
    python load_remoteok.py
"""

from pathlib import Path
import duckdb

HERE = Path(__file__).parent
JSONL_PATH = HERE / "data" / "remoteok_jobs.jsonl"
DB_PATH = HERE / "data" / "warehouse.duckdb"

EXPECTED_COLUMNS = {
    "id": "VARCHAR",
    "position": "VARCHAR",
    "company": "VARCHAR",
    "tags": "VARCHAR[]",
    "location": "VARCHAR",
    "salary_min": "BIGINT",
    "salary_max": "BIGINT",
    "url": "VARCHAR",
    "date": "VARCHAR",
}


def run() -> None:
    if not JSONL_PATH.exists():
        print(f"No data file found at {JSONL_PATH}. Run remoteok.py first.")
        return

    con = duckdb.connect(str(DB_PATH))

    columns_literal = ", ".join(f"'{name}': '{dtype}'" for name, dtype in EXPECTED_COLUMNS.items())
    select_cols = ", ".join(f'"{name}"' for name in EXPECTED_COLUMNS.keys())

    con.execute(
        f"""
        CREATE OR REPLACE TABLE raw_remoteok_jobs AS
        SELECT {select_cols}, current_timestamp AS loaded_at
        FROM read_json_auto(?, columns = {{{columns_literal}}})
        """,
        [str(JSONL_PATH)],
    )

    row_count = con.execute("SELECT COUNT(*) FROM raw_remoteok_jobs").fetchone()[0]
    con.close()

    print(f"raw_remoteok_jobs now holds {row_count} current listings")
    print(f"Database file: {DB_PATH}")


if __name__ == "__main__":
    run()
