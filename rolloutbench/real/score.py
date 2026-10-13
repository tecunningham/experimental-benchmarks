"""Summarise RolloutBench-Real.

judge: blind LLM-judge score 0-10 (see judge.py) and whether the basic outcome was right.
sim:   difflib similarity between prediction and real result (first 2000 chars), 0-1.
novel: items where copying the previous result of the same tool scores sim < 0.5, i.e. the answer
       is not simply sitting in the history (repeated log polling, identical re-runs).
"""
import difflib
import json
import math
import statistics
from pathlib import Path

D = Path("rolloutbench/data/real")
items = {i["id"]: i for i in map(json.loads, open(D / "items.jsonl"))}
grades = {r["id"]: r["grades"] for r in map(json.loads, open("rolloutbench/real/grades.jsonl"))}
preds = {f.stem.removeprefix("pred-"): {r["id"]: r["prediction"] for r in map(json.loads, open(f))}
         for f in sorted(D.glob("pred-*.jsonl"))}
ids = [i for i in items if i in grades]
models = [m for m in sorted(preds) if all(m in grades[i] for i in ids)]  # predicted and judged


def sim(a, b):
    return difflib.SequenceMatcher(None, a.strip()[:2000], b.strip()[:2000], autojunk=False).ratio()


copy_sim = {i: sim(items[i]["copy_baseline"], items[i]["target"]) for i in ids}
novel = [i for i in ids if copy_sim[i] < 0.5]


def mse(xs):
    return statistics.mean(xs), (statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0)


def table(sub, title):
    print(f"\n**{title}** (n={len(sub)})\n")
    print("| predictor | judge score (0-10) | outcome right | similarity |\n|---|---|---|---|")
    print(f"| baseline: copy last result of same tool | – | – | {statistics.mean(copy_sim[i] for i in sub):.2f} |")
    for m in models:
        mu, se = mse([grades[i][m]["score"] for i in sub])
        acc = statistics.mean(bool(grades[i][m]["outcome_right"]) for i in sub)
        s = statistics.mean(sim(preds[m][i], items[i]["target"]) for i in sub)
        print(f"| {m} | {mu:.2f} ± {se:.2f} | {acc:.0%} | {s:.2f} |")


print(f"{len(ids)} tool calls from {len({i.rsplit('/', 1)[0] for i in ids})} real sessions "
      f"({sum(items[i]['source'] == 'wisp' for i in ids)} wisp, {sum(items[i]['source'] == 'ml-intern' for i in ids)} ml-intern), "
      f"dated {min(items[i]['date'] for i in ids)} to {max(items[i]['date'] for i in ids)}.")
table(ids, "All items")
table(novel, "Novel items (answer not copyable from history)")

cats = sorted({items[i]["category"] for i in ids}, key=lambda c: -sum(items[i]["category"] == c for i in ids))
print("\n**Judge score by tool category, novel items** (n per category in header)\n")
print("| predictor | " + " | ".join(f"{c} ({sum(items[i]['category'] == c for i in novel)})" for c in cats) + " |")
print("|---|" + "---|" * len(cats))
for m in models:
    cells = []
    for c in cats:
        sub = [grades[i][m]["score"] for i in novel if items[i]["category"] == c]
        cells.append(f"{statistics.mean(sub):.1f}" if sub else "–")
    print(f"| {m} | " + " | ".join(cells) + " |")

# per-model summary with 95% bootstrap CIs, for figures and ECI correlations
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.stats import mean_ci

summary = {"n": len(ids), "models": {m: {
    "score": list(mean_ci([grades[i][m]["score"] for i in ids])),
    "outcome_right": list(mean_ci([float(bool(grades[i][m]["outcome_right"])) for i in ids])),
    "score_novel": list(mean_ci([grades[i][m]["score"] for i in novel])),
} for m in models}}
Path("rolloutbench/real/summary.json").write_text(json.dumps(summary, indent=1))
