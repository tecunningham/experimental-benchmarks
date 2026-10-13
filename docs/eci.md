# Correlation with the Epoch Capabilities Index (ECI)

[← back to the benchmark list](../README.md)

Across the Claude models we tested that have an ECI score (Epoch AI). 95% CIs bootstrap over models, so
with ~13 models they are wide.

| metric | benchmark | models | Pearson r [95% CI] | Spearman ρ [95% CI] |
|---|---|---|---|---|
| Email reply · AUC | ReplyBench | 3 | +0.99 [+0.00, +1.00] | +1.00 [+0.00, +1.00] |
| Email reply · Brier skill | ReplyBench | 3 | +0.55 [-1.00, +1.00] | +0.50 [-1.00, +1.00] |
| PR merge · AUC | ReplyBench | 4 | +0.38 [-1.00, +1.00] | +0.00 [-1.00, +1.00] |
| PR merge · Brier skill | ReplyBench | 4 | -0.10 [-1.00, +1.00] | -0.80 [-1.00, +1.00] |
| HN 50+ points · AUC | ReplyBench | 5 | +0.94 [+0.54, +1.00] | +0.80 [+0.11, +1.00] |
| HN points · Spearman | ReplyBench | 5 | +0.08 [-1.00, +1.00] | +0.50 [-1.00, +1.00] |
| Tool result · judge score | RolloutBench | 2 | +1.00 [+0.00, +1.00] | +1.00 [+0.00, +1.00] |
| Tool result · outcome right | RolloutBench | 2 | +1.00 [+0.00, +1.00] | +1.00 [+0.00, +1.00] |

ECI source: Epoch AI, [benchmark data](https://epoch.ai/data/benchmark_data.zip) (`eci_scores.csv`), fetched by [`common/fetch_eci.py`](../common/fetch_eci.py).
