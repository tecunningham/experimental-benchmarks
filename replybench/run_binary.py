"""ReplyBench yes/no tasks: will this email get a reply? will this merge request be merged?

The model sees a batch of items (no tools, no internet) and returns a probability for each.
"""
import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.llm import complete

SYSTEM = "You are an expert forecaster of how people respond. You have no internet access."


def fmt_email(e):
    return (f"id: {e['id']}\nlist: {e['list']}\nfrom: {e['from']}\nsent: {e['date']} UTC\nsubject: {e['subject']}\n"
            f"body:\n{e['body'][:1500]}")


def fmt_pr(m):
    return (f"id: {m['id']}\nproject: {m['project']} ({m['host']})\nauthor: {m['author']}\nopened: {m['created']} UTC\n"
            f"draft: {m['draft']}\ntarget branch: {m['target_branch']}\ntitle: {m['title']}\n"
            f"description:\n{m['description'][:1200]}\nfiles changed: {m['n_files']}\ndiff (truncated):\n{m['diff'][:1500]}")


TASKS = {
    "email": dict(data="replybench/email/data/emails.jsonl", fmt=fmt_email, batch=10, field="p_reply", prompt="""\
Below are {n} emails that each started a new thread on a public Apache Software Foundation mailing list in
August or early September 2026. They are a random sample of human-written thread starters.

For each, predict the probability that at least one person OTHER than the sender replied to it on the list
(measured about 6 weeks later).

{items}

Respond with ONLY a JSON list, one object per email, same order: [{{"id": "<id>", "p_reply": <0-1>}}, ...]"""),
    "pr": dict(data="replybench/pr/data/prs.jsonl", fmt=fmt_pr, batch=5, field="p_merge", prompt="""\
Below are {n} merge requests opened on open-source GitLab projects between mid-July and the end of August
2026. They are a random sample of all MRs opened by humans in that period, whatever happened to them.

For each, predict the probability that it was merged within 30 days of being opened.

{items}

Respond with ONLY a JSON list, one object per MR, same order: [{{"id": "<id>", "p_merge": <0-1>}}, ...]"""),
}


def run_batch(batch, task, model):
    t = TASKS[task]
    prompt = t["prompt"].format(n=len(batch), items="\n\n---\n\n".join(t["fmt"](x) for x in batch))
    for _ in range(3):
        try:
            preds = json.loads(re.search(r"\[.*\]", complete(prompt, model, SYSTEM), re.S).group(0))
            by_id = {str(p["id"]): float(p[t["field"]]) for p in preds}
            if all(str(x["id"]) in by_id for x in batch):
                return [{"id": x["id"], "p": min(max(by_id[str(x["id"])], 0.0), 1.0)} for x in batch]
        except Exception as e:
            print("retry:", e, file=sys.stderr)
    raise RuntimeError("batch failed")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", choices=TASKS, required=True)
    p.add_argument("--model", required=True)
    a = p.parse_args()
    t = TASKS[a.task]
    items = [json.loads(l) for l in open(t["data"])]
    batches = [items[i:i + t["batch"]] for i in range(0, len(items), t["batch"])]
    with ThreadPoolExecutor(6) as ex:
        preds = [r for b in ex.map(lambda b: run_batch(b, a.task, a.model), batches) for r in b]
    out = Path(f"replybench/{a.task}/results/{a.model}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in preds:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(preds)} -> {out}")


if __name__ == "__main__":
    main()
