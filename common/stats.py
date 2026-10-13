import math


def ranks(x):
    order = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def pearson(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sxy / (sx * sy) if sx and sy else 0.0


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def auc(scores, labels):
    pos = [s for s, l in zip(scores, labels) if l]
    neg = [s for s, l in zip(scores, labels) if not l]
    if not pos or not neg:
        return float("nan")
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def bootstrap_ci(metric, n, B=2000, seed=0, alpha=0.05):
    """Percentile bootstrap CI for metric(idx) over n items resampled with replacement."""
    import random
    rng = random.Random(seed)
    vals = sorted(metric([rng.randrange(n) for _ in range(n)]) for _ in range(B))
    vals = [v for v in vals if v == v]  # drop NaN (e.g. AUC on a one-class resample)
    return vals[int(alpha / 2 * len(vals))], vals[int((1 - alpha / 2) * len(vals)) - 1]


def mean_ci(xs, B=2000, seed=0):
    m = sum(xs) / len(xs)
    lo, hi = bootstrap_ci(lambda idx: sum(xs[i] for i in idx) / len(idx), len(xs), B, seed)
    return m, lo, hi
