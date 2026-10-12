import json
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.stats import auc, spearman

truth = {s["id"]: s for s in map(json.loads, open("replybench/data/hn_stories.jsonl"))}
ids = list(truth)
y_pts = [truth[i]["score"] for i in ids]
y_com = [truth[i]["comments"] for i in ids]
hit = [p >= 50 for p in y_pts]
log = lambda v: math.log1p(max(v, 0))
base = sum(hit) / len(hit)


def row(name, pts, com, p50):
    return {
        "model": name,
        "spearman_points": round(spearman(pts, y_pts), 3),
        "spearman_comments": round(spearman(com, y_com), 3),
        "mae_log_points": round(statistics.mean(abs(log(a) - log(b)) for a, b in zip(pts, y_pts)), 3),
        "brier_p50": round(statistics.mean((p - h) ** 2 for p, h in zip(p50, hit)), 4),
        "auc_p50": round(auc(p50, hit), 3),
    }


rows = [row("baseline: constant median / base rate", [statistics.median(y_pts)] * len(ids),
            [statistics.median(y_com)] * len(ids), [base] * len(ids))]
for f in sorted(Path("replybench/results").glob("*.jsonl")):
    pr = {int(p["id"]): p for p in map(json.loads, open(f))}
    rows.append(row(f.stem, [float(pr[i]["points"]) for i in ids], [float(pr[i]["comments"]) for i in ids],
                    [min(max(float(pr[i]["p50"]), 0), 1) for i in ids]))

print(f"n={len(ids)} stories, {sum(hit)} reached >=50 points (base rate {base:.3f})\n")
keys = list(rows[0])
print("| " + " | ".join(keys) + " |\n|" + "---|" * len(keys))
for r in rows:
    print("| " + " | ".join(str(r[k]) for k in keys) + " |")
