"""Render ReplyBench figures (SVG, no plotting deps) from each task's data and results."""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.svg import MODEL_CLASS, Canvas, grouped_hbars, log_scatter, reliability

MODELS = [("claude-haiku-5-5", "Haiku 5.5"), ("claude-sonnet-5-5", "Sonnet 5.5"), ("claude-opus-5-5", "Opus 5.5")]
SERIES = [(name, MODEL_CLASS[name]) for _, name in MODELS]
TASKS = [("email", "Email: will anyone reply?"), ("pr", "PR: merged within 30 days?"),
         ("hn", "HN post: reaches 50 points?")]
OUT = Path("replybench/figures")
summ = {t: json.load(open(f"replybench/{t}/results/summary.json")) for t, _ in TASKS}


def metric(key):
    groups = [(label, [summ[t]["models"][f][key][0] for f, _ in MODELS]) for t, label in TASKS]
    cis = [[summ[t]["models"][f][key][1:] for f, _ in MODELS] for t, _ in TASKS]
    return groups, cis


# 1. headline: ranking and calibration across the three tasks, with 95% CIs
c = Canvas(720, 420)
c.title(24, 30, "Ranking: does the model know which ones?", "AUC · 0.5 = chance · higher is better")
c.legend(470, 30, SERIES)
g, ci = metric("auc")
end = grouped_hbars(c, 24, 66, 680, g, SERIES, 1, lambda v: f"{v:.2f}", label_w=190, bh=10, cis=ci, gap=16)
c.title(24, end + 22, "Calibration: does it beat the base rate?", "Brier skill vs. always predicting the base rate · > 0 beats it")
g, ci = metric("bss")
end = grouped_hbars(c, 24, end + 58, 680, g, SERIES, 1, lambda v: f"{v:+.2f}", label_w=190, bh=10, cis=ci, gap=16,
                    vmin=-1, ticks=4)
c.text(24, end + 12, f"Whiskers: 95% bootstrap CIs (clipped at −1). n = {summ['email']['n']} emails, {summ['pr']['n']} MRs, {summ['hn']['n']} HN posts.", "t3")
c.h = int(end + 26)
(OUT / "headline.svg").write_text(c.svg())

# 2. reliability diagrams for the yes/no tasks
LABEL = {"email": "replied", "pr": "merged_30d"}
c = Canvas(720, 330)
c.title(24, 30, "Are the probabilities calibrated?", "Predictions binned by probability; dot size ~ items in bin. On the dashed line = calibrated.")
c.legend(24, 68, SERIES)
for k, (t, label) in enumerate(TASKS[:2]):
    items = {str(x["id"]): bool(x[LABEL[t]]) for x in map(json.loads, open(next(Path(f"replybench/{t}/data").glob("*.jsonl"))))}
    curves = []
    for f, name in MODELS:
        pr = [(r["p"], items[str(r["id"])]) for r in map(json.loads, open(f"replybench/{t}/results/{f}.jsonl"))]
        pts = []
        for lo in (0, 0.2, 0.4, 0.6, 0.8):
            b = [(p, y) for p, y in pr if lo <= p < lo + 0.2 or (lo == 0.8 and p == 1)]
            if len(b) >= 5:
                pts.append((statistics.mean(p for p, _ in b), statistics.mean(y for _, y in b), len(b)))
        curves.append((MODEL_CLASS[name], pts))
    x0 = 70 + k * 340
    reliability(c, x0, 100, 190, curves, title=label)
    c.text(x0 + 95, 100 + 190 + 30, "predicted probability", "tick t3", "middle")
c.text(30, 195, "observed rate", "tick t3", "middle", extra='transform="rotate(-90 30 195)"')
(OUT / "reliability.svg").write_text(c.svg())

# 3. HN: predicted vs actual points, one panel per model
truth = {s["id"]: s for s in map(json.loads, open("replybench/hn/data/hn_stories.jsonl"))}
ids = list(truth)
preds = {name: {int(p["id"]): p for p in map(json.loads, open(f"replybench/hn/results/{f}.jsonl"))} for f, name in MODELS}
c = Canvas(720, 334)
c.title(24, 30, "HN: predicted vs. actual points", "Each dot is a story. Dots below the dashed line were over-predicted.")
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
