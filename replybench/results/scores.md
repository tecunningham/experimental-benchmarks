n=200 stories, 12 reached >=50 points (base rate 0.060)

| model | spearman_points | spearman_comments | mae_log_points | brier_p50 | auc_p50 |
|---|---|---|---|---|---|
| baseline: constant median / base rate | 0.0 | 0.0 | 0.626 | 0.0564 | 0.5 |
| claude-haiku-5-5 | 0.274 | 0.186 | 1.278 | 0.0718 | 0.742 |
| claude-opus-5-5 | 0.363 | 0.288 | 1.113 | 0.0594 | 0.82 |
| claude-sonnet-5-5 | 0.321 | 0.218 | 1.32 | 0.0751 | 0.807 |
