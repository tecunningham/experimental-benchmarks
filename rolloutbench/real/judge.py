"""Grade each prediction on its own against the real tool result (no other predictions in view).

Grades are cached per (item, model) in grades.jsonl, so adding a model only grades that model.
"""
import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.llm import complete

SYSTEM = "You are a strict, consistent grader. You compare a predicted tool result with the real one."
GRADES = Path("rolloutbench/real/grades.jsonl")

PROMPT = """An AI agent made this tool call:
<tool_call name="{tool}">
{call}
</tool_call>

The REAL result was:
<real_result>
{target}
</real_result>

A forecaster, without running the call, predicted the result:
<prediction>
{pred}
</prediction>

Score the prediction from 0 to 10 for how well it anticipated the real result: the outcome (success, failure,
error type), the facts, numbers, names, file contents, search hits, or reply that would matter for the agent's
next decision. Ignore formatting, phrasing and length.
- 10: essentially the same information
- 7: right outcome and most key details
- 4: right general outcome, but key details wrong or missing
- 1: mostly wrong, with a few correct elements
- 0: wrong outcome or unrelated
Also say whether it got the basic outcome right (e.g. succeeded vs failed, found vs not found, yes vs no).

Respond with ONLY JSON: {{"score": <0-10>, "outcome_right": <true|false>}}"""


def grade(it, pred, model):
    prompt = PROMPT.format(tool=it["tool"], call=json.dumps(it["call"], ensure_ascii=False)[:3000],
                           target=it["target"], pred=pred[:3000])
    for _ in range(3):
        try:
            g = json.loads(re.search(r"\{.*\}", complete(prompt, model, SYSTEM), re.S).group(0))
            return {"score": float(g["score"]), "outcome_right": bool(g["outcome_right"])}
        except Exception as e:
            print("retry:", e, file=sys.stderr)
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--judge", default="claude-opus-5-5")
    p.add_argument("--workers", type=int, default=10)
    a = p.parse_args()
    items = {i["id"]: i for i in map(json.loads, open("rolloutbench/data/real/items.jsonl"))}
    preds = {}
    for f in sorted(Path("rolloutbench/data/real").glob("pred-*.jsonl")):
        rows = [json.loads(l) for l in open(f)]
        if len(rows) == len(items):  # only finished runs
            preds[f.stem.removeprefix("pred-")] = {r["id"]: r["prediction"] for r in rows}
    done = {(r["id"], r["model"]) for r in map(json.loads, open(GRADES))} if GRADES.exists() else set()
    todo = [(i, m) for m in preds for i in items if (i, m) not in done]
    print(f"{len(todo)} predictions to grade ({len(preds)} models)", flush=True)
    with ThreadPoolExecutor(a.workers) as ex, open(GRADES, "a") as f:
        for (i, m), g in zip(todo, ex.map(lambda t: grade(items[t[0]], preds[t[1]][t[0]], a.judge), todo)):
            if g:
                it = items[i]
                f.write(json.dumps({"id": i, "model": m, "source": it["source"], "category": it["category"],
                                    "tool": it["tool"], **g}) + "\n")
                f.flush()


if __name__ == "__main__":
    main()
