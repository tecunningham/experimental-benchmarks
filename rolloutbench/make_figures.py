"""Render RolloutBench figures (SVG, no plotting deps) from committed grades and pilot results."""
import difflib
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.models import MODELS, TIER, TIERS
from common.stats import mean_ci
from common.svg import TIER_CLASS, Canvas, hbars, heatmap

OUT = Path("rolloutbench/figures")
grades = [json.loads(l) for l in open("rolloutbench/real/grades.jsonl")]
models = [(m, n) for m, n, _ in MODELS if all(m in g["grades"] for g in grades)]
LEGEND = [(t, TIER_CLASS[t]) for t in TIERS if any(TIER[m] == t for m, _ in models)]
ROWH = 19

# 1. headline: real-trace judge score and outcome accuracy, all models, 95% CIs
score = {m: mean_ci([g["grades"][m]["score"] for g in grades]) for m, _ in models}
right = {m: mean_ci([float(bool(g["grades"][m]["outcome_right"])) for g in grades]) for m, _ in models}
c = Canvas(720, 140 + len(models) * ROWH)
c.title(24, 30, "How close is the predicted result?", "Blind judge score, 0–10")
c.title(384, 30, "Is the basic outcome right?", "Succeeded/failed, found/not found, …")
c.legend(24 + 84, 70, LEGEND)
end = hbars(c, 24, 94, 340, [(n, score[m][0], TIER_CLASS[TIER[m]]) for m, n in models], 10, lambda v: f"{v:.1f}",
            cis=[score[m][1:] for m, _ in models], bh=13, gap=6)
hbars(c, 384, 94, 320, [("", right[m][0], TIER_CLASS[TIER[m]]) for m, _ in models], 1, lambda v: f"{v:.0%}",
      cis=[right[m][1:] for m, _ in models], label_w=0, bh=13, gap=6)
c.text(24, end + 12, f"{len(grades)} tool calls from 75 real agent sessions (Jun–Sep 2026). Whiskers: 95% bootstrap CIs.", "t3")
c.h = int(end + 26)
(OUT / "headline.svg").write_text(c.svg())

# 2. by tool category: heatmap of mean judge score (categories with >= 10 calls)
cats = sorted({g["category"] for g in grades}, key=lambda k: -sum(g["category"] == k for g in grades))
cats = [k for k in cats if sum(g["category"] == k for g in grades) >= 10]
best = models[-1][0]
cats.sort(key=lambda k: -statistics.mean(g["grades"][best]["score"] for g in grades if g["category"] == k))
vals = [[statistics.mean(g["grades"][m]["score"] for g in grades if g["category"] == k) for k in cats] for m, _ in models]
c = Canvas(720, 110 + len(models) * 24)
c.title(24, 30, "Judge score by kind of tool call (0–10, darker = better)",
        "Templated results (sub-agent reports, job status) are easiest; live world state (APIs, web) is hardest")
end = heatmap(c, 24, 88, [n for _, n in models], [f"{k} ({sum(g['category'] == k for g in grades)})" for k in cats],
              vals, 1.5, 7.5, lambda v: f"{v:.1f}", label_w=84, cw=98)
c.text(24, end + 18, "Per-category n is 25–70, so differences of ~1 point within a column are within noise.", "t3")
c.h = int(end + 30)
(OUT / "by_tool.svg").write_text(c.svg())

# 3. sandbox pilot: outputs that follow from code vs outputs that depend on the machine
EMPTY, MACHINE = "(Bash completed with no output)", {"sysinfo", "pystdlib"}
traces = [json.loads(l) for l in open("rolloutbench/data/traces.jsonl")]
truth = {(t["task_id"], k): s["output"] for t in traces for k, s in enumerate(t["steps"]) if s["output"].strip() != EMPTY}
sim = lambda a, b: difflib.SequenceMatcher(None, a.strip()[:3000], b.strip()[:3000], autojunk=False).ratio()
pilot = [(m, n) for m, n in models if Path(f"rolloutbench/results/{m}.jsonl").exists()]
vals = {}
for m, _ in pilot:
    pr = {(p["task_id"], p["step"]): p["prediction"] for p in map(json.loads, open(f"rolloutbench/results/{m}.jsonl"))}
    for g in ("code", "machine"):
        vals[m, g] = mean_ci([sim(pr[k], v) for k, v in truth.items() if (k[0] in MACHINE) == (g == "machine")])
c = Canvas(720, 130 + len(pilot) * ROWH)
c.title(24, 30, "Sandbox pilot: code is easy, the machine is not", "Similarity of predicted vs. real shell output (synthetic tasks)")
c.legend(470, 30, LEGEND)
c.title(24 + 84, 64, "Output follows from code (27)")
end = hbars(c, 24, 84, 340, [(n, vals[m, "code"][0], TIER_CLASS[TIER[m]]) for m, n in pilot], 1, lambda v: f"{v:.2f}",
            cis=[vals[m, "code"][1:] for m, _ in pilot], bh=13, gap=6)
c.title(384, 64, "Output depends on machine state (27)")
hbars(c, 384, 84, 320, [("", vals[m, "machine"][0], TIER_CLASS[TIER[m]]) for m, _ in pilot], 1, lambda v: f"{v:.2f}",
      cis=[vals[m, "machine"][1:] for m, _ in pilot], label_w=0, bh=13, gap=6)
c.text(24, end + 12, "76 calls from 8 synthetic sandbox tasks. Whiskers: 95% bootstrap CIs.", "t3")
c.h = int(end + 26)
(OUT / "sandbox.svg").write_text(c.svg())
print("wrote", *sorted(p.name for p in OUT.glob("*.svg")), "for", len(models), "models")
