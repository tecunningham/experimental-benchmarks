"""Score question-format RolloutBench predictions exactly; writes summary_questions.json.

Per question: multi-class Brier score of the probability vector against the true option. Brier skill compares
to a uniform guess over the options (0 = chance, 1 = perfect). Item scores average over that item's questions;
95% CIs bootstrap over items. Uses answer_key.jsonl (option counts + correct index only, no text).
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.models import MODELS, NAME
from common.stats import mean_ci

R = Path("rolloutbench/real")
src = Path("rolloutbench/data/real/questions.jsonl")
if src.exists():  # refresh the content-free key from the full questions
    with open(R / "answer_key.jsonl", "w") as f:
        for r in map(json.loads, open(src)):
            if r["questions"]:
                f.write(json.dumps({"id": r["id"], "n_options": [len(q["options"]) for q in r["questions"]],
                                    "answer": [q["answer"] for q in r["questions"]]}) + "\n")
key = {r["id"]: r for r in map(json.loads, open(R / "answer_key.jsonl"))}


def item_scores(probs, k):
    bs, acc, ll = [], [], []
    for p, n, a in zip(probs, k["n_options"], k["answer"]):
        brier = sum((x - (j == a)) ** 2 for j, x in enumerate(p))
        uniform = (1 - 1 / n) ** 2 + (n - 1) / n ** 2
        bs.append(1 - brier / uniform)
        acc.append(float(max(range(n), key=lambda j: p[j]) == a))
        ll.append(-math.log(max(p[a], 1e-3)))
    m = lambda v: sum(v) / len(v)
    return m(bs), m(acc), m(ll)


summary, rows = {"n_items": len(key), "n_questions": sum(len(k["answer"]) for k in key.values()), "models": {}}, []
names = {**NAME, **{f"{m}-blind": f"{NAME[m]} (questions only)" for m in NAME}}
for f in sorted((R / "qpreds").glob("*.jsonl")):
    preds = {r["id"]: r["probs"] for r in map(json.loads, open(f))}
    ids = [i for i in key if i in preds]
    if len(ids) < 0.95 * len(key):
        continue
    s = [item_scores(preds[i], key[i]) for i in ids]
    summary["models"][f.stem] = {k: list(mean_ci([x[j] for x in s])) for j, k in enumerate(["skill", "accuracy", "logloss"])}
    summary["models"][f.stem]["n"] = len(ids)
order = [m for m, _, _ in MODELS] + [f"{m}-blind" for m, _, _ in MODELS]
print(f"{summary['n_items']} tool calls, {summary['n_questions']} questions; 95% bootstrap CIs over items\n")
print("| predictor | Brier skill vs uniform | accuracy | log loss |\n|---|---|---|---|")
for m in [m for m in order if m in summary["models"]]:
    v = summary["models"][m]
    print(f"| {names.get(m, m)} | {v['skill'][0]:.3f} [{v['skill'][1]:.3f}, {v['skill'][2]:.3f}] | "
          f"{v['accuracy'][0]:.0%} [{v['accuracy'][1]:.0%}, {v['accuracy'][2]:.0%}] | {v['logloss'][0]:.2f} |")
(R / "summary_questions.json").write_text(json.dumps(summary, indent=1))
