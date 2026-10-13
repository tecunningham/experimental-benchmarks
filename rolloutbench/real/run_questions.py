"""RolloutBench-Real, question format: predict facts about a tool result as probabilities (no judge needed).

The model sees the session so far and the tool call (never the result), plus the questions written from the
real result (make_questions.py), and returns a probability for each option.
--blind: show only the tool name and the questions (no session, no call), to measure how much the questions
themselves give away.
"""
import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.llm import complete

SYSTEM = ("You predict what tools return. You are shown part of a real AI-agent session and one tool call from it, "
          "and you forecast facts about the result that call actually produced. You have no tools and no internet.")

PROMPT = """{context}

Answer these questions about the result the call returned. For each question give a probability for every
option (they must sum to 1). Express real uncertainty: don't put 1.0 on an option unless you are sure.

{questions}

Respond with ONLY JSON: a list with one list of probabilities per question, in order, e.g. [[0.7, 0.3], [0.1, 0.6, 0.3]]"""


def context(it, blind):
    if blind:
        return f"An AI agent called the tool `{it['tool']}` on {it['date']}. You are not shown the session or the call."
    return (f"Session so far (truncated; the session took place on {it['date']}):\n\n{it['history']}\n\n"
            f"The agent now makes this tool call:\n<tool_call name=\"{it['tool']}\">\n"
            f"{json.dumps(it['call'], ensure_ascii=False, indent=1)[:4000]}\n</tool_call>")


def ask(it, qs, model, blind):
    qtext = "\n\n".join(f"Q{k + 1}. {q['question']}\n" + "\n".join(f"  ({j}) {o}" for j, o in enumerate(q["options"]))
                        for k, q in enumerate(qs))
    prompt = PROMPT.format(context=context(it, blind), questions=qtext)
    for _ in range(3):
        try:
            ps = json.loads(re.search(r"\[\s*\[.*\]\s*\]", complete(prompt, model, SYSTEM), re.S).group(0))
            out = []
            for q, p in zip(qs, ps):
                p = [max(float(x), 0.0) for x in p][:len(q["options"])]
                p += [0.0] * (len(q["options"]) - len(p))
                s = sum(p)
                out.append([x / s for x in p] if s > 0 else [1 / len(p)] * len(p))
            if len(out) == len(qs):
                return out
        except Exception as e:
            print("retry:", e, file=sys.stderr)
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--blind", action="store_true")
    p.add_argument("--workers", type=int, default=8)
    a = p.parse_args()
    items = {i["id"]: i for i in map(json.loads, open("rolloutbench/data/real/items.jsonl"))}
    qs = [(r["id"], r["questions"]) for r in map(json.loads, open("rolloutbench/data/real/questions.jsonl")) if r["questions"]]
    with ThreadPoolExecutor(a.workers) as ex:
        res = list(ex.map(lambda t: ask(items[t[0]], t[1], a.model, a.blind), qs))
    out = Path(f"rolloutbench/real/qpreds/{a.model}{'-blind' if a.blind else ''}.jsonl")
    out.parent.mkdir(exist_ok=True)
    with open(out, "w") as f:
        for (i, _), r in zip(qs, res):
            if r:
                f.write(json.dumps({"id": i, "probs": [[round(x, 4) for x in p] for p in r]}) + "\n")
    print(f"wrote {sum(r is not None for r in res)}/{len(qs)} -> {out}")


if __name__ == "__main__":
    main()
