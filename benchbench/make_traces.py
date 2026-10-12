"""Record agent traces for BenchBench: a Claude agent (Bash tool only) works each task in an
empty sandbox dir; we keep every (command, output) pair.
"""
import argparse
import json
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


# Nudge the agent toward many small calls, so each trace has many predictable-ish steps.
STYLE = ("IMPORTANT: Work incrementally. Make a separate Bash call for every step (create file, run, inspect, "
         "check a value, ...), so you look at each output before deciding the next step. Never chain steps "
         "with && or ; and never write a file and run it in the same call. Expect to make 10-20 Bash calls. "
         "Work in the current directory.")


def run_task(task, model):
    with tempfile.TemporaryDirectory(prefix="bb_") as d:
        cmd = ["claude", "-p", task["prompt"] + "\n\n" + STYLE, "--model", model, "--tools", "Bash",
               "--permission-mode", "bypassPermissions", "--setting-sources", "",
               "--no-session-persistence", "--output-format", "stream-json", "--verbose",
               "--max-turns", "40"]
        out = subprocess.run(cmd, capture_output=True, text=True, cwd=d, timeout=1200).stdout
    calls, results = {}, {}
    order = []
    for line in out.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = ev.get("message") or {}
        for block in msg.get("content") or [] if isinstance(msg.get("content"), list) else []:
            if block.get("type") == "tool_use" and block.get("name") == "Bash":
                calls[block["id"]] = block["input"]
                order.append(block["id"])
            elif block.get("type") == "tool_result":
                c = block.get("content")
                if isinstance(c, list):
                    c = "".join(x.get("text", "") for x in c)
                results[block["tool_use_id"]] = {"output": c or "", "is_error": bool(block.get("is_error"))}
    clean = lambda t: re.sub(r"\n?Shell cwd was reset to .*", "", t).replace(d, "/sandbox")
    steps = [{"command": clean(calls[i].get("command", "")), "description": calls[i].get("description"),
              "output": clean(results[i]["output"]), "is_error": results[i]["is_error"]}
             for i in order if i in results]
    return {"task_id": task["id"], "prompt": task["prompt"], "agent_model": model, "steps": steps}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="claude-haiku-5-5")
    p.add_argument("--out", default="benchbench/data/traces.jsonl")
    a = p.parse_args()
    tasks = json.load(open("benchbench/tasks.json"))
    with ThreadPoolExecutor(4) as ex:
        traces = list(ex.map(lambda t: run_task(t, a.model), tasks))
    with open(a.out, "w") as f:
        for tr in traces:
            print(tr["task_id"], len(tr["steps"]), "steps")
            f.write(json.dumps(tr) + "\n")


if __name__ == "__main__":
    main()
