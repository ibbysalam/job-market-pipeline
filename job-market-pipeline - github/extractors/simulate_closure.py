"""
Demo helper: pretend one RemoteOK job just got filled.

It removes ONE listing from raw_remoteok_jobs, exactly what would happen if
RemoteOK stopped listing it. Then run `dbt snapshot` and that listing's
dbt_valid_to gets filled in, which is the SCD Type 2 proof.

    py simulate_closure.py              # picks an open listing for you
    py simulate_closure.py 1234567      # closes a specific job_id

Run `dbt snapshot` at least once BEFORE this, so the snapshot already knows
the listing was open. The next real run of remoteok.py + load_remoteok.py
will bring the listing back (the snapshot then opens a fresh row for it).
"""

import sys
from pathlib import Path

import duckdb

DB_PATH = Path(__file__).parent / "data" / "warehouse.duckdb"


def snapshot_exists(con) -> bool:
    return con.execute(
        "select count(*) from information_schema.tables "
        "where table_schema = 'snapshots' and table_name = 'remoteok_jobs_snapshot'"
    ).fetchone()[0] > 0


def run() -> None:
    if not DB_PATH.exists():
        print(f"No warehouse found at {DB_PATH}. Run the load scripts first.")
        return

    con = duckdb.connect(str(DB_PATH))
    try:
        if not snapshot_exists(con):
            print("The snapshot table does not exist yet.")
            print("Run `dbt snapshot` once first, then come back to this script.")
            return

        # Only choose listings the snapshot already counts as open, so the
        # closure shows up clearly after the next `dbt snapshot`.
        wanted = sys.argv[1] if len(sys.argv) > 1 else None
        if wanted:
            job = con.execute(
                """
                select r.id, r.position, r.company
                from raw_remoteok_jobs r
                join snapshots.remoteok_jobs_snapshot s
                  on s.job_id = r.id and s.dbt_valid_to is null
                where r.id = ?
                """,
                [wanted],
            ).fetchone()
        else:
            job = con.execute(
                """
                select r.id, r.position, r.company
                from raw_remoteok_jobs r
                join snapshots.remoteok_jobs_snapshot s
                  on s.job_id = r.id and s.dbt_valid_to is null
                order by (lower(r.position) like '%data engineer%') desc, r.id
                limit 1
                """
            ).fetchone()

        if job is None:
            print("No open listing found to close.")
            print("Run `dbt snapshot` so the snapshot knows what is open, "
                  "or check the job_id you passed.")
            return

        job_id, title, company = job
        print(f"Closing: {title} at {company} (job_id={job_id})")

        before = con.execute("select count(*) from raw_remoteok_jobs").fetchone()[0]
        con.execute("delete from raw_remoteok_jobs where id = ?", [job_id])
        after = con.execute("select count(*) from raw_remoteok_jobs").fetchone()[0]

        print(f"raw_remoteok_jobs: {before} rows -> {after} rows")
        print("\nNow run `dbt snapshot` and watch this listing get closed.")
        print(f"Then check it with:\n"
              f"  py inspect_warehouse.py \"select job_id, job_title, dbt_valid_from, "
              f"dbt_valid_to from snapshots.remoteok_jobs_snapshot "
              f"where job_id = '{job_id}'\"")
    finally:
        con.close()


if __name__ == "__main__":
    run()
