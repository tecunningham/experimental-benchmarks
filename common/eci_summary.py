"""Correlate each benchmark metric with ECI across models; writes docs/eci.svg and docs/eci.md.

Also renders the per-benchmark ECI scatter plots (replybench/figures/eci.svg, rolloutbench/figures/eci.svg).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.eci import ECI
from common.models import MODELS, NAME, TIER, TIERS
from common.stats import corr_ci, pearson, spearman
from common.svg import TIER_CLASS, Canvas, hbars, xy_scatter

S = {t: json.load(open(f"replybench/{t}/results/summary.json")) for t in ("email", "pr", "hn")}
S["rollout"] = json.load(open("rolloutbench/real/summary.json"))
S["rollq"] = json.load(open("rolloutbench/real/summary_questions.json"))
METRICS = [  # (label, source, key, benchmark)
    ("Email reply · AUC", "email", "auc", "ReplyBench"),
    ("Email reply · Brier skill", "email", "bss", "ReplyBench"),
    ("PR merge · AUC", "pr", "auc", "ReplyBench"),
    ("PR merge · Brier skill", "pr", "bss", "ReplyBench"),
    ("HN 50+ points · AUC", "hn", "auc", "ReplyBench"),
    ("HN points · Spearman", "hn", "spearman_points", "ReplyBench"),
    ("Tool result · question Brier skill", "rollq", "skill", "RolloutBench"),
    ("Tool result · hard-question skill", "rollq", "skill_hard", "RolloutBench"),
    ("Tool result · judge score", "rollout", "score", "RolloutBench"),
    ("Tool result · outcome right", "rollout", "outcome_right", "RolloutBench"),
]


def points(src, key):
    ms = [m for m, _, _ in MODELS if m in ECI and m in S[src]["models"]]
    return ms, [ECI[m][0] for m in ms], [S[src]["models"][m][key][0] for m in ms]


rows = []
for label, src, key, bench in METRICS:
    ms, x, y = points(src, key)
    rows.append((label, bench, len(ms), corr_ci(x, y, pearson), corr_ci(x, y, spearman)))

# docs/eci.md: the correlation table
md = ["# Correlation with the Epoch Capabilities Index (ECI)", "", "[← back to the benchmark list](../README.md)", "",
      "Across the Claude models we tested that have an ECI score (Epoch AI). 95% CIs bootstrap over models, so",
      "with ~13 models they are wide.", "",
      "| metric | benchmark | models | Pearson r [95% CI] | Spearman ρ [95% CI] |", "|---|---|---|---|---|"]
for label, bench, n, (r, rl, rh), (s, sl, sh) in rows:
    md.append(f"| {label} | {bench} | {n} | {r:+.2f} [{rl:+.2f}, {rh:+.2f}] | {s:+.2f} [{sl:+.2f}, {sh:+.2f}] |")
md += ["", "ECI source: Epoch AI, [benchmark data](https://epoch.ai/data/benchmark_data.zip) "
           "(`eci_scores.csv`), fetched by [`common/fetch_eci.py`](../common/fetch_eci.py).", ""]
Path("docs/eci.md").write_text("\n".join(md))
print("\n".join(md))

# docs/eci.svg: one bar per metric
c = Canvas(720, 120 + len(rows) * 30)
c.title(24, 30, "How well does each metric track general capability?", "Pearson r with ECI across models · 95% bootstrap CIs over models")
end = hbars(c, 24, 76, 680, [(l, r[0], "s1" if b == "ReplyBench" else "s3") for l, b, _, r, _ in rows], 1,
            lambda v: f"{v:+.2f}", label_w=210, bh=16, gap=14, vmin=-1, cis=[r[1:] for *_, r, _ in rows])
c.legend(24, end + 14, [("ReplyBench", "s1"), ("RolloutBench", "s3")])
c.h = int(end + 30)
Path("docs/eci.svg").write_text(c.svg())


def scatter_fig(path, panels, title, sub):
    """panels: [(label, src, key, yr, fmt)] side by side."""
    w = (640 - 90 * (len(panels) - 1)) / len(panels)
    c = Canvas(720, 350)
    c.title(24, 30, title, sub)
    c.legend(24, 68, [(t, TIER_CLASS[t]) for t in TIERS])
    for k, (label, src, key, yr, fmt, yt) in enumerate(panels):
        ms = [m for m, _, _ in MODELS if m in ECI and m in S[src]["models"]]
        pts = [(ECI[m][0], ECI[m][1], S[src]["models"][m][key][0], S[src]["models"][m][key][1:],
                TIER_CLASS[TIER[m]], NAME[m]) for m in ms]
        r = corr_ci([p[0] for p in pts], [p[2] for p in pts], pearson)
        x0 = 64 + k * (w + 90)
        c.text(x0, 94, label, "t1", extra='font-weight="600"')
        c.text(x0, 108, f"Pearson r = {r[0]:+.2f} [{r[1]:+.2f}, {r[2]:+.2f}]", "tick t2")
        xy_scatter(c, x0, 120, w, 176, pts, (140, 170), yr, lambda v: f"{v:.0f}", fmt, xticks=3, yticks=yt)
        c.text(x0 + w / 2, 116 + 180 + 30, "ECI (Epoch Capabilities Index)", "tick t3", "middle")
    Path(path).write_text(c.svg())


scatter_fig("replybench/figures/eci.svg",
            [("Email · AUC", "email", "auc", (0.7, 1.0), lambda v: f"{v:.1f}", 3),
             ("PR · AUC", "pr", "auc", (0.6, 0.9), lambda v: f"{v:.1f}", 3),
             ("HN · AUC", "hn", "auc", (0.4, 1.0), lambda v: f"{v:.1f}", 3)],
            "ReplyBench vs. general capability", "Ranking skill (AUC) against ECI; whiskers are 95% CIs on both axes")
scatter_fig("rolloutbench/figures/eci.svg",
            [("Questions · Brier skill", "rollq", "skill", (0.2, 0.6), lambda v: f"{v:.1f}", 4),
             ("Judge score (0–10)", "rollout", "score", (2, 6), lambda v: f"{v:.0f}", 4)],
            "RolloutBench vs. general capability", "Real-trace scores against ECI; whiskers are 95% CIs on both axes")
