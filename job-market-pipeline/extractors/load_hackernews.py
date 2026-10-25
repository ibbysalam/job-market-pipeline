"""
Loads data/hn_stories.jsonl into a local DuckDB file.

Safe to run repeatedly: the `id` column is a primary key, so re-running
this after the extractor appends new lines will only insert rows that
aren't already in the table. Already-loaded rows are skipped, not
duplicated or overwritten.

Usage:
    python load_hackernews.py
"""

from pathlib import Path
import duckdb

HERE = Path(__file__).parent
JSONL_PATH = HERE / "data" / "hn_stories.jsonl"
DB_PATH = HERE / "data" / "warehouse.duckdb"

# Fixed schema we care about. HN items vary by type (a "job" item has no
# "by", an "Ask HN" post has "text" but no "url", etc.) so we declare
# every column we want and let missing fields come back as NULL rather
# than let DuckDB infer a different shape from whatever happens to be in
# the file on a given run.
EXPECTED_COLUMNS = {
    "id": "BIGINT",
    "by": "VARCHAR",
    "descendants": "BIGINT",
    "score": "BIGINT",
    "time": "BIGINT",
    "title": "VARCHAR",
    "type": "VARCHAR",
    "url": "VARCHAR",
    "text": "VARCHAR",
}


def run() -> None:
    if not JSONL_PATH.exists():
        print(f"No data file found at {JSONL_PATH}. Run hackernews.py first.")
        return

    con = duckdb.connect(str(DB_PATH))

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_hackernews_stories (
            id BIGINT PRIMARY KEY,
            "by" VARCHAR,
            descendants BIGINT,
            score BIGINT,
            time BIGINT,
            title VARCHAR,
            type VARCHAR,
            url VARCHAR,
            text VARCHAR,
            loaded_at TIMESTAMP DEFAULT current_timestamp
        )
        """
    )

    before = con.execute("SELECT COUNT(*) FROM raw_hackernews_stories").fetchone()[0]

    # read_json_auto with an explicit columns map pins every row to the
    # same shape, regardless of which fields a given story happens to have.
    columns_literal = ", ".join(f"'{name}': '{dtype}'" for name, dtype in EXPECTED_COLUMNS.items())
    select_cols = ", ".join(f'"{name}"' for name in EXPECTED_COLUMNS.keys())

    con.execute(
        f"""
        INSERT INTO raw_hackernews_stories ({select_cols})
        SELECT {select_cols}
        FROM read_json_auto(?, columns = {{{columns_literal}}})
        ON CONFLICT (id) DO NOTHING
        """,
        [str(JSONL_PATH)],
    )

    after = con.execute("SELECT COUNT(*) FROM raw_hackernews_stories").fetchone()[0]
    con.close()

    print(f"Rows before load: {before}")
    print(f"Rows after load:  {after}")
    print(f"New rows inserted: {after - before}")
    print(f"Database file: {DB_PATH}")


if __name__ == "__main__":
    run()
