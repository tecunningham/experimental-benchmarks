"""Grade predictions against the real tool result with a blind LLM judge.

For each item, the judge sees the call, the real result, and every model's prediction (shuffled,
anonymised), and scores each one 0-10 on the information that matters, ignoring formatting.
"""
import argparse
import json
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.llm import complete

SYSTEM = "You are a strict, consistent grader. You compare predicted tool results with the real ones."

PROMPT = """An AI agent made this tool call:
<tool_call name="{tool}">
{call}
</tool_call>

The REAL result was:
<real_result>
{target}
</real_result>

Several forecasters, without running the call, predicted the result:
{preds}

Score each prediction from 0 to 10 for how well it anticipated the real result: the outcome (success,
failure, error type), the facts, numbers, names, file contents, search hits, or reply that would matter for
the agent's next decision. Ignore formatting, phrasing and length.
- 10: essentially the same information
- 7: right outcome and most key details
- 4: right general outcome, but key details wrong or missing
- 1: mostly wrong, with a few correct elements
- 0: wrong outcome or unrelated
Also say for each whether it got the basic outcome right (e.g. succeeded vs failed, found vs not found, yes vs no).

Respond with ONLY JSON: {{"<label>": {{"score": <0-10>, "outcome_right": <true|false>}}, ...}}"""


def judge(it, preds, model, seed):
    names = list(preds)
    random.Random(f"{seed}-{it['id']}").shuffle(names)
    labels = {n: chr(ord("A") + i) for i, n in enumerate(names)}
    block = "\n\n".join(f"<prediction label=\"{labels[n]}\">\n{preds[n][:3000]}\n</prediction>" for n in names)
    prompt = PROMPT.format(tool=it["tool"], call=json.dumps(it["call"], ensure_ascii=False)[:3000],
                           target=it["target"], preds=block)
    for _ in range(3):
        try:
            g = json.loads(re.search(r"\{.*\}", complete(prompt, model, SYSTEM), re.S).group(0))
            return {n: g[labels[n]] for n in names}
        except Exception as e:
            print("retry:", e, file=sys.stderr)
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--judge", default="claude-opus-5-5")
    p.add_argument("--data", default="rolloutbench/data/real/items.jsonl")
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    items = [json.loads(l) for l in open(a.data)]
    preds = {}
    for f in sorted(Path("rolloutbench/data/real").glob("pred-*.jsonl")):
        for r in map(json.loads, open(f)):
            preds.setdefault(r["id"], {})[f.stem.removeprefix("pred-")] = r["prediction"]
    with ThreadPoolExecutor(8) as ex:
        grades = list(ex.map(lambda it: judge(it, preds[it["id"]], a.judge, a.seed), items))
    with open("rolloutbench/real/grades.jsonl", "w") as f:
        for it, g in zip(items, grades):
            if g:
                f.write(json.dumps({"id": it["id"], "source": it["source"], "category": it["category"],
                                    "tool": it["tool"], "grades": g}) + "\n")
    print(f"graded {sum(g is not None for g in grades)}/{len(items)}")


if __name__ == "__main__":
    main()
