"""Score ReplyBench yes/no tasks with bootstrap 95% CIs; writes results/summary.json for the figures.

Brier skill = 1 - Brier / Brier(base rate): above 0 beats always predicting the base rate.
"""
import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.stats import auc, bootstrap_ci

LABEL = {"email": "replied", "pr": "merged_30d"}
GROUP = {"email": None, "pr": "project"}  # leave-one-out group base rate as an extra baseline


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", choices=LABEL, required=True)
    a = p.parse_args()
    d = Path(f"replybench/{a.task}")
    items = [json.loads(l) for l in open(next(d.glob("data/*.jsonl")))]
    y = [bool(x[LABEL[a.task]]) for x in items]
    n, base = len(y), sum(y) / len(y)

    predictors = {"baseline: overall base rate": [base] * n}
    if GROUP[a.task]:
        tot, cnt = defaultdict(int), defaultdict(int)
        for x, yi in zip(items, y):
            tot[x[GROUP[a.task]]] += yi
            cnt[x[GROUP[a.task]]] += 1
        predictors[f"baseline: {GROUP[a.task]} merge rate (leave-one-out)"] = [
            (tot[x[GROUP[a.task]]] - yi + base) / cnt[x[GROUP[a.task]]]  # +base: shrink, avoids 0/0
            for x, yi in zip(items, y)]
    for f in sorted((d / "results").glob("claude-*.jsonl")):
        pr = {str(r["id"]): r["p"] for r in map(json.loads, open(f))}
        predictors[f.stem] = [pr[str(x["id"])] for x in items]

    brier = lambda ps, idx: statistics.mean((ps[i] - y[i]) ** 2 for i in idx)

    def bss(ps, idx):
        r = statistics.mean(y[i] for i in idx)
        return 1 - brier(ps, idx) / max(r * (1 - r), 1e-9)  # Brier of the resample's own base rate
    au = lambda ps, idx: auc([ps[i] for i in idx], [y[i] for i in idx])
    summary = {"n": n, "base_rate": base, "models": {}}
    print(f"ReplyBench-{a.task}: n={n}, base rate {base:.2f}\n")
    print("| predictor | AUC [95% CI] | Brier [95% CI] | Brier skill vs base rate [95% CI] |\n|---|---|---|---|")
    full = list(range(n))
    for name, ps in predictors.items():
        row = {}
        for key, fn in [("auc", au), ("brier", brier), ("bss", bss)]:
            v = fn(ps, full)
            lo, hi = bootstrap_ci(lambda idx: fn(ps, idx), n)
            row[key] = [v, lo, hi]
        summary["models"][name] = row
        cell = lambda k, f: f"{row[k][0]:{f}} [{row[k][1]:{f}}, {row[k][2]:{f}}]"
        auc_cell = "–" if name.startswith("baseline: overall") else cell("auc", ".2f")
        print(f"| {name} | {auc_cell} | {cell('brier', '.3f')} | {cell('bss', '+.2f')} |")
    (d / "results" / "summary.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
