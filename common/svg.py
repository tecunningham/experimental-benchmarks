"""Tiny dependency-free SVG chart helpers, so every figure in the repo shares one look.

Colours come from a validated categorical palette (light + dark steps); text never wears series colour.
Models always keep the same colour: Haiku = slot 1, Sonnet = slot 2, Opus = slot 3.
"""
import math

STYLE = """<style>
.bg{fill:#fcfcfb}.t1{fill:#0b0b0b}.t2{fill:#52514e}.t3{fill:#8a8984}.grid{stroke:#e4e3df}
.s1{fill:#2a78d6}.s2{fill:#eb6834}.s3{fill:#1baf7a}.neutral{fill:#b9b8b2}.ref{stroke:#52514e}
.d1{fill:#2a78d6;stroke:#fcfcfb}.d2{fill:#eb6834;stroke:#fcfcfb}.d3{fill:#1baf7a;stroke:#fcfcfb}
@media (prefers-color-scheme: dark){.bg{fill:#1a1a19}.t1{fill:#f0efec}.t2{fill:#c3c2b7}.t3{fill:#8f8e88}
.grid{stroke:#33332f}.s1{fill:#3987e5}.s2{fill:#d95926}.s3{fill:#199e70}.neutral{fill:#5a5954}.ref{stroke:#c3c2b7}
.d1{fill:#3987e5;stroke:#1a1a19}.d2{fill:#d95926;stroke:#1a1a19}.d3{fill:#199e70;stroke:#1a1a19}}
text{font-size:12px}.h{font-size:15px;font-weight:600}.v{font-size:11px;font-weight:600}.tick{font-size:10px}
</style>"""
FONT = "-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"
MODEL_CLASS = {"Haiku 5.5": "s1", "Sonnet 5.5": "s2", "Opus 5.5": "s3"}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Canvas:
    def __init__(self, w, h):
        self.w, self.h, self.parts = w, h, []

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, cls="t2", anchor="start", extra=""):
        self.add(f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" {extra}>{esc(s)}</text>')

    def title(self, x, y, title, sub=None):
        self.text(x, y, title, "h t1")
        if sub:
            self.text(x, y + 18, sub, "t2")

    def bar(self, x, y, w, h, cls):
        """Horizontal bar, 4px rounded at the data end, square at the baseline."""
        w = max(w, 2)
        r = min(4, w / 2, h / 2)
        self.add(f'<path class="{cls}" d="M{x:.1f},{y:.1f} h{w - r:.1f} a{r},{r} 0 0 1 {r},{r} v{h - 2 * r:.1f} '
                 f'a{r},{r} 0 0 1 -{r},{r} h{-(w - r):.1f} z"/>')

    def legend(self, x, y, items):
        for name, cls in items:
            self.add(f'<rect class="{cls}" x="{x}" y="{y - 9}" width="10" height="10" rx="2"/>')
            self.text(x + 14, y, name, "t2")
            x += 24 + 7 * len(name)

    def svg(self):
        return "\n".join([f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                          f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">', STYLE,
                          f'<rect class="bg" width="{self.w}" height="{self.h}" rx="8"/>', *self.parts, "</svg>"])


def hbars(c, x0, y0, w, rows, vmax, fmt, label_w=84, bh=24, gap=12, ticks=4, ref=None):
    """rows: [(label, value, css_class)]. Returns the y just below the axis."""
    pw = w - label_w - 44
    top, bottom = y0, y0 + len(rows) * (bh + gap) - gap
    for t in range(ticks + 1):
        gx = x0 + label_w + pw * t / ticks
        c.add(f'<line class="grid" x1="{gx:.1f}" x2="{gx:.1f}" y1="{top - 4}" y2="{bottom + 4}"/>')
        c.text(gx, bottom + 18, fmt(vmax * t / ticks), "tick t3", "middle")
    for i, (name, v, cls) in enumerate(rows):
        y = top + i * (bh + gap)
        bw = pw * v / vmax
        c.text(x0 + label_w - 8, y + bh / 2 + 4, name, "t2", "end")
        c.bar(x0 + label_w, y, bw, bh, cls)
        c.text(x0 + label_w + bw + 6, y + bh / 2 + 4, fmt(v), "v t1")
    if ref is not None:
        rx = x0 + label_w + pw * ref / vmax
        c.add(f'<line class="ref" stroke-dasharray="3 3" x1="{rx:.1f}" x2="{rx:.1f}" y1="{top - 8}" y2="{bottom + 4}"/>')
    return bottom + 24


def grouped_hbars(c, x0, y0, w, groups, series, vmax, fmt, label_w=110, bh=9, inner=2, gap=14, ticks=4):
    """groups: [(label, [v_series0, v_series1, ...])]; series: [(name, css_class)]."""
    pw = w - label_w - 40
    k = len(series)
    gh = k * bh + (k - 1) * inner
    bottom = y0 + len(groups) * (gh + gap) - gap
    for t in range(ticks + 1):
        gx = x0 + label_w + pw * t / ticks
        c.add(f'<line class="grid" x1="{gx:.1f}" x2="{gx:.1f}" y1="{y0 - 4}" y2="{bottom + 4}"/>')
        c.text(gx, bottom + 18, fmt(vmax * t / ticks), "tick t3", "middle")
    for i, (label, vals) in enumerate(groups):
        y = y0 + i * (gh + gap)
        c.text(x0 + label_w - 8, y + gh / 2 + 4, label, "t2", "end")
        for j, v in enumerate(vals):
            yy = y + j * (bh + inner)
            bw = pw * v / vmax
            c.bar(x0 + label_w, yy, bw, bh, series[j][1])
            c.text(x0 + label_w + bw + 5, yy + bh - 1, fmt(v), "tick t2")
    return bottom + 24


def log_scatter(c, x0, y0, size, pts, cls, lo=1, hi=1000, title=None):
    """Square log-log scatter of (x, y) points with a y = x reference line."""
    L = lambda v: math.log10(max(min(v, hi), lo))
    span = math.log10(hi) - math.log10(lo)
    px = lambda v: x0 + size * (L(v) - math.log10(lo)) / span
    py = lambda v: y0 + size - size * (L(v) - math.log10(lo)) / span
    if title:
        c.text(x0, y0 - 10, title, "t1", extra='font-weight="600"')
    t = lo
    while t <= hi:
        c.add(f'<line class="grid" x1="{px(t):.1f}" x2="{px(t):.1f}" y1="{y0}" y2="{y0 + size}"/>')
        c.add(f'<line class="grid" x1="{x0}" x2="{x0 + size}" y1="{py(t):.1f}" y2="{py(t):.1f}"/>')
        c.text(px(t), y0 + size + 14, f"{t:g}", "tick t3", "middle")
        c.text(x0 - 6, py(t) + 3, f"{t:g}", "tick t3", "end")
        t *= 10
    c.add(f'<line class="ref" stroke-dasharray="3 3" x1="{px(lo):.1f}" y1="{py(lo):.1f}" x2="{px(hi):.1f}" y2="{py(hi):.1f}"/>')
    for x, y in pts:
        c.add(f'<circle class="{cls}" cx="{px(x):.1f}" cy="{py(y):.1f}" r="4" fill-opacity="0.55" stroke-width="1"/>')
