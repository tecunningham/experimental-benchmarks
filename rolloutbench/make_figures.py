"""Render RolloutBench figures (SVG, no plotting deps) from committed grades and pilot results."""
import difflib
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.svg import MODEL_CLASS, Canvas, grouped_hbars, hbars

MODELS = [("claude-haiku-5-5", "Haiku 5.5"), ("claude-sonnet-5-5", "Sonnet 5.5"), ("claude-opus-5-5", "Opus 5.5")]
SERIES = [(name, MODEL_CLASS[name]) for _, name in MODELS]
OUT = Path("rolloutbench/figures")
grades = [json.loads(l) for l in open("rolloutbench/real/grades.jsonl")]

# 1. headline: real-trace judge score and outcome accuracy
c = Canvas(720, 230)
c.title(24, 34, "How close is the predicted result?", "Blind judge score, 0–10")
end = hbars(c, 24, 78, 330, [(n, statistics.mean(g["grades"][f]["score"] for g in grades), MODEL_CLASS[n])
                              for f, n in MODELS], 10, lambda v: f"{v:.1f}")
c.title(374, 34, "Is the basic outcome right?", "Succeeded/failed, found/not found, …")
hbars(c, 374, 78, 330, [(n, statistics.mean(bool(g["grades"][f]["outcome_right"]) for g in grades), MODEL_CLASS[n])
                        for f, n in MODELS], 1, lambda v: f"{v:.0%}")
c.text(24, end + 14, f"{len(grades)} tool calls from 75 real agent sessions (Jun–Sep 2026); models get no tools or internet.", "t3")
(OUT / "headline.svg").write_text(c.svg())

# 2. by tool category (categories with at least 10 items)
cats = sorted({g["category"] for g in grades}, key=lambda k: -sum(g["category"] == k for g in grades))
cats = [k for k in cats if sum(g["category"] == k for g in grades) >= 10]
groups = []
for k in sorted(cats, key=lambda k: -statistics.mean(g["grades"]["claude-opus-5-5"]["score"] for g in grades if g["category"] == k)):
    sub = [g for g in grades if g["category"] == k]
    groups.append((f"{k} ({len(sub)})", [statistics.mean(g["grades"][f]["score"] for g in sub) for f, _ in MODELS]))
c = Canvas(720, 112 + len(groups) * 45)
c.title(24, 34, "Judge score by kind of tool call", "Templated results (sub-agent reports, job status) are easiest; live world state (APIs, web) is hardest")
c.legend(24, 80, SERIES)
end = grouped_hbars(c, 24, 100, 680, groups, SERIES, 10, lambda v: f"{v:.1f}", label_w=120)
(OUT / "by_tool.svg").write_text(c.svg())

# 3. sandbox pilot: outputs that follow from code vs outputs that depend on the machine
EMPTY, MACHINE = "(Bash completed with no output)", {"sysinfo", "pystdlib"}
traces = [json.loads(l) for l in open("rolloutbench/data/traces.jsonl")]
truth = {(t["task_id"], k): s["output"] for t in traces for k, s in enumerate(t["steps"]) if s["output"].strip() != EMPTY}
sim = lambda a, b: difflib.SequenceMatcher(None, a.strip()[:3000], b.strip()[:3000], autojunk=False).ratio()
vals = {"code": [], "machine": []}
for f, _ in MODELS:
    pr = {(p["task_id"], p["step"]): p["prediction"] for p in map(json.loads, open(f"rolloutbench/results/{f}.jsonl"))}
    for g in vals:
        vals[g].append(statistics.mean(sim(pr[k], v) for k, v in truth.items() if (k[0] in MACHINE) == (g == "machine")))
c = Canvas(720, 212)
c.title(24, 34, "Sandbox pilot: code is easy, the machine is not", "Similarity of predicted vs. real shell output (76 calls from 8 synthetic tasks)")
c.legend(24, 80, SERIES)
grouped_hbars(c, 24, 100, 680, [("follows from code", vals["code"]), ("depends on machine", vals["machine"])],
              SERIES, 1, lambda v: f"{v:.2f}", label_w=140, bh=10)
(OUT / "sandbox.svg").write_text(c.svg())
print("wrote", *sorted(p.name for p in OUT.glob("*.svg")))
