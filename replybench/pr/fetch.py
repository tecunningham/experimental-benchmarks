"""Build ReplyBench-PR: open-source merge requests and whether they were merged within 30 days.

GitHub's API is not reachable from our environment, so this uses public GitLab instances (GitLab.com,
freedesktop, GNOME, KDE). All MRs opened in a window after the training cutoff are eligible, whatever
happened to them, so the label has no survivorship bias: merged within 30 days = 1, otherwise 0
(closed, still open, or merged later). Bot-authored MRs are dropped.
"""
import argparse
import json
import os
import random
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

PROJECTS = {
    "https://gitlab.freedesktop.org": ["mesa/mesa", "gstreamer/gstreamer", "pipewire/pipewire",
                                       "NetworkManager/NetworkManager", "wayland/wayland-protocols"],
    "https://gitlab.com": ["inkscape/inkscape", "fdroid/fdroiddata", "wireshark/wireshark", "kicad/code/kicad",
                           "gitlab-org/gitlab"],
    "https://gitlab.gnome.org": ["GNOME/gtk", "GNOME/gnome-shell", "GNOME/mutter", "GNOME/glib", "GNOME/nautilus"],
    "https://invent.kde.org": ["plasma/plasma-workspace", "plasma/kwin", "multimedia/kdenlive", "graphics/krita",
                               "system/dolphin"],
}
BOT = re.compile(r"bot|renovate|dependabot|weblate|translat|ci-|-ci$|release-tools", re.I)


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(8 * (i + 1))  # rate limits (GNOME is strict)


def project_mrs(host, path, start, end, k, rng):
    pid = urllib.parse.quote(path, safe="")
    base = f"{host}/api/v4/projects/{pid}"
    mrs, page = [], 1
    while page <= 10:
        q = urllib.parse.urlencode({"created_after": start, "created_before": end, "state": "all",
                                    "per_page": 100, "page": page, "order_by": "created_at"})
        batch = get(f"{base}/merge_requests?{q}")
        mrs += batch
        if len(batch) < 100:
            break
        page += 1
    mrs = [m for m in mrs if not BOT.search(m["author"]["username"]) and not BOT.search(m["author"].get("name", ""))]
    rng.shuffle(mrs)
    out = []
    for m in mrs[:k]:
        created = datetime.fromisoformat(m["created_at"].replace("Z", "+00:00"))
        merged_at = m.get("merged_at") and datetime.fromisoformat(m["merged_at"].replace("Z", "+00:00"))
        try:
            diffs = get(f"{base}/merge_requests/{m['iid']}/diffs?per_page=30")
        except Exception:
            diffs = []
        diff_text = "".join(f"--- {d.get('old_path')}\n+++ {d.get('new_path')}\n{d.get('diff', '')}" for d in diffs)
        out.append({
            "id": f"{host.split('//')[1]}/{path}!{m['iid']}", "project": path, "host": host.split("//")[1],
            "title": m["title"], "description": (m.get("description") or "")[:2000], "author": m["author"]["username"],
            "created": created.strftime("%Y-%m-%d %H:%M (%a)"), "draft": m.get("draft", False),
            "target_branch": m.get("target_branch"), "n_files": len(diffs), "diff": diff_text[:3000],
            "merged_30d": bool(merged_at and merged_at - created <= timedelta(days=30)),
            "state_now": m["state"],
            "days_to_merge": round((merged_at - created).total_seconds() / 86400, 1) if merged_at else None,
        })
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2026-07-15T00:00:00Z")
    p.add_argument("--end", default="2026-09-01T00:00:00Z")
    p.add_argument("--per-project", type=int, default=12)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default="replybench/pr/data/prs.jsonl")
    a = p.parse_args()

    def host_job(host):  # hosts in parallel, projects within a host sequentially (rate limits)
        rows = []
        for path in PROJECTS[host]:
            try:
                rows += project_mrs(host, path, a.start, a.end, a.per_project, random.Random(f"{a.seed}{path}"))
            except Exception as e:
                print("skip", path, e)
        return rows

    with ThreadPoolExecutor(len(PROJECTS)) as ex:
        rows = [r for rs in ex.map(host_job, PROJECTS) for r in rs]
    random.Random(a.seed).shuffle(rows)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} MRs from {len({r['project'] for r in rows})} projects; "
          f"merged within 30d: {sum(r['merged_30d'] for r in rows) / len(rows):.2f}")


if __name__ == "__main__":
    main()
