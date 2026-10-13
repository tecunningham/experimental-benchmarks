"""Tiny dependency-free SVG chart helpers, so every figure in the repo shares one look.

Colours come from a validated categorical palette (light + dark steps); text never wears series colour.
Models always keep the same colour: Haiku = slot 1, Sonnet = slot 2, Opus = slot 3.
"""
import math

STYLE = """<style>
.bg{fill:#fcfcfb}.t1{fill:#0b0b0b}.t2{fill:#52514e}.t3{fill:#8a8984}.grid{stroke:#e4e3df}
.s1{fill:#2a78d6}.s2{fill:#eb6834}.s3{fill:#1baf7a}.neutral{fill:#b9b8b2}.ref{stroke:#52514e}.ci{stroke:#0b0b0b;stroke-width:1.5;fill:none}
.line-s1{stroke:#2a78d6}.line-s2{stroke:#eb6834}.line-s3{stroke:#1baf7a}
.d1{fill:#2a78d6;stroke:#fcfcfb}.d2{fill:#eb6834;stroke:#fcfcfb}.d3{fill:#1baf7a;stroke:#fcfcfb}
@media (prefers-color-scheme: dark){.bg{fill:#1a1a19}.t1{fill:#f0efec}.t2{fill:#c3c2b7}.t3{fill:#8f8e88}
.grid{stroke:#33332f}.s1{fill:#3987e5}.s2{fill:#d95926}.s3{fill:#199e70}.neutral{fill:#5a5954}.ref{stroke:#c3c2b7}.ci{stroke:#f0efec}.line-s1{stroke:#3987e5}.line-s2{stroke:#d95926}.line-s3{stroke:#199e70}
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
        """Horizontal bar from baseline x, length w (negative = leftwards), 4px rounded at the data end."""
        sgn = -1 if w < 0 else 1
        w = max(abs(w), 2)
        r = min(4, w / 2, h / 2)
        sw = 1 if sgn > 0 else 0
        self.add(f'<path class="{cls}" d="M{x:.1f},{y:.1f} h{sgn * (w - r):.1f} a{r},{r} 0 0 {sw} {sgn * r},{r} '
                 f'v{h - 2 * r:.1f} a{r},{r} 0 0 {sw} {-sgn * r},{r} h{-sgn * (w - r):.1f} z"/>')

    def whisker(self, x1, x2, yc, cap=4):
        """95% CI whisker drawn over a bar."""
        self.add(f'<path class="ci" d="M{x1:.1f},{yc:.1f} H{x2:.1f} M{x1:.1f},{yc - cap:.1f} V{yc + cap:.1f} '
                 f'M{x2:.1f},{yc - cap:.1f} V{yc + cap:.1f}"/>')

    def legend(self, x, y, items):
        for name, cls in items:
            self.add(f'<rect class="{cls}" x="{x}" y="{y - 9}" width="10" height="10" rx="2"/>')
            self.text(x + 14, y, name, "t2")
            x += 24 + 7 * len(name)

    def svg(self):
        return "\n".join([f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                          f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">', STYLE,
                          f'<rect class="bg" width="{self.w}" height="{self.h}" rx="8"/>', *self.parts, "</svg>"])


def _axis(c, x0, w, vmin, vmax, top, bottom, fmt, ticks):
    px = lambda v: x0 + w * (min(max(v, vmin), vmax) - vmin) / (vmax - vmin)  # clamp (long whiskers)
    for t in range(ticks + 1):
        v = vmin + (vmax - vmin) * t / ticks
        cls = "ref" if vmin < 0 and abs(v) < 1e-9 else "grid"
        c.add(f'<line class="{cls}" x1="{px(v):.1f}" x2="{px(v):.1f}" y1="{top - 4}" y2="{bottom + 4}"/>')
        c.text(px(v), bottom + 18, fmt(v), "tick t3", "middle")
    return px


def hbars(c, x0, y0, w, rows, vmax, fmt, label_w=84, bh=24, gap=12, ticks=4, ref=None, cis=None, vmin=0):
    """rows: [(label, value, css_class)]; cis: optional [(lo, hi)] 95% intervals. Returns y below the axis."""
    pw = w - label_w - 44
    top, bottom = y0, y0 + len(rows) * (bh + gap) - gap
    px = _axis(c, x0 + label_w, pw, vmin, vmax, top, bottom, fmt, ticks)
    for i, (name, v, cls) in enumerate(rows):
        y = top + i * (bh + gap)
        c.text(x0 + label_w - 8, y + bh / 2 + 4, name, "t2", "end")
        c.bar(px(max(vmin, 0)), y, px(v) - px(max(vmin, 0)), bh, cls)
        lo, hi = (px(cis[i][0]), px(cis[i][1])) if cis and cis[i] else (px(v), px(v))
        if cis and cis[i]:
            c.whisker(lo, hi, y + bh / 2)
        # labels sit right of the bar end / whisker (for negative bars: right of the zero line)
        c.text(max(px(max(v, 0)), hi) + 6, y + bh / 2 + 4, fmt(v), "v t1")
    if ref is not None:
        c.add(f'<line class="ref" stroke-dasharray="3 3" x1="{px(ref):.1f}" x2="{px(ref):.1f}" y1="{top - 8}" y2="{bottom + 4}"/>')
    return bottom + 24


def grouped_hbars(c, x0, y0, w, groups, series, vmax, fmt, label_w=110, bh=9, inner=2, gap=14, ticks=4,
                  cis=None, vmin=0):
    """groups: [(label, [v per series])]; series: [(name, css_class)]; cis: [[(lo, hi) per series] per group]."""
    pw = w - label_w - 40
    k = len(series)
    gh = k * bh + (k - 1) * inner
    bottom = y0 + len(groups) * (gh + gap) - gap
    px = _axis(c, x0 + label_w, pw, vmin, vmax, y0, bottom, fmt, ticks)
    for i, (label, vals) in enumerate(groups):
        y = y0 + i * (gh + gap)
        c.text(x0 + label_w - 8, y + gh / 2 + 4, label, "t2", "end")
        for j, v in enumerate(vals):
            yy = y + j * (bh + inner)
            c.bar(px(max(vmin, 0)), yy, px(v) - px(max(vmin, 0)), bh, series[j][1])
            lo, hi = (px(cis[i][j][0]), px(cis[i][j][1])) if cis and cis[i][j] else (px(v), px(v))
            if cis and cis[i][j]:
                c.whisker(lo, hi, yy + bh / 2, cap=3)
            c.text(max(px(max(v, 0)), hi) + 5, yy + bh - 1, fmt(v), "tick t2")
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


def reliability(c, x0, y0, size, curves, title=None, ticks=(0, 0.25, 0.5, 0.75, 1)):
    """Calibration plot: curves = [(css_class, [(mean_pred, observed_rate, n)])]; y = x is perfect."""
    px = lambda v: x0 + size * v
    py = lambda v: y0 + size - size * v
    if title:
        c.text(x0, y0 - 10, title, "t1", extra='font-weight="600"')
    for t in ticks:
        c.add(f'<line class="grid" x1="{px(t):.1f}" x2="{px(t):.1f}" y1="{y0}" y2="{y0 + size}"/>')
        c.add(f'<line class="grid" x1="{x0}" x2="{x0 + size}" y1="{py(t):.1f}" y2="{py(t):.1f}"/>')
        c.text(px(t), y0 + size + 14, f"{t:g}", "tick t3", "middle")
        c.text(x0 - 6, py(t) + 3, f"{t:g}", "tick t3", "end")
    c.add(f'<line class="ref" stroke-dasharray="3 3" x1="{px(0)}" y1="{py(0)}" x2="{px(1)}" y2="{py(1)}"/>')
    for cls, pts in curves:
        d = " ".join(f"{'M' if i == 0 else 'L'}{px(x):.1f},{py(y):.1f}" for i, (x, y, _) in enumerate(pts))
        c.add(f'<path class="line-{cls}" d="{d}" fill="none" stroke-width="2"/>')
        for x, y, n in pts:
            c.add(f'<circle class="d{cls[-1]}" cx="{px(x):.1f}" cy="{py(y):.1f}" r="{3 + min(n, 60) ** 0.5 / 2:.1f}" stroke-width="2"/>')
