"""Models evaluated across benchmarks: id, display name, tier. Tier picks the chart colour (fixed order).

ECI = Epoch Capabilities Index (Epoch AI, benchmark_data.zip, eci_scores.csv); None where Epoch has no score.
"""
MODELS = [
    ("claude-haiku-4-5", "Haiku 4.5", "Haiku"),
    ("claude-haiku-5-5", "Haiku 5.5", "Haiku"),
    ("claude-sonnet-4-5", "Sonnet 4.5", "Sonnet"),
    ("claude-sonnet-4-6", "Sonnet 4.6", "Sonnet"),
    ("claude-sonnet-5", "Sonnet 5", "Sonnet"),
    ("claude-sonnet-5-5", "Sonnet 5.5", "Sonnet"),
    ("claude-opus-4-5", "Opus 4.5", "Opus"),
    ("claude-opus-4-6", "Opus 4.6", "Opus"),
    ("claude-opus-4-7", "Opus 4.7", "Opus"),
    ("claude-opus-4-8", "Opus 4.8", "Opus"),
    ("claude-opus-5", "Opus 5", "Opus"),
    ("claude-opus-5-5", "Opus 5.5", "Opus"),
    ("claude-fable-5", "Fable 5", "Fable"),
    ("claude-fable-5-1", "Fable 5.1", "Fable"),
]
TIERS = ["Haiku", "Sonnet", "Opus", "Fable"]
NAME = {m: n for m, n, _ in MODELS}
TIER = {m: t for m, _, t in MODELS}
