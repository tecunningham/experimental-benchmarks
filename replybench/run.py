"""ReplyBench-HN: predict how Hacker News responds to each story.

The model sees title / domain / author / post time (and text for text posts) and predicts
final points, comment count, and P(points >= 50). Stories are batched to keep it cheap.
"""
import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.llm import complete

SYSTEM = "You are an expert forecaster of online community behaviour. You have no internet access."

PROMPT = """Below are {n} stories submitted to Hacker News (news.ycombinator.com) in early October 2026.
They are a uniform random sample of ALL story submissions in that period (most submissions get little attention).

For each story, predict its final outcome (measured ~1 week later):
- "points": final score (every story starts with 1 point)
- "comments": final number of comments
- "p50": probability that the story reaches 50 or more points

Stories:
{stories}

Respond with ONLY a JSON list, one object per story, in the same order:
[{{"id": <id>, "points": <int>, "comments": <int>, "p50": <float 0-1>}}, ...]"""


def fmt(s):
    lines = [f"id: {s['id']}", f"title: {s['title']}"]
    lines.append(f"domain: {s['domain']}" if s["domain"] else "type: text post (no link)")
    if s["text"]:
        lines.append(f"text: {s['text'][:500]}")
    lines += [f"author: {s['author']}", f"posted: {s['posted_utc']} UTC"]
    return "\n".join(lines)


def run_batch(batch, model):
    prompt = PROMPT.format(n=len(batch), stories="\n\n".join(fmt(s) for s in batch))
    for _ in range(3):
        try:
            text = complete(prompt, model, SYSTEM)
            preds = json.loads(re.search(r"\[.*\]", text, re.S).group(0))
            by_id = {int(p["id"]): p for p in preds}
            if all(s["id"] in by_id for s in batch):
                return [by_id[s["id"]] for s in batch]
        except Exception as e:
            print("retry:", e, file=sys.stderr)
    raise RuntimeError("batch failed")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--data", default="replybench/data/hn_stories.jsonl")
    p.add_argument("--batch", type=int, default=25)
    a = p.parse_args()

    stories = [json.loads(l) for l in open(a.data)]
    batches = [stories[i:i + a.batch] for i in range(0, len(stories), a.batch)]
    with ThreadPoolExecutor(4) as ex:
        preds = [p for b in ex.map(lambda b: run_batch(b, a.model), batches) for p in b]
    out = Path(f"replybench/results/{a.model}.jsonl")
    with open(out, "w") as f:
        for p in preds:
            f.write(json.dumps(p) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
