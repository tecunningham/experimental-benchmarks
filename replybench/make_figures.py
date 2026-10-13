"""Render ReplyBench figures (SVG, no plotting deps) from each task's data and results."""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.models import MODELS, TIER, TIERS
from common.svg import TIER_CLASS, Canvas, hbars, log_scatter, reliability

TASKS = [("email", "Email: anyone replies?"), ("pr", "PR: merged in 30 days?"), ("hn", "HN: reaches 50 points?")]
OUT = Path("replybench/figures")
summ = {t: json.load(open(f"replybench/{t}/results/summary.json")) for t, _ in TASKS}
models = [(m, n) for m, n, _ in MODELS if all(m in summ[t]["models"] for t, _ in TASKS)]
LEGEND = [(t, TIER_CLASS[t]) for t in TIERS if any(TIER[m] == t for m, _ in models)]
LATEST = {}  # newest model per tier, for the less dense charts
for m, n in models:
    LATEST[TIER[m]] = (m, n)


def panel_row(c, y, key, vmin, vmax, fmt, ticks=4):
    """One small panel per task, models as rows (labels only on the first panel)."""
    end = y
    for k, (t, label) in enumerate(TASKS):
        x0, lw = (24, 84) if k == 0 else (24 + 84 + 196 * k, 0)
        c.text(x0 + lw, y - 10, label, "t1", extra='font-weight="600"')
        rows = [(n if k == 0 else "", summ[t]["models"][m][key][0], TIER_CLASS[TIER[m]]) for m, n in models]
        cis = [summ[t]["models"][m][key][1:] for m, _ in models]
        end = hbars(c, x0, y, lw + 182, rows, vmax, fmt, label_w=lw, bh=13, gap=6, cis=cis, vmin=vmin, ticks=ticks)
    return end


# 1. headline: ranking and calibration, one panel per task, 95% CIs
H = 2 * (len(models) * 19 + 110) + 40
c = Canvas(720, H)
c.title(24, 30, "Ranking: does the model know which ones?", "AUC · 0.5 = chance")
c.legend(470, 30, LEGEND)
end = panel_row(c, 84, "auc", 0.5, 1.0, lambda v: f"{v:.2f}", ticks=2)
c.title(24, end + 28, "Calibration: does it beat the base rate?", "Brier skill vs. always predicting the base rate · > 0 beats it")
end = panel_row(c, end + 82, "bss", -0.6, 0.6, lambda v: f"{v:+.2f}", ticks=2)
c.text(24, end + 12, f"Whiskers: 95% bootstrap CIs (clipped to axis). n = {summ['email']['n']} emails, "
                     f"{summ['pr']['n']} MRs, {summ['hn']['n']} HN posts.", "t3")
c.h = int(end + 26)
(OUT / "headline.svg").write_text(c.svg())

# 2. reliability diagrams (newest model per tier)
LABEL = {"email": "replied", "pr": "merged_30d"}
c = Canvas(720, 330)
c.title(24, 30, "Are the probabilities calibrated?", "Newest model per tier; dot size ~ items in bin. On the dashed line = calibrated.")
c.legend(24, 68, [(n, TIER_CLASS[t]) for t, (m, n) in LATEST.items()])
for k, (t, label) in enumerate(TASKS[:2]):
    items = {str(x["id"]): bool(x[LABEL[t]]) for x in map(json.loads, open(next(Path(f"replybench/{t}/data").glob("*.jsonl"))))}
    curves = []
    for tier, (m, _) in LATEST.items():
        pr = [(r["p"], items[str(r["id"])]) for r in map(json.loads, open(f"replybench/{t}/results/{m}.jsonl"))]
        pts = []
        for lo in (0, 0.2, 0.4, 0.6, 0.8):
            b = [(p, y) for p, y in pr if lo <= p < lo + 0.2 or (lo == 0.8 and p == 1)]
            if len(b) >= 5:
                pts.append((statistics.mean(p for p, _ in b), statistics.mean(y for _, y in b), len(b)))
        curves.append((TIER_CLASS[tier], pts))
    x0 = 70 + k * 340
    reliability(c, x0, 100, 190, curves, title=label)
    c.text(x0 + 95, 100 + 190 + 30, "predicted probability", "tick t3", "middle")
c.text(30, 195, "observed rate", "tick t3", "middle", extra='transform="rotate(-90 30 195)"')
(OUT / "reliability.svg").write_text(c.svg())

# 3. HN: predicted vs actual points (newest model per tier)
truth = {s["id"]: s for s in map(json.loads, open("replybench/hn/data/hn_stories.jsonl"))}
ids = list(truth)
c = Canvas(720, 300)
c.title(24, 30, "HN: predicted vs. actual points", "Each dot is a story. Dots below the dashed line were over-predicted.")
for k, (tier, (m, n)) in enumerate(LATEST.items()):
    preds = {int(p["id"]): p for p in map(json.loads, open(f"replybench/hn/results/{m}.jsonl"))}
    x0 = 50 + k * 168
    pts = [(max(float(preds[i]["points"]), 1), max(truth[i]["score"], 1)) for i in ids]
    med = statistics.median(p for p, _ in pts)
    log_scatter(c, x0, 86, 140, pts, TIER_CLASS[tier].replace("s", "d"), title=f"{n} · median {med:g}")
    c.text(x0 + 70, 86 + 140 + 30, "predicted points", "tick t3", "middle")
c.text(18, 156, "actual points", "tick t3", "middle", extra='transform="rotate(-90 18 156)"')
c.text(24, 290, f"Actual median: {statistics.median(truth[i]['score'] for i in ids):g} points. Values clipped to 1–1000.", "t3")
(OUT / "calibration.svg").write_text(c.svg())
print("wrote", *sorted(p.name for p in OUT.glob("*.svg")), "for", len(models), "models")
