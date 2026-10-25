"""
RemoteOK job listings extractor — replaces the Remotive extractor.

Why the swap: Remotive's public API currently ignores every query
parameter (search, category, even limit) and just serves a fixed,
unfiltered sample regardless of what's asked for. Confirmed directly
against the live API, not a bug in our own request. RemoteOK's API is
genuinely live and responsive, so we're using it instead.

Like the old Remotive script, this has no "give me only what's new"
option, so every run writes out the FULL current snapshot of matching
listings, overwriting the previous one. Detecting what opened/closed
over time is dbt's snapshot job, built on top of this raw data, not
something this extractor tries to do itself.

A quirk worth knowing: RemoteOK's own `tags` query parameter does
filter, but loosely — it matches jobs that have ANY data-related tag
anywhere in a long, generic tag list RemoteOK assigns per posting (30+
tags isn't unusual). Used alone it pulls in a lot of irrelevant titles
(a "Lead Paralegal" posting that happens to carry a "data entry" tag,
for instance). But it's still a useful first pass: it surfaces a much
larger pool of data-adjacent postings than RemoteOK's fully generic
"most recent across all categories" feed does, which on a quiet run
can easily contain zero exact title matches for our target roles.

So this script uses `tags=data` as a server-side pre-filter to get a
bigger, data-adjacent candidate pool, THEN applies our own strict
title-keyword match on top of that pool to cut the noise back down.
One request per run either way.

Run it any time:
    python remoteok.py
"""

import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError

REMOTEOK_API = "https://remoteok.com/api"

# RemoteOK, like Remotive, rejects requests with no browser-style
# User-Agent.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# Title keywords we're matching against, client-side, after the
# tags=data pre-filter narrows the pool. Case-insensitive substring
# match. Added "data analyst" since it's a common adjacent/entry role
# in the same job market.
ROLE_KEYWORDS = [
    "data engineer",
    "analytics engineer",
    "etl",
    "data platform",
    "business intelligence",
    "big data",
    "data scientist",
    "data analyst",
]

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = DATA_DIR / "remoteok_jobs.jsonl"
PREVIOUS_FILE = DATA_DIR / "remoteok_jobs_previous.jsonl"

REQUEST_TIMEOUT = 10
MAX_ATTEMPTS = 3
RETRY_PAUSE = 2  # seconds, doubled after each failed attempt

# URLError = could not connect. TimeoutError = connected, then the reply
# never finished. Both just mean "try again".
NETWORK_ERRORS = (URLError, TimeoutError, ConnectionError)

FIELDS_TO_KEEP = [
    "id",
    "position",
    "company",
    "tags",
    "location",
    "salary_min",
    "salary_max",
    "url",
    "date",
]


def fetch_json(url: str):
    request = Request(url, headers=REQUEST_HEADERS)
    pause = RETRY_PAUSE
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                return json.loads(response.read().decode("utf-8"))
        except NETWORK_ERRORS as e:
            if attempt == MAX_ATTEMPTS:
                raise
            print(f"  network hiccup ({type(e).__name__}), "
                  f"retrying in {pause}s (attempt {attempt + 1} of {MAX_ATTEMPTS})")
            time.sleep(pause)
            pause *= 2


def fetch_data_tagged_jobs() -> list[dict] | None:
    url = f"{REMOTEOK_API}?{urlencode({'tags': 'data'})}"
    try:
        payload = fetch_json(url)
    except NETWORK_ERRORS as e:
        print(f"Failed to fetch RemoteOK after {MAX_ATTEMPTS} attempts: {e}")
        return None  # None means "request failed", different from "zero jobs"
    # The first element is always a legal/notice object, not a job.
    return [item for item in payload if "id" in item]


def matches_target_role(job: dict) -> bool:
    title = (job.get("position") or "").lower()
    return any(keyword in title for keyword in ROLE_KEYWORDS)


def trim_fields(job: dict) -> dict:
    return {field: job.get(field) for field in FIELDS_TO_KEEP}


def load_jsonl(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    records = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            records[record["id"]] = record
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


def run() -> None:
    print("Fetching RemoteOK listings tagged 'data' (single request)")
    candidate_pool = fetch_data_tagged_jobs()
    if candidate_pool is None:
        # A failed request is not the same as "no jobs are open". Leave the
        # last good snapshot alone, or the next dbt snapshot would mark
        # every listing as closed.
        print("Keeping the previous snapshot untouched. Try again in a minute.")
        return
    print(f"  Candidate pool (tags=data pre-filter): {len(candidate_pool)} listings")

    matched = [job for job in candidate_pool if matches_target_role(job)]
    print(f"  {len(matched)} match our target roles: {', '.join(ROLE_KEYWORDS)}")

    current_jobs: dict[str, dict] = {}
    for job in matched:
        trimmed = trim_fields(job)
        current_jobs[trimmed["id"]] = trimmed

    current_ids = set(current_jobs.keys())
    print(f"\nTotal unique matching listings this run: {len(current_ids)}")

    # Informational diff only — the dbt snapshot (built later) is the
    # real system of record for what opened/closed over time.
    previous_jobs = load_jsonl(OUTPUT_FILE)
    previous_ids = set(previous_jobs.keys())

    if previous_ids:
        new_ids = current_ids - previous_ids
        missing_ids = previous_ids - current_ids
        print(f"New since last run: {len(new_ids)}")
        print(f"No longer listed (likely closed/filled): {len(missing_ids)}")
    else:
        print("No previous snapshot to compare against (first run).")

    if OUTPUT_FILE.exists():
        write_jsonl(PREVIOUS_FILE, list(previous_jobs.values()))

    write_jsonl(OUTPUT_FILE, list(current_jobs.values()))
    print(f"\nWrote current snapshot to: {OUTPUT_FILE}")


if __name__ == "__main__":
    run()
