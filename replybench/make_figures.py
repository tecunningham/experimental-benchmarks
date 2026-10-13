"""Render ReplyBench figures (SVG, no plotting deps) from data/ and results/."""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.stats import auc
from common.svg import MODEL_CLASS, Canvas, hbars, log_scatter

MODELS = [("claude-haiku-5-5", "Haiku 5.5"), ("claude-sonnet-5-5", "Sonnet 5.5"), ("claude-opus-5-5", "Opus 5.5")]
OUT = Path("replybench/figures")

truth = {s["id"]: s for s in map(json.loads, open("replybench/data/hn_stories.jsonl"))}
ids = list(truth)
hit = [truth[i]["score"] >= 50 for i in ids]
base = sum(hit) / len(hit)
preds = {name: {int(p["id"]): p for p in map(json.loads, open(f"replybench/results/{f}.jsonl"))} for f, name in MODELS}

rows = [("Base rate", 0.5, statistics.mean((base - h) ** 2 for h in hit), "neutral")]
for _, name in MODELS:
    p50 = [min(max(float(preds[name][i]["p50"]), 0), 1) for i in ids]
    rows.append((name, auc(p50, hit), statistics.mean((p - h) ** 2 for p, h in zip(p50, hit)), MODEL_CLASS[name]))

# 1. headline: ranking vs calibration
c = Canvas(720, 262)
c.title(24, 34, "Ranking: who will hit 50 points?", "AUC · higher is better")
end = hbars(c, 24, 78, 330, [(n, a, k) for n, a, _, k in rows], 1.0, lambda v: f"{v:.2f}")
c.title(374, 34, "Calibration: how likely?", "Brier score · lower is better")
hbars(c, 374, 78, 330, [(n, b, k) for n, _, b, k in rows], 0.08, lambda v: f"{v:.3f}", ref=rows[0][2])
c.text(24, end + 14, f"{len(ids)} random HN stories, 1–6 Oct 2026 (after training cutoff). Dashed line: base-rate Brier.", "t3")
(OUT / "headline.svg").write_text(c.svg())

# 2. predicted vs actual points, one panel per model
c = Canvas(720, 334)
c.title(24, 30, "Predicted vs. actual points", "Each dot is a story. Dots below the dashed line were over-predicted.")
for k, (_, name) in enumerate(MODELS):
    x0 = 58 + k * 228
    pts = [(max(float(preds[name][i]["points"]), 1), max(truth[i]["score"], 1)) for i in ids]
    med = statistics.median(p for p, _ in pts)
    log_scatter(c, x0, 86, 180, pts, MODEL_CLASS[name].replace("s", "d"), title=f"{name} · median guess {med:g}")
    c.text(x0 + 90, 86 + 180 + 30, "predicted points", "tick t3", "middle")
c.text(20, 180, "actual points", "tick t3", "middle", extra='transform="rotate(-90 20 180)"')
c.text(24, 322, f"Actual median: {statistics.median(truth[i]['score'] for i in ids):g} points. Values clipped to 1–1000.", "t3")
(OUT / "calibration.svg").write_text(c.svg())
print("wrote", *sorted(p.name for p in OUT.glob("*.svg")))
