"""Turn each real tool result into checkable multiple-choice questions (written once, before any model predicts).

The question writer sees the tool call and the REAL result. Predictors later see the session and the call but
never the result, and answer with probabilities, so grading is exact (like ReplyBench) and needs no judge.
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

SYSTEM = "You write precise, fair test questions about what a tool call returned."

PROMPT = """An AI agent made this tool call during a real session:
<tool_call name="{tool}">
{call}
</tool_call>

The REAL result was:
<real_result>
{target}
</real_result>

Write 2 to 4 multiple-choice questions about this result that a forecaster, who sees the session and the call
but NOT the result, would have to predict. Rules:
- Ask about what matters for the agent's next decision: success vs. failure, the error type, whether something
  exists or was found, key numbers (bucketed into ranges), names, statuses, which of several things appears.
- Each question must be answered unambiguously by the real result.
- Give 2 to 5 options. Make the wrong options plausible, and don't let the wording hint at the answer
  (include options like "none" / "0" / "no error" where natural). Don't always put the answer first.
- Don't ask about things already stated in the call itself, or trivia like exact timestamps or hashes.

Respond with ONLY JSON: [{{"question": "...", "options": ["...", "..."], "answer": <index of correct option>}}, ...]"""


def make(it, model, seed):
    prompt = PROMPT.format(tool=it["tool"], call=json.dumps(it["call"], ensure_ascii=False)[:3000], target=it["target"])
    for _ in range(3):
        try:
            qs = json.loads(re.search(r"\[.*\]", complete(prompt, model, SYSTEM), re.S).group(0))
            out = []
            for k, q in enumerate(qs[:4]):
                opts, ans = [str(o) for o in q["options"]], int(q["answer"])
                if not (2 <= len(opts) <= 5 and 0 <= ans < len(opts)):
                    continue
                order = list(range(len(opts)))  # reshuffle so answer position carries no signal
                random.Random(f"{seed}-{it['id']}-{k}").shuffle(order)
                out.append({"question": q["question"], "options": [opts[i] for i in order], "answer": order.index(ans)})
            if out:
                return out
        except Exception as e:
            print("retry:", e, file=sys.stderr)
    return []


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="claude-opus-5-5")
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    items = [json.loads(l) for l in open("rolloutbench/data/real/items.jsonl")]
    with ThreadPoolExecutor(8) as ex:
        qs = list(ex.map(lambda it: make(it, a.model, a.seed), items))
    with open("rolloutbench/data/real/questions.jsonl", "w") as f:
        for it, q in zip(items, qs):
            f.write(json.dumps({"id": it["id"], "questions": q}, ensure_ascii=False) + "\n")
    print(f"{sum(map(len, qs))} questions for {sum(bool(q) for q in qs)}/{len(items)} items")


if __name__ == "__main__":
    main()
