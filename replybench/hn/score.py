"""Score ReplyBench-HN with bootstrap 95% CIs; writes results/summary.json for the figures."""
import json
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.stats import auc, bootstrap_ci, spearman

truth = {s["id"]: s for s in map(json.loads, open("replybench/hn/data/hn_stories.jsonl"))}
ids = list(truth)
n = len(ids)
y_pts = [truth[i]["score"] for i in ids]
y_com = [truth[i]["comments"] for i in ids]
hit = [p >= 50 for p in y_pts]
base = sum(hit) / n
log = lambda v: math.log1p(max(v, 0))

predictors = {"baseline: constant median / base rate": (
    [statistics.median(y_pts)] * n, [statistics.median(y_com)] * n, [base] * n)}
for f in sorted(Path("replybench/hn/results").glob("claude-*.jsonl")):
    pr = {int(p["id"]): p for p in map(json.loads, open(f))}
    predictors[f.stem] = ([float(pr[i]["points"]) for i in ids], [float(pr[i]["comments"]) for i in ids],
                          [min(max(float(pr[i]["p50"]), 0), 1) for i in ids])

brier = lambda ps, idx: statistics.mean((ps[i] - hit[i]) ** 2 for i in idx)
metrics = {
    "spearman_points": lambda pts, com, p50, idx: spearman([pts[i] for i in idx], [y_pts[i] for i in idx]),
    "spearman_comments": lambda pts, com, p50, idx: spearman([com[i] for i in idx], [y_com[i] for i in idx]),
    "mae_log_points": lambda pts, com, p50, idx: statistics.mean(abs(log(pts[i]) - log(y_pts[i])) for i in idx),
    "brier": lambda pts, com, p50, idx: brier(p50, idx),
    "bss": lambda pts, com, p50, idx: 1 - brier(p50, idx) / max(
        (r := statistics.mean(hit[i] for i in idx)) * (1 - r), 1e-9),
    "auc": lambda pts, com, p50, idx: auc([p50[i] for i in idx], [hit[i] for i in idx]),
}
summary = {"n": n, "base_rate": base, "models": {}}
full = list(range(n))
print(f"n={n} stories, {sum(hit)} reached >=50 points (base rate {base:.3f}); [95% bootstrap CI]\n")
print("| predictor | " + " | ".join(metrics) + " |\n|---|" + "---|" * len(metrics))
for name, (pts, com, p50) in predictors.items():
    row = {}
    for k, fn in metrics.items():
        v = fn(pts, com, p50, full)
        lo, hi = bootstrap_ci(lambda idx: fn(pts, com, p50, idx), n)
        row[k] = [v, lo, hi]
    summary["models"][name] = row
    print(f"| {name} | " + " | ".join(f"{row[k][0]:.3f} [{row[k][1]:.2f}, {row[k][2]:.2f}]" for k in metrics) + " |")
Path("replybench/hn/results/summary.json").write_text(json.dumps(summary, indent=1))
