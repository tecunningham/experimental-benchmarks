"""Build RolloutBench-Real items from public, real-world agent sessions on Hugging Face.

Sources (pinned revisions; raw files are downloaded locally and never committed):
  - crispwisp/wisp-claude-code-sessions: Claude Code on one person's real workstation (Jun-Jul 2026)
  - lewtun/ml-intern-sessions: an ML agent doing real training/data work on HF (Jun-Sep 2026)

Each item is one tool call: the session so far (truncated), the call, and the real result.
"""
import argparse
import json
import random
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SOURCES = {
    "wisp": ("crispwisp/wisp-claude-code-sessions", "c2c90b59174318ab0b163ec9c9ac82bb879288ce", "transcripts/-home-me"),
    "ml-intern": ("lewtun/ml-intern-sessions", "b86771afabadfd4b7bba10981cf42725e4720f36", "sessions"),
}
MIN_DATE = "2026-06-01"  # around the predictors' training cutoff

# tool name -> category; tools not listed (file writes/edits, planning, todo lists) are skipped
CATEGORY = {
    "Bash": "shell", "bash": "shell",
    "Read": "file read", "read": "file read",
    "WebFetch": "web", "WebSearch": "web", "web_search": "web", "fetch_hf_docs": "web", "explore_hf_docs": "web",
    "hub_repo_search": "API call", "hub_repo_details": "API call", "hf_inspect_dataset": "API call",
    "hf_repo_files": "API call", "hf_papers": "API call", "paper_search": "API call",
    "github_find_examples": "API call", "github_read_file": "API call", "github_list_repos": "API call",
    "hf_jobs": "GPU job",
    "research": "sub-agent", "Task": "sub-agent", "Agent": "sub-agent", "TaskOutput": "sub-agent",
    "AskUserQuestion": "human reply",
}
CAP = {"shell": 70, "file read": 25, "web": 40, "API call": 40, "GPU job": 40, "sub-agent": 30, "human reply": 10}
HISTORY_CHARS, RESULT_CHARS, TARGET_CHARS = 12000, 600, 4000


def hf(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def download(raw_dir: Path):
    for name, (repo, rev, prefix) in SOURCES.items():
        d = raw_dir / name
        d.mkdir(parents=True, exist_ok=True)
        tree = json.loads(hf(f"https://huggingface.co/api/datasets/{repo}/tree/{rev}/{prefix}?recursive=true"))
        paths = [t["path"] for t in tree if t["type"] == "file" and t["path"].endswith(".jsonl") and t.get("size", 1)]

        def get(p):
            out = d / p.replace("/", "__")
            if not out.exists():
                out.write_bytes(hf(f"https://huggingface.co/datasets/{repo}/resolve/{rev}/{p}"))

        with ThreadPoolExecutor(8) as ex:
            list(ex.map(get, paths))
        print(f"{name}: {len(paths)} sessions")


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(c.get("text", "[image]" if c.get("type") == "image" else "") for c in content if isinstance(c, dict))
    return json.dumps(content)


def events(path):
    """Flatten a Claude-Code-style session into ordered events."""
    evs, calls = [], {}
    for line in open(path, errors="replace"):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        m, ts = r.get("message"), r.get("timestamp", "")
        if not isinstance(m, dict):
            continue
        c = m.get("content")
        if isinstance(c, str):
            evs.append({"kind": m.get("role"), "text": c, "ts": ts})
            continue
        for b in c or []:
            if not isinstance(b, dict):
                continue
            t = b.get("type")
            if t == "text":
                evs.append({"kind": m.get("role"), "text": b.get("text", ""), "ts": ts})
            elif t == "tool_use":
                calls[b["id"]] = {"kind": "call", "name": b.get("name"), "input": b.get("input"), "ts": ts}
                evs.append(calls[b["id"]])
            elif t == "tool_result" and b.get("tool_use_id") in calls:
                evs.append({"kind": "result", "call": calls[b["tool_use_id"]], "text": text_of(b.get("content")),
                            "is_error": bool(b.get("is_error")), "ts": ts})
    return evs


def trunc(s, n):
    s = s or ""
    return s if len(s) <= n else s[:n] + f"\n…[{len(s) - n} more chars]"


def render(e):
    if e["kind"] == "call":
        return f"<tool_call name=\"{e['name']}\">\n{trunc(json.dumps(e['input'], ensure_ascii=False), 1500)}\n</tool_call>"
    if e["kind"] == "result":
        return f"<tool_result>\n{trunc(e['text'], RESULT_CHARS)}\n</tool_result>"
    return f"<{e['kind']}>\n{trunc(e['text'], 1000)}\n</{e['kind']}>"


def history(evs):
    """The session's first user message + as many recent events as fit in the budget."""
    first = next((e for e in evs if e["kind"] == "user" and e["text"].strip()), None)
    parts, used, cut = [], 0, False
    for e in reversed(evs):
        r = render(e)
        if used + len(r) > HISTORY_CHARS:
            cut = True
            break
        parts.append(r)
        used += len(r)
    parts.reverse()
    if cut:
        parts = ([render(first)] if first else []) + ["…[earlier events omitted]"] + parts
    return "\n\n".join(parts)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", default="rolloutbench/data/real/raw")
    p.add_argument("--out", default="rolloutbench/data/real/items.jsonl")
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    raw = Path(a.raw)
    download(raw)

    pool = []
    for src in SOURCES:
        for f in sorted((raw / src).glob("*.jsonl")):
            evs = events(f)
            for k, e in enumerate(evs):
                if e["kind"] != "result" or (e["ts"] or "9")[:10] < MIN_DATE:
                    continue
                cat = CATEGORY.get(e["call"]["name"])
                if not cat or len(e["text"].strip()) < 20:
                    continue
                pool.append({
                    "id": f"{src}/{f.stem[-36:]}/{k}", "source": src, "category": cat, "tool": e["call"]["name"],
                    "date": e["ts"][:10], "history": history([x for x in evs[:k] if x is not e["call"]]),
                    "call": e["call"]["input"],
                    "target": trunc(e["text"], TARGET_CHARS), "is_error": e["is_error"],
                    # baseline: the most recent earlier result from the same tool in this session
                    "copy_baseline": next((trunc(x["text"], TARGET_CHARS) for x in reversed(evs[:k]) if
                                           x["kind"] == "result" and x["call"]["name"] == e["call"]["name"]), ""),
                })
    rng = random.Random(a.seed)
    rng.shuffle(pool)
    items, n = [], {}
    for it in pool:
        if n.get(it["category"], 0) < CAP[it["category"]]:
            n[it["category"]] = n.get(it["category"], 0) + 1
            items.append(it)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"pool {len(pool)} -> {len(items)} items:", n)


if __name__ == "__main__":
    main()
