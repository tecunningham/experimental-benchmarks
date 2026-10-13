"""RolloutBench-Real: predict the real result of each tool call from a real agent session."""
import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.llm import complete

SYSTEM = ("You predict what tools return. You are shown a real AI-agent session and one tool call from it; "
          "predict the result that call actually produced. You have no tools and no internet access.")

PROMPT = """Session so far (truncated; the session took place on {date}):

{history}

The agent now makes this tool call:
<tool_call name="{tool}">
{call}
</tool_call>

Predict the result this call returned, as it would appear in the transcript. Be concrete: give the actual
text, numbers, file contents, errors, search hits, or reply you expect, not a description of them. If the
real result is long, write its beginning and the parts that matter most for the agent's next decision
(at most ~2000 characters).
Respond with ONLY the predicted result inside <result></result> tags."""


def prompt(it):
    return PROMPT.format(date=it["date"], history=it["history"], tool=it["tool"],
                         call=json.dumps(it["call"], ensure_ascii=False, indent=1)[:4000])


def predict(it, model):
    for _ in range(3):
        try:
            text = complete(prompt(it), model, SYSTEM)
            m = re.search(r"<result>\n?(.*?)\n?</result>", text, re.S)
            return m.group(1) if m else text
        except Exception as e:
            print("retry:", e, file=sys.stderr)
    return ""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--data", default="rolloutbench/data/real/items.jsonl")
    p.add_argument("--workers", type=int, default=8)
    a = p.parse_args()
    items = [json.loads(l) for l in open(a.data)]
    with ThreadPoolExecutor(a.workers) as ex:
        preds = list(ex.map(lambda it: predict(it, a.model), items))
    out = Path(f"rolloutbench/data/real/pred-{a.model}.jsonl")
    with open(out, "w") as f:
        for it, pr in zip(items, preds):
            f.write(json.dumps({"id": it["id"], "prediction": pr}, ensure_ascii=False) + "\n")
    print(f"wrote {len(preds)} -> {out}")


if __name__ == "__main__":
    main()
