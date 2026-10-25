"""
Hacker News incremental extractor.

Pulls new story IDs from the HN Firebase API and only fetches stories
we haven't seen before, using a simple watermark file to track the
highest item ID processed so far.

Run it twice in a row to see the incremental behavior:
    python hackernews.py
    python hackernews.py   # should fetch far fewer (or zero) new items
"""

import json
import time
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

HN_BASE = "https://hacker-news.firebaseio.com/v0"
NEW_STORIES_URL = f"{HN_BASE}/newstories.json"
ITEM_URL = f"{HN_BASE}/item/{{item_id}}.json"

DATA_DIR = Path(__file__).parent / "data"
WATERMARK_FILE = DATA_DIR / "hn_watermark.json"
OUTPUT_FILE = DATA_DIR / "hn_stories.jsonl"

REQUEST_TIMEOUT = 10
REQUEST_DELAY = 0.1  # be polite to the free API
MAX_ATTEMPTS = 3
RETRY_PAUSE = 2  # seconds, doubled after each failed attempt

# A slow connection can fail in different ways: URLError (could not connect)
# or a plain TimeoutError (connected, then the reply never finished). Both
# mean "try again", so we treat them the same.
NETWORK_ERRORS = (URLError, TimeoutError, ConnectionError)


def fetch_json(url: str):
    """Fetch a URL, retrying a few times on network trouble.

    Raises the last error if every attempt fails, so callers decide
    what to do about it.
    """
    pause = RETRY_PAUSE
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urlopen(url, timeout=REQUEST_TIMEOUT) as response:
                return json.loads(response.read().decode("utf-8"))
        except NETWORK_ERRORS as e:
            if attempt == MAX_ATTEMPTS:
                raise
            print(f"  network hiccup ({type(e).__name__}), "
                  f"retrying in {pause}s (attempt {attempt + 1} of {MAX_ATTEMPTS})")
            time.sleep(pause)
            pause *= 2


def load_watermark() -> int:
    """Highest item ID we've already processed. 0 means first run."""
    if WATERMARK_FILE.exists():
        return json.loads(WATERMARK_FILE.read_text()).get("last_item_id", 0)
    return 0


def save_watermark(last_item_id: int) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    WATERMARK_FILE.write_text(json.dumps({"last_item_id": last_item_id}))


def append_stories(stories: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("a") as f:
        for story in stories:
            f.write(json.dumps(story) + "\n")


def run() -> None:
    watermark = load_watermark()
    print(f"Current watermark (last item ID processed): {watermark}")

    try:
        new_story_ids = fetch_json(NEW_STORIES_URL)
    except NETWORK_ERRORS as e:
        print(f"Failed to reach Hacker News API after {MAX_ATTEMPTS} attempts: {e}")
        return

    # newstories.json returns up to 500 of the most recent story IDs,
    # newest first. We only care about ones above our watermark.
    unseen_ids = [item_id for item_id in new_story_ids if item_id > watermark]
    print(f"Found {len(new_story_ids)} recent IDs, {len(unseen_ids)} unseen")

    if not unseen_ids:
        print("Nothing new since last run.")
        return

    fetched = []
    failed_ids = []
    for item_id in unseen_ids:
        try:
            item = fetch_json(ITEM_URL.format(item_id=item_id))
        except NETWORK_ERRORS as e:
            print(f"  gave up on {item_id}: {e}")
            failed_ids.append(item_id)
            continue
        if item is None:
            continue
        fetched.append(item)
        time.sleep(REQUEST_DELAY)

    if not fetched:
        print("No items could be fetched.")
        return

    append_stories(fetched)
    print(f"Fetched {len(fetched)} stories.")
    print(f"Appended to: {OUTPUT_FILE}")

    if failed_ids:
        # Moving the watermark forward now would make us skip these stories
        # forever. Leaving it alone means the next run re-fetches them. Any
        # story we did save gets fetched twice, which is fine because the
        # loader ignores duplicates (ON CONFLICT DO NOTHING).
        print(f"{len(failed_ids)} stories failed, so the watermark stays at {watermark}.")
        print("Run this script again to fill the gaps.")
        return

    new_high_watermark = max(unseen_ids)
    save_watermark(new_high_watermark)
    print(f"New watermark: {new_high_watermark}")


if __name__ == "__main__":
    run()
