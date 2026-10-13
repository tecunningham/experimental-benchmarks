ReplyBench-pr: n=234, base rate 0.65

| predictor | AUC [95% CI] | Brier [95% CI] | Brier skill vs base rate [95% CI] |
|---|---|---|---|
| baseline: overall base rate | – | 0.228 [0.210, 0.246] | +0.00 [-0.02, +0.00] |
| baseline: project merge rate (leave-one-out) | 0.70 [0.63, 0.77] | 0.202 [0.176, 0.227] | +0.11 [+0.01, +0.21] |
| claude-haiku-5-5 | 0.77 [0.70, 0.83] | 0.221 [0.199, 0.244] | +0.03 [-0.14, +0.16] |
| claude-opus-5-5 | 0.79 [0.73, 0.85] | 0.203 [0.179, 0.228] | +0.11 [-0.06, +0.23] |
| claude-sonnet-5-5 | 0.76 [0.69, 0.82] | 0.195 [0.171, 0.220] | +0.14 [+0.00, +0.26] |
