"""Render figures/headline.svg from the scored results (no plotting deps)."""
import difflib
import json
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.stats import auc

MODELS = [("claude-haiku-5-5", "Haiku 5.5"), ("claude-sonnet-5-5", "Sonnet 5.5"), ("claude-opus-5-5", "Opus 5.5")]

# --- ReplyBench numbers
truth = {s["id"]: s for s in map(json.loads, open("replybench/data/hn_stories.jsonl"))}
ids = list(truth)
hit = [truth[i]["score"] >= 50 for i in ids]
base = sum(hit) / len(hit)
rb = [("Base rate", 0.5, statistics.mean((base - h) ** 2 for h in hit))]
for f, name in MODELS:
    pr = {int(p["id"]): p for p in map(json.loads, open(f"replybench/results/{f}.jsonl"))}
    p50 = [min(max(float(pr[i]["p50"]), 0), 1) for i in ids]
    rb.append((name, auc(p50, hit), statistics.mean((p - h) ** 2 for p, h in zip(p50, hit))))

# --- RolloutBench numbers: similarity on non-trivial steps, split by what the output depends on
EMPTY = "(Bash completed with no output)"
MACHINE = {"sysinfo", "pystdlib"}  # outputs depend on this machine's state, not just the code
traces = [json.loads(l) for l in open("rolloutbench/data/traces.jsonl")]
truth_bb = {(t["task_id"], k): s["output"] for t in traces for k, s in enumerate(t["steps"])}
sim = lambda a, b: difflib.SequenceMatcher(None, a.strip()[:3000], b.strip()[:3000], autojunk=False).ratio()
bb = []
for f, name in MODELS:
    pr = {(p["task_id"], p["step"]): p["prediction"] for p in map(json.loads, open(f"rolloutbench/results/{f}.jsonl"))}
    groups = {"code": [], "machine": []}
    for k, v in truth_bb.items():
        if v.strip() != EMPTY:
            groups["machine" if k[0] in MACHINE else "code"].append(sim(pr[k], v))
    bb.append((name, statistics.mean(groups["code"]), statistics.mean(groups["machine"])))
n_code = sum(1 for k, v in truth_bb.items() if v.strip() != EMPTY and k[0] not in MACHINE)
n_mach = sum(1 for k, v in truth_bb.items() if v.strip() != EMPTY and k[0] in MACHINE)

# --- SVG
W, H = 960, 284
out = []
a = out.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">')
a("""<style>
.bg{fill:#fcfcfb}.t1{fill:#0b0b0b}.t2{fill:#52514e}.t3{fill:#8a8984}.grid{stroke:#e4e3df}.axis{stroke:#b9b8b2}
.s1{fill:#2a78d6}.s2{fill:#eb6834}.neutral{fill:#b9b8b2}.ref{stroke:#52514e}
@media (prefers-color-scheme: dark){.bg{fill:#1a1a19}.t1{fill:#f0efec}.t2{fill:#c3c2b7}.t3{fill:#8f8e88}
.grid{stroke:#33332f}.axis{stroke:#5a5954}.s1{fill:#3987e5}.s2{fill:#d95926}.neutral{fill:#5a5954}.ref{stroke:#c3c2b7}}
text{font-size:12px}.h{font-size:15px;font-weight:600}.sub{font-size:12px}.v{font-size:11px;font-weight:600}
</style>""")
a(f'<rect class="bg" width="{W}" height="{H}" rx="8"/>')


def hbars(x0, y0, w, title, sub, rows, vmax, fmt, note=None, ref=None):
    a(f'<text class="h t1" x="{x0}" y="{y0}">{title}</text>')
    a(f'<text class="sub t2" x="{x0}" y="{y0 + 18}">{sub}</text>')
    lab, top, bh, gap = 78, y0 + 44, 26, 12
    pw = w - lab - 40
    for t in range(0, 5):
        gx = x0 + lab + pw * t / 4
        a(f'<line class="grid" x1="{gx:.1f}" x2="{gx:.1f}" y1="{top - 4}" y2="{top + len(rows) * (bh + gap) - gap + 4}"/>')
        a(f'<text class="t3" x="{gx:.1f}" y="{top + len(rows) * (bh + gap) + 12}" text-anchor="middle" font-size="10">{fmt(vmax * t / 4)}</text>')
    for i, (name, v, cls) in enumerate(rows):
        y = top + i * (bh + gap)
        bw = max(pw * v / vmax, 2)
        a(f'<text class="t2" x="{x0 + lab - 8}" y="{y + bh / 2 + 4}" text-anchor="end">{name}</text>')
        a(f'<path class="{cls}" d="M{x0 + lab},{y} h{bw - 4:.1f} a4,4 0 0 1 4,4 v{bh - 8} a4,4 0 0 1 -4,4 h{-(bw - 4):.1f} z"/>')
        a(f'<text class="v t1" x="{x0 + lab + bw + 6:.1f}" y="{y + bh / 2 + 4}">{fmt(v)}</text>')
    if ref is not None:
        rx = x0 + lab + pw * ref / vmax
        a(f'<line class="ref" stroke-dasharray="3 3" x1="{rx:.1f}" x2="{rx:.1f}" y1="{top - 8}" y2="{top + len(rows) * (bh + gap) - gap + 4}"/>')
    if note:
        a(f'<text class="t2" x="{x0}" y="{H - 22}" font-size="11">{note}</text>')


hbars(24, 34, 290, "ReplyBench · ranking", "AUC for “will this HN story hit 50 pts?”",
      [(n, v, "neutral" if n == "Base rate" else "s1") for n, v, _ in rb], 1.0, lambda v: f"{v:.2f}",
      note="Higher is better · 200 stories, Oct 2026")
hbars(334, 34, 290, "ReplyBench · calibration", "Brier score for the same question",
      [(n, b, "neutral" if n == "Base rate" else "s1") for n, _, b in rb], 0.08, lambda v: f"{v:.3f}",
      note="Lower is better · all models lose to the base rate", ref=rb[0][2])

# grouped bars for RolloutBench
x0, y0, w = 644, 34, 300
a(f'<text class="h t1" x="{x0}" y="{y0}">RolloutBench · predict tool output</text>')
a(f'<text class="sub t2" x="{x0}" y="{y0 + 18}">Similarity of predicted vs. real output</text>')
lab, top, bh, gap = 78, y0 + 44, 12, 14
pw = w - lab - 44
for t in range(0, 5):
    gx = x0 + lab + pw * t / 4
    a(f'<line class="grid" x1="{gx:.1f}" x2="{gx:.1f}" y1="{top - 4}" y2="{top + 3 * (2 * bh + 2 + gap) - gap + 4}"/>')
    a(f'<text class="t3" x="{gx:.1f}" y="{top + 3 * (2 * bh + 2 + gap) + 12}" text-anchor="middle" font-size="10">{t / 4:.2f}</text>')
for i, (name, c, m) in enumerate(bb):
    y = top + i * (2 * bh + 2 + gap)
    a(f'<text class="t2" x="{x0 + lab - 8}" y="{y + bh + 4}" text-anchor="end">{name}</text>')
    for j, (v, cls) in enumerate([(c, "s1"), (m, "s2")]):
        yy = y + j * (bh + 2)
        bw = pw * v
        a(f'<path class="{cls}" d="M{x0 + lab},{yy} h{bw - 4:.1f} a4,4 0 0 1 4,4 v{bh - 8} a4,4 0 0 1 -4,4 h{-(bw - 4):.1f} z"/>')
        a(f'<text class="v t1" x="{x0 + lab + bw + 6:.1f}" y="{yy + bh - 2}">{v:.2f}</text>')
ly = top + 3 * (2 * bh + 2 + gap) + 30
a(f'<rect class="s1" x="{x0}" y="{ly - 9}" width="10" height="10" rx="2"/><text class="t2" x="{x0 + 14}" y="{ly}" font-size="11">Output follows from the code ({n_code} calls)</text>')
a(f'<rect class="s2" x="{x0}" y="{ly + 7}" width="10" height="10" rx="2"/><text class="t2" x="{x0 + 14}" y="{ly + 16}" font-size="11">Output depends on machine state ({n_mach} calls)</text>')
a("</svg>")
Path("figures/headline.svg").write_text("\n".join(out))
print("rb", rb, "\nbb", bb, n_code, n_mach)
