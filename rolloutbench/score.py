"""Score RolloutBench predictions.

similarity: difflib ratio between predicted and true output (first 3000 chars), in [0, 1].
exact: prediction == truth after stripping whitespace.
"nontrivial" excludes steps whose true output is the empty-output marker.
"""
import difflib
import json
import statistics
from pathlib import Path

EMPTY = "(Bash completed with no output)"
N = 3000


def sim(a, b):
    return difflib.SequenceMatcher(None, a.strip()[:N], b.strip()[:N], autojunk=False).ratio()


traces = [json.loads(l) for l in open("rolloutbench/data/traces.jsonl")]
truth = {(t["task_id"], k): s["output"] for t in traces for k, s in enumerate(t["steps"])}
keys = list(truth)
nontriv = [k for k in keys if truth[k].strip() != EMPTY]


def row(name, pred):
    s = {k: sim(pred[k], truth[k]) for k in keys}
    by_task = {}
    for (task, _), v in ((k, s[k]) for k in nontriv):
        by_task.setdefault(task, []).append(v)
    return {
        "model": name,
        "similarity_all": round(statistics.mean(s.values()), 3),
        "similarity_nontrivial": round(statistics.mean(s[k] for k in nontriv), 3),
        "exact_all": round(statistics.mean(pred[k].strip() == truth[k].strip() for k in keys), 3),
        "exact_nontrivial": round(statistics.mean(pred[k].strip() == truth[k].strip() for k in nontriv), 3),
    }, {t: round(statistics.mean(v), 2) for t, v in by_task.items()}


rows = [row("baseline: always empty-output marker", {k: EMPTY for k in keys}),
        row("baseline: repeat previous output", {(t, k): truth[(t, k - 1)] if k else EMPTY for t, k in keys})]
for f in sorted(Path("rolloutbench/results").glob("*.jsonl")):
    pr = {(p["task_id"], p["step"]): p["prediction"] for p in map(json.loads, open(f))}
    rows.append(row(f.stem, pr))

print(f"{len(traces)} traces, {len(keys)} tool calls ({len(nontriv)} with non-empty output)\n")
cols = list(rows[0][0])
print("| " + " | ".join(cols) + " |\n|" + "---|" * len(cols))
for r, _ in rows:
    print("| " + " | ".join(str(r[c]) for c in cols) + " |")
tasks = list(rows[-1][1])
print("\nMean similarity on non-trivial steps, by task:\n")
print("| model | " + " | ".join(tasks) + " |\n|" + "---|" * (len(tasks) + 1))
for r, bt in rows:
    print(f"| {r['model']} | " + " | ".join(str(bt.get(t, '')) for t in tasks) + " |")
