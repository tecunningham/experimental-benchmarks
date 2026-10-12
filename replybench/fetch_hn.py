"""Build the ReplyBench-HN dataset: a random sample of Hacker News stories with settled outcomes.

Stories come from a window after the models' training cutoff, and at least ~5 days old so
scores have settled. Ground truth (score, comment count) is re-read from the official
Firebase API at fetch time.
"""
import argparse
import json
import random
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse

ALGOLIA = "https://hn.algolia.com/api/v1/search_by_date"
FIREBASE = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def story_ids(start: int, end: int, step: int = 3 * 3600):
    ids = []
    for t in range(start, end, step):
        url = f"{ALGOLIA}?tags=story&hitsPerPage=1000&numericFilters=created_at_i>={t},created_at_i<{min(t + step, end)}"
        ids += [int(h["objectID"]) for h in get(url)["hits"]]
    return sorted(set(ids))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2026-10-01")
    p.add_argument("--end", default="2026-10-06")
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default="replybench/data/hn_stories.jsonl")
    a = p.parse_args()

    ts = lambda s: int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())
    ids = story_ids(ts(a.start), ts(a.end))
    print(f"{len(ids)} stories in window")
    random.Random(a.seed).shuffle(ids)

    rows = []
    for i in ids:
        it = get(FIREBASE.format(i))
        if not it or it.get("dead") or it.get("deleted") or it.get("type") != "story":
            continue
        rows.append({
            "id": i,
            "title": it.get("title", ""),
            "domain": urlparse(it["url"]).netloc.removeprefix("www.") if it.get("url") else None,
            "text": (it.get("text") or "")[:1000] or None,
            "author": it.get("by"),
            "posted_utc": datetime.fromtimestamp(it["time"], timezone.utc).strftime("%Y-%m-%d %H:%M (%a)"),
            "score": it.get("score", 0),
            "comments": it.get("descendants", 0),
        })
        if len(rows) == a.n:
            break
    with open(a.out, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(rows)} -> {a.out}")


if __name__ == "__main__":
    main()
