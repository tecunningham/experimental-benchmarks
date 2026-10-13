"""RolloutBench: given an agent trace so far, predict the exact output of the next tool call.

For every step k of every trace the model sees the task, steps 1..k-1 with their true outputs,
and the command for step k, and must write the output it expects. No tools, no internet.
"""
import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.llm import complete

MAX_CTX_OUT = 1500  # chars of each earlier output shown as context

SYSTEM = ("You are simulating a computer. Given a transcript of an AI agent's shell session, you predict "
          "exactly what the next command prints. You have no tools and no internet access.")

PROMPT = """An AI agent is working on this task in an empty directory (/sandbox) on a Linux machine:

<task>
{task}
</task>

Shell session so far (earlier outputs may be truncated):
{history}

Next command:
<command>
{command}
</command>

Predict the exact combined stdout/stderr this command produces, as the agent's tool would show it.
Conventions: if the command fails, the output starts with "Exit code N" on its own line; if it prints
nothing, the output is exactly "(Bash completed with no output)".
Respond with ONLY the predicted output inside <output></output> tags."""


def trunc(s, n):
    return s if len(s) <= n else s[:n] + f"\n...[{len(s) - n} more chars]"


def items(traces):
    for t in traces:
        for k, step in enumerate(t["steps"]):
            history = "\n\n".join(
                f"<command>\n{s['command']}\n</command>\n<output>\n{trunc(s['output'], MAX_CTX_OUT)}\n</output>"
                for s in t["steps"][:k]) or "(none yet)"
            yield {"task_id": t["task_id"], "step": k, "command": step["command"], "target": step["output"],
                   "prompt": PROMPT.format(task=t["prompt"], history=history, command=step["command"])}


def predict(item, model):
    for _ in range(3):
        try:
            text = complete(item["prompt"], model, SYSTEM)
            m = re.search(r"<output>\n?(.*?)\n?</output>", text, re.S)
            return m.group(1) if m else text
        except Exception as e:
            print("retry:", e, file=sys.stderr)
    return ""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--data", default="rolloutbench/data/traces.jsonl")
    p.add_argument("--workers", type=int, default=8)
    a = p.parse_args()
    its = list(items(map(json.loads, open(a.data))))
    with ThreadPoolExecutor(a.workers) as ex:
        preds = list(ex.map(lambda it: predict(it, a.model), its))
    out = Path(f"rolloutbench/results/{a.model}.jsonl")
    with open(out, "w") as f:
        for it, pr in zip(its, preds):
            f.write(json.dumps({"task_id": it["task_id"], "step": it["step"], "prediction": pr}) + "\n")
    print(f"wrote {len(preds)} predictions -> {out}")


if __name__ == "__main__":
    main()
