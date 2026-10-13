"""Summarise judge grades: mean score (0-10) and outcome accuracy, overall and by tool category."""
import json
import math
import statistics

rows = [json.loads(l) for l in open("rolloutbench/real/grades.jsonl")]
models = sorted({m for r in rows for m in r["grades"]})
cats = sorted({r["category"] for r in rows}, key=lambda c: -sum(r["category"] == c for r in rows))


def stat(rs, m):
    s = [r["grades"][m]["score"] for r in rs]
    return statistics.mean(s), (statistics.stdev(s) / math.sqrt(len(s)) if len(s) > 1 else 0)


print(f"{len(rows)} tool calls from real sessions; judge scores 0-10 (± s.e.)\n")
print("| model | score | outcome right |\n|---|---|---|")
for m in models:
    mu, se = stat(rows, m)
    acc = statistics.mean(bool(r["grades"][m]["outcome_right"]) for r in rows)
    print(f"| {m} | {mu:.2f} ± {se:.2f} | {acc:.0%} |")
print("\nMean score by tool category:\n")
print("| model | " + " | ".join(f"{c} (n={sum(r['category'] == c for r in rows)})" for c in cats) + " |")
print("|---|" + "---|" * len(cats))
for m in models:
    print(f"| {m} | " + " | ".join(f"{stat([r for r in rows if r['category'] == c], m)[0]:.1f}" for c in cats) + " |")
print("\nMean score by source:\n")
for src in sorted({r["source"] for r in rows}):
    rs = [r for r in rows if r["source"] == src]
    print(f"- {src} (n={len(rs)}): " + ", ".join(f"{m} {stat(rs, m)[0]:.2f}" for m in models))
