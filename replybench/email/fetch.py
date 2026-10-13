"""Build ReplyBench-Email: thread-starting emails on Apache mailing lists and whether anyone replied.

Every Apache project list is public (lists.apache.org). We take human-written thread starters from a window
after the models' training cutoff, and look up to ~6 weeks later for replies from someone other than the
sender. Bot traffic (JIRA, GitHub, CI notifications) is dropped.
"""
import argparse
import json
import random
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

API = "https://lists.apache.org/api"
BOT = re.compile(r"jira|github|gitbox|jenkins|buildbot|notification|dependabot|noreply|no-reply|bot@|"
                 r"commits@|\(jira\)|ci@|issues@", re.I)
BOT_SUBJECT = re.compile(r"^\s*(\[jira\]|\[github\]|\[pr\]|\[i\]|\[gh\]|\[ci\]|re:|fwd?:)|"
                         r"\b(pull request|build failed|build is still|nightly)\b|"
                         r"^\s*\([\w.\-]+\)\s+(branch|tag|\d+/\d+:)", re.I)  # gitbox commit mails


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def month_emails(domain, lst, month):
    q = urllib.parse.urlencode({"list": lst, "domain": domain, "d": month})
    try:
        return get(f"{API}/stats.lua?{q}").get("emails", [])
    except Exception:
        return []


def sender(frm):
    m = re.search(r"<([^>]+)>", frm or "")
    return (m.group(1) if m else frm or "").lower()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2026-08-01")
    p.add_argument("--end", default="2026-09-15")
    p.add_argument("--months", default="2026-08,2026-09,2026-10")
    p.add_argument("--lists", type=int, default=80, help="most active user/dev lists to scan")
    p.add_argument("--per-list", type=int, default=6)
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default="replybench/email/data/emails.jsonl")
    a = p.parse_args()
    ts = lambda s: datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()
    t0, t1 = ts(a.start), ts(a.end)

    prefs = get(f"{API}/preferences.lua")["lists"]
    lists = sorted(((n, d, l) for d, ls in prefs.items() for l, n in ls.items() if l in ("user", "users", "dev")),
                   reverse=True)[:a.lists]
    jobs = [(d, l, m) for _, d, l in lists for m in a.months.split(",")]
    with ThreadPoolExecutor(8) as ex:
        results = list(ex.map(lambda j: (j, month_emails(*j)), jobs))
    by_list = defaultdict(list)
    for (d, l, _), es in results:
        by_list[(d, l)] += es

    rng = random.Random(a.seed)
    cands = []
    for (d, l), es in by_list.items():
        replies = defaultdict(list)
        for e in es:
            if e.get("in-reply-to"):
                replies[e["in-reply-to"].strip()].append(e)
        roots = [e for e in es if not e.get("in-reply-to") and t0 <= e["epoch"] < t1
                 and not BOT.search(e.get("from", "")) and not BOT_SUBJECT.search(e.get("subject", ""))]
        rng.shuffle(roots)
        for e in roots[:a.per_list]:
            rs = [r for r in replies.get(e["message-id"].strip(), []) if sender(r["from"]) != sender(e["from"])]
            first = min((r["epoch"] for r in rs), default=None)
            cands.append({"id": e["id"], "list": f"{l}@{d}", "subject": e["subject"], "from": e["from"],
                          "date": datetime.fromtimestamp(e["epoch"], timezone.utc).strftime("%Y-%m-%d %H:%M (%a)"),
                          "replied": bool(rs), "n_repliers": len({sender(r['from']) for r in rs}),
                          "hours_to_reply": round((first - e["epoch"]) / 3600, 1) if first else None})
    rng.shuffle(cands)
    cands = cands[:a.n]

    def body(c):  # full text of the starting email only
        try:
            c["body"] = (get(f"{API}/email.lua?id={c['id']}").get("body") or "")[:2500]
        except Exception:
            c["body"] = ""
        return c

    with ThreadPoolExecutor(8) as ex:
        cands = [c for c in ex.map(body, cands) if c["body"].strip()]
    import os
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        for c in cands:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"{len(by_list)} lists, wrote {len(cands)} threads; reply rate {sum(c['replied'] for c in cands) / len(cands):.2f}")


if __name__ == "__main__":
    main()
