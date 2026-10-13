# Correlation with the Epoch Capabilities Index (ECI)

[← back to the benchmark list](../README.md)

Across the Claude models we tested that have an ECI score (Epoch AI). 95% CIs bootstrap over models, so
with ~13 models they are wide.

| metric | benchmark | models | Pearson r [95% CI] | Spearman ρ [95% CI] |
|---|---|---|---|---|
| Email reply · AUC | ReplyBench | 13 | +0.87 [+0.78, +0.98] | +0.93 [+0.62, +1.00] |
| Email reply · Brier skill | ReplyBench | 13 | +0.85 [+0.55, +0.97] | +0.74 [+0.21, +0.99] |
| PR merge · AUC | ReplyBench | 13 | +0.90 [+0.74, +0.97] | +0.85 [+0.51, +0.99] |
| PR merge · Brier skill | ReplyBench | 13 | +0.31 [-0.35, +0.73] | +0.09 [-0.61, +0.69] |
| HN 50+ points · AUC | ReplyBench | 13 | +0.94 [+0.92, +0.98] | +0.94 [+0.73, +1.00] |
| HN points · Spearman | ReplyBench | 13 | +0.60 [-0.10, +0.90] | +0.51 [-0.15, +0.94] |
| Tool result · question Brier skill | RolloutBench | 13 | +0.93 [+0.86, +0.97] | +0.91 [+0.61, +0.98] |
| Tool result · hard-question skill | RolloutBench | 13 | +0.88 [+0.75, +0.96] | +0.90 [+0.61, +0.99] |
| Tool result · judge score | RolloutBench | 13 | +0.97 [+0.95, +0.99] | +0.98 [+0.90, +1.00] |
| Tool result · outcome right | RolloutBench | 13 | +0.88 [+0.75, +0.96] | +0.84 [+0.50, +0.97] |

ECI source: Epoch AI, [benchmark data](https://epoch.ai/data/benchmark_data.zip) (`eci_scores.csv`), fetched by [`common/fetch_eci.py`](../common/fetch_eci.py).
