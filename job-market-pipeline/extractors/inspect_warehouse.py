"""
Peek inside the DuckDB warehouse without any extra tools.

    py inspect_warehouse.py
        Overview: every table and view with its row count, plus a few
        sample rows from the main ones.

    py inspect_warehouse.py "select job_title, company from stg_remoteok_jobs"
        Run any SQL you like and print the result.

    py inspect_warehouse.py before
    py inspect_warehouse.py after
        The same rows as raw data (before dbt run) and as cleaned data
        (after dbt run), for showing what dbt actually changed.

It opens the database read-only, so it is safe to run between other steps.
"""

import sys
from pathlib import Path

import duckdb

DB_PATH = Path(__file__).parent / "data" / "warehouse.duckdb"

OVERVIEW_TABLES = [
    "main.raw_hackernews_stories",
    "main.raw_remoteok_jobs",
    "main.stg_hackernews_stories",
    "main.stg_remoteok_jobs",
    "snapshots.remoteok_jobs_snapshot",
]


def table_exists(con, qualified_name: str) -> bool:
    schema, name = qualified_name.split(".")
    found = con.execute(
        "select count(*) from information_schema.tables "
        "where table_schema = ? and table_name = ?",
        [schema, name],
    ).fetchone()[0]
    return found > 0


def overview(con) -> None:
    print("What is in the warehouse right now:\n")
    for name in OVERVIEW_TABLES:
        if table_exists(con, name):
            count = con.execute(f"select count(*) from {name}").fetchone()[0]
            print(f"  {name:<40} {count:>6} rows")
        else:
            print(f"  {name:<40} (not created yet)")

    if table_exists(con, "main.raw_remoteok_jobs"):
        print("\nSample of raw_remoteok_jobs:")
        con.sql(
            "select id, position, company from main.raw_remoteok_jobs limit 5"
        ).show()

    if table_exists(con, "snapshots.remoteok_jobs_snapshot"):
        print("Snapshot status (open = dbt_valid_to is empty):")
        con.sql(
            "select case when dbt_valid_to is null then 'open' else 'closed' end "
            "as status, count(*) as listings "
            "from snapshots.remoteok_jobs_snapshot group by 1 order by 1"
        ).show()


def list_objects(con) -> None:
    print("Tables and views in the warehouse:")
    rows = con.execute(
        "select table_schema || '.' || table_name, "
        "case table_type when 'VIEW' then 'view' else 'table' end "
        "from information_schema.tables "
        "where table_schema in ('main', 'snapshots') order by 1"
    ).fetchall()
    for name, kind in rows:
        print(f"  {name:<40} {kind}")
    print()


def before_after(con, stage: str) -> None:
    """Show the SAME rows as raw (before dbt) or as cleaned (after dbt)."""
    after = stage == "after"
    print("=" * 60)
    print("AFTER dbt: cleaned tables, tested, with history" if after
          else "BEFORE dbt: raw tables exactly as they were loaded")
    print("=" * 60 + "\n")
    list_objects(con)

    if after:
        hn_sql = ("select story_id, author, posted_at, title "
                  "from main.stg_hackernews_stories order by story_id desc limit 3")
        ro_sql = ("select job_id, job_title, salary_min, salary_max, posted_at "
                  "from main.stg_remoteok_jobs order by job_id limit 3")
        hn_table, ro_table = "main.stg_hackernews_stories", "main.stg_remoteok_jobs"
    else:
        hn_sql = ('select id, "by", time, title '
                  "from main.raw_hackernews_stories order by id desc limit 3")
        ro_sql = ("select id, position, salary_min, salary_max, date "
                  "from main.raw_remoteok_jobs order by id limit 3")
        hn_table, ro_table = "main.raw_hackernews_stories", "main.raw_remoteok_jobs"

    for label, table, sql in [("Hacker News", hn_table, hn_sql), ("RemoteOK", ro_table, ro_sql)]:
        print(f"{label} ({table}):")
        if table_exists(con, table):
            con.sql(sql).show(max_width=200)
        else:
            print("  not there yet. Run `dbt run` first.\n" if after
                  else "  not there yet. Run the load scripts first.\n")

    if after and table_exists(con, "snapshots.remoteok_jobs_snapshot"):
        print("History kept by dbt snapshot (open = dbt_valid_to is empty):")
        con.sql(
            "select case when dbt_valid_to is null then 'open' else 'closed' end "
            "as status, count(*) as listings "
            "from snapshots.remoteok_jobs_snapshot group by 1 order by 1"
        ).show()


def main() -> None:
    if not DB_PATH.exists():
        print(f"No warehouse yet at {DB_PATH}")
        print("Run the load scripts first (load_hackernews.py, load_remoteok.py).")
        return

    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        if len(sys.argv) == 2 and sys.argv[1] in ("before", "after"):
            before_after(con, sys.argv[1])
        elif len(sys.argv) > 1:
            con.sql(" ".join(sys.argv[1:])).show(max_width=200, max_rows=50)
        else:
            overview(con)
    finally:
        con.close()


if __name__ == "__main__":
    main()
