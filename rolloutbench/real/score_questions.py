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


BLIND = R / "qpreds" / "claude-opus-5-5-blind.jsonl"  # questions-only predictor (no session, no call)
blind = {r["id"]: r["probs"] for r in map(json.loads, open(BLIND))} if BLIND.exists() else {}
# "hard" questions: the questions-only predictor puts < 50% on the right answer, so the wording doesn't give it away
hard = {i: [blind[i][q][a] < 0.5 for q, a in enumerate(k["answer"])] if i in blind else [True] * len(k["answer"])
        for i, k in key.items()}


def item_scores(probs, k, mask=None):
    bs, acc, ll = [], [], []
    for q, (p, n, a) in enumerate(zip(probs, k["n_options"], k["answer"])):
        if mask is not None and not mask[q]:
            continue
        brier = sum((x - (j == a)) ** 2 for j, x in enumerate(p))
        uniform = (1 - 1 / n) ** 2 + (n - 1) / n ** 2
        bs.append(1 - brier / uniform)
        acc.append(float(max(range(n), key=lambda j: p[j]) == a))
        ll.append(-math.log(max(p[a], 1e-3)))
    if not bs:
        return None
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
    h = [x for x in (item_scores(preds[i], key[i], hard[i]) for i in ids) if x]
    summary["models"][f.stem] = {k: list(mean_ci([x[j] for x in s])) for j, k in enumerate(["skill", "accuracy", "logloss"])}
    summary["models"][f.stem].update({f"{k}_hard": list(mean_ci([x[j] for x in h])) for j, k in enumerate(["skill", "accuracy"])})
    summary["models"][f.stem]["n"] = len(ids)
summary["n_hard_questions"] = sum(sum(v) for v in hard.values())
order = [m for m, _, _ in MODELS] + [f"{m}-blind" for m, _, _ in MODELS]
print(f"{summary['n_items']} tool calls, {summary['n_questions']} questions; 95% bootstrap CIs over items\n")
print(f"Hard questions: {summary['n_hard_questions']} where the questions-only predictor puts < 50% on the answer.\n")
print("| predictor | Brier skill (all) | accuracy (all) | Brier skill (hard) | accuracy (hard) |\n|---|---|---|---|---|")
ci = lambda v, f: f"{v[0]:{f}} [{v[1]:{f}}, {v[2]:{f}}]"
for m in [m for m in order if m in summary["models"]]:
    v = summary["models"][m]
    print(f"| {names.get(m, m)} | {ci(v['skill'], '.2f')} | {ci(v['accuracy'], '.0%')} | "
          f"{ci(v['skill_hard'], '.2f')} | {ci(v['accuracy_hard'], '.0%')} |")
(R / "summary_questions.json").write_text(json.dumps(summary, indent=1))
