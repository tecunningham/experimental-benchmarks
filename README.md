# Experimental benchmarks

Prototype benchmarks for one question: **can a model predict the consequences of its actions?**

Evals of whether a model can *achieve* real-world outcomes (exfiltrate, persuade, make money) are expensive
and dangerous to run. But to act well, a model has to know what its actions will do. So predicting
consequences is a cheap, safe and hard-to-saturate proxy.

Each benchmark here is scored instantly against data the model hasn't seen, uses continuous metrics, and costs
a few dollars per model to run.

| Benchmark | Question | Prototype data | Headline result | |
|---|---|---|---|---|
| **[ReplyBench](replybench/)** | How will *people* respond to an action? | 191 Apache mailing-list threads, 234 GitLab merge requests, 200 Hacker News posts, all after the training cutoff | Reply prediction is strong (AUC 0.84–0.88); merge prediction only slightly beats a per-project prior; HN calibration is poor | [Landing page →](replybench/) |
| **[RolloutBench](rolloutbench/)** | What will a *tool call* return? | 249 tool calls from 75 real-world agent sessions | Best model scores 5.3/10; live web and API results are hardest | [Landing page →](rolloutbench/) |

---

## [ReplyBench](replybench/): predicting how people respond

Show a model an action and ask it to predict the response. Three tasks: will anyone reply to this email
thread? Will this merge request be merged within 30 days? How many points will this HN post get?

<a href="replybench/"><img src="replybench/figures/headline.svg" alt="ReplyBench: AUC and Brier skill with 95% CIs across email, PR and HN tasks" width="100%"></a>

- **Replies are predictable, merges less so.** Reply prediction is strong (AUC 0.84–0.88, well ahead of the
  base rate). Merge prediction (AUC 0.76–0.79) beats a per-project merge-rate prior on ranking, but only
  slightly on calibration.
- **Calibration flips with the setting.** On HN the models are over-confident; on email and MRs they're
  under-confident.
- **Next step:** 1,000+ items per task, and private data (METR's own PRs, email, Slack).

## [RolloutBench](rolloutbench/): predicting what tools return

Take a trace from a real agent session and hide each tool result: shell output, web pages, API responses,
GPU job logs, sub-agent reports, human replies. The model, which has no internet, predicts each one.

<a href="rolloutbench/"><img src="rolloutbench/figures/headline.svg" alt="RolloutBench results: judge score 3.2 / 4.4 / 5.3 out of 10 for Haiku / Sonnet / Opus" width="100%"></a>

- **Far from saturated and well spread:** Haiku 3.2, Sonnet 4.4, Opus 5.3 out of 10. Basic outcomes are
  right 65–80% of the time, but details much less often.
- **Real-world traces are the point.** In a sandbox pilot, code outputs were nearly solved. Unlike
  AgentWorldBench (Qwen, 2026), which uses benchmark-task trajectories, these traces come from real use.

---

## Shared design

- **Unseen ground truth.** Data comes from after the training cutoff, or is private, so nothing has to
  resolve in the future, unlike forecasting benchmarks. See the
  [comparison with FutureSim, ForecastBench, PredictionArena and AgentWorldBench](docs/comparison.md).
- **Continuous scores with uncertainty.** Rank correlations, Brier scores and judge scores rather than
  pass/fail, so improvements show up smoothly. Every model comparison has a 95% bootstrap CI.
- **No tools for the predictor.** Models predict from context alone. [`common/llm.py`](common/llm.py) calls
  the Anthropic API when `ANTHROPIC_API_KEY` is set, and otherwise uses the `claude` CLI with tools disabled.
- **One look for all charts.** [`common/svg.py`](common/svg.py) renders dependency-free SVG figures that work
  in light and dark mode.

## Layout

```
common/          model interface, stats, SVG chart helpers
docs/            comparison with existing prediction benchmarks
replybench/      README (landing page), email/ pr/ hn/ tasks, run_binary.py, score_binary.py, make_figures.py
rolloutbench/    README (landing page), real/ (real-world traces), sandbox pilot, make_figures.py, figures/
```

A new benchmark gets its own folder with a README landing page, a `run.py` and `score.py`, and a
`make_figures.py` that writes to its `figures/` folder.
