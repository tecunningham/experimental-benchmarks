# Can models predict what their actions will do?

**Two prototype benchmarks that score a model on predicting the *consequences of actions*, not world events.**
Both are scored instantly from data the model has never seen, use continuous metrics, and cost under $1 per
model to run.

> Evals of whether a model can *achieve* real-world outcomes (exfiltrate, cause harm, make money) are expensive
> and dangerous. To act well, a model has to know what its actions will do, so prediction is a cheap, safe and
> unsaturatable proxy.

<p align="center"><img src="figures/headline.svg" alt="Results: ReplyBench AUC 0.74–0.82 but worse-than-base-rate Brier; RolloutBench on real-world traces, judge score 3.2 / 4.4 / 5.3 out of 10 for Haiku / Sonnet / Opus" width="100%"></p>

## Takeaways

1. **Models know what Hacker News likes, but not how little it cares.** Opus 5.5 picks out stories that will
   reach 50 points with AUC 0.82, yet every model is *worse calibrated than a constant base rate*. A typical
   submission gets 2 points; the models expect far more.
2. **On real-world agent traces, predicting tool results is far from solved.** On 249 tool calls from real
   sessions (a person's workstation, an ML agent launching GPU jobs), a blind judge scores the models' predicted
   results at 3.2 (Haiku), 4.4 (Sonnet) and 5.3 (Opus) out of 10. Opus gets the basic outcome right 78% of the
   time, but the details much less often.
3. **Synthetic traces are too easy, so real ones matter.** In a sandbox pilot, models reproduced outputs that
   follow from code almost perfectly (similarity ≈ 0.9). The headroom is in results that depend on the state of
   the world: API responses, web content, job status. That is also the key difference from AgentWorldBench
   (Qwen, 2026), which uses benchmark-task trajectories.
4. **Unlike existing forecasting benchmarks, nothing has to resolve.** FutureSim, ForecastBench and
   PredictionArena predict world events, so they wait months or go stale. Here the ground truth already exists
   in held-out data, so a run is scored immediately.

## The two benchmarks

| | **ReplyBench** | **RolloutBench** |
|---|---|---|
| Question | *How will people respond to this action?* | *What will this tool call return?* |
| Idea | Predict how a person or system responds to an input (an email, a PR, a post, a paper) | Take a trace from a real model run and predict the result of every tool call (shell, web fetch, GPU run, API call, email, sub-agent), with no internet |
| Prototype | Hacker News submissions after the training cutoff: predict points, comments, P(≥50 points) | 249 tool calls (shell, web, APIs, GPU jobs, sub-agents, human replies) from 75 public real-world sessions, Jun–Sep 2026 |
| Example | “Cops Can Bypass iPhone's Automatic Reboot…” (404media) → Opus 5.5 predicted 150 points, actual **293**. “Official Proton Drive CLI” → predicted 120, actual **1**. | `hf_jobs ps` → Opus 5.5 predicted one running job; actual: **"No running jobs found"** (judge score 0/10) |
| Size | 200 stories, 3 models | 249 tool calls, 3 models, blind LLM judge (plus a 76-call sandbox pilot) |
| More | [`replybench/`](replybench/) | **[RolloutBench page →](rolloutbench/README.md)** |

| | FutureSim | ForecastBench | PredictionArena | AgentWorldBench | **ReplyBench** | **RolloutBench** |
|---|---|---|---|---|---|---|
| Predicts | World events | World events | World events, through trading | Next observation in agent trajectories | Response to an action | Result of an agent's tool call |
| Data | News replay | Markets and data series | Live markets | Benchmark tasks in sandboxes | Real HN posts | **Real-world agent sessions** |
| Time to score | 0, but goes stale | Weeks to years | Days to weeks | Instant | Instant | Instant |
| Cost per run | $50–2,000 | Low | $10k at risk | Low | <$1 | ~$5–10 |

## Next steps to make this real

The prototypes show that the pipelines work and that the scores spread across models. To become a benchmark
people trust, each one needs three things: **data nobody has seen**, **an outcome that is the consequence of
an action**, and **a known noise ceiling**.

### ReplyBench

1. **Use private data.** This is the biggest lever. METR's own records are contamination-proof by
   construction:
   - GitHub PRs: merged? how many review rounds? time to merge?
   - Slack and email: does it get a reply, how fast, what reaction?
   - Issue trackers: does the bug get fixed?

   Partner datasets would do the same at scale: support tickets, sales outreach, ad campaigns.
2. **Get causal data.** A/B-test archives answer the observational-not-causal objection. The task becomes
   "which of these two variants won?", with the audience held fixed. The Upworthy Research Archive (32k
   headline tests) is a public development set; fresh, private A/B results from partner companies would be
   the held-out test set.
3. **Add more public streams with a monthly refresh**, so the benchmark is always past the training cutoff:
   - Hacker News, Reddit, and GitHub PR outcomes in public repos.
   - OpenReview scores (ICLR reviews land each November).
   - Kickstarter funding, Stack Overflow accepted answers.
4. **Measure the noise ceiling.** HN reposts of the same URL give a natural test-retest measurement of how
   predictable an outcome can be at all. Report scores as a fraction of that ceiling.
5. **Score full predictive distributions** (quantiles, then log score). Report discrimination and calibration
   separately, and let models see the empirical distribution so that calibration isn't the whole story.
6. **Plot compute against score.** Give an agent an offline corpus (the author's history, similar past
   posts) and a thinking budget, and plot spend vs. score, as the design doc recommends.

### RolloutBench

The real-trace test works. The next steps are scale and breadth: more public sessions refreshed monthly,
private staff and METR agent sessions (contamination-proof), more human replies and lab experiments, scoring of
key facts with a judge from another model family, a noise ceiling, and a check that scores predict real agentic
success. Details are in the [RolloutBench page](rolloutbench/README.md#next-steps), along with
[related work](rolloutbench/README.md#related-work) (AgentWorldBench, ToolEmu, WebDreamer, CRUXEval, …).

### Shared

- Port to [Inspect](https://inspect.aisi.org.uk/) and run non-Claude models (GPT, Gemini, open weights).
- Keep a public dev split and a private, rotating test split.
- Grow ReplyBench to ≥2k items and RolloutBench to ≥1k steps, so that model differences fall outside the noise
  (the current error bar on Spearman ρ is about ±0.07).

---

## Running

```bash
pip install anthropic                     # optional: used if ANTHROPIC_API_KEY is set, else the `claude` CLI
# ReplyBench
python3 replybench/fetch_hn.py --start 2026-10-01 --end 2026-10-06 --n 200
python3 replybench/run.py --model claude-opus-5-5
python3 replybench/score.py
# RolloutBench on real-world traces (see rolloutbench/README.md for the sandbox pilot)
python3 rolloutbench/real/build.py
python3 rolloutbench/real/run.py --model claude-opus-5-5
python3 rolloutbench/real/judge.py
python3 rolloutbench/real/score.py
```

`common/llm.py` is the only model interface. Outside the Anthropic API path, it runs `claude -p` with no
tools, no settings, and an empty working directory.

## ReplyBench-HN

**Data.** 200 stories drawn uniformly at random from all 4,687 HN submissions between 1 and 6 Oct 2026. That
window is after the models' training cutoff. Ground truth comes from the official Firebase API on 12 Oct, so
every story is at least 6 days old and its score has settled. The scores are heavy-tailed: median 2, 90th
percentile 12, and 12 of the 200 stories (6%) reached 50 or more points.

**Protocol.** Each model call covers 25 stories, so a run of one model takes 8 calls. The prompt says the
sample is uniform over all submissions.

| model | Spearman (points) | Spearman (comments) | MAE log(1+points) | Brier P(≥50) | AUC P(≥50) |
|---|---|---|---|---|---|
| baseline: constant median / base rate | 0 | 0 | 0.626 | 0.0564 | 0.5 |
| claude-haiku-5-5 | 0.274 | 0.186 | 1.278 | 0.0718 | 0.742 |
| claude-sonnet-5-5 | 0.321 | 0.218 | 1.320 | 0.0751 | 0.807 |
| claude-opus-5-5 | **0.363** | **0.288** | 1.113 | 0.0594 | **0.820** |

**Reading.**
- **Ranking.** All three models rank stories well above chance, and Opus does best. Its AUC of 0.82 means it
  picks out the stories that later hit 50 points fairly well.
- **Calibration.** All three are badly calibrated. On log-MAE and Brier every model is *worse* than a
  constant baseline, because each one predicts that a typical story gets far more points than it does, even
  though the prompt states the base rate.
- **Discrimination vs calibration.** This is the "on-distribution vs. off-distribution" concern from the
  proposal in a concrete form: the models have a good sense of what HN likes, but not of how little attention
  a typical submission gets.
- **Next step.** A calibration step (e.g. isotonic regression on a held-out split), or telling the model the
  empirical distribution, would separate the two skills.

## Full comparison with existing prediction benchmarks

|  | **FutureSim** (Goel et al. 2026) | **ForecastBench** (Karger et al.) | **PredictionArena** (Zhang et al. 2026) | **AgentWorldBench** (Zuo et al. 2026) | **ReplyBench-HN** (this repo) | **RolloutBench** (this repo) |
|---|---|---|---|---|---|---|
| What is predicted | Short-answer questions about world events. An agent replays the news day by day (24 Dec 2025 – Mar 2026) and updates its forecasts. | Binary probabilities on future events: market questions plus questions generated from time-series data (FRED, ACLED, Wikipedia, …) | Nothing stated explicitly. Agents trade Kalshi and Polymarket markets with real money ($10k each). | The next environment observation given an agent's action/observation history (MCP, search, terminal, SWE, Android, web, OS) | Community response to a post: points, comments, P(≥50 points) | The result of each tool call in a real agent session: shell, web, APIs, GPU jobs, sub-agents, human replies |
| Source of ground truth | 330 questions generated from Al Jazeera articles in CCNews | Market resolutions and data releases | Market settlements | 2,170 observations from frontier agents running benchmark tasks (Terminal-Bench, OSWorld, …) in sandboxes | HN API | 249 recorded results from 75 public real-world sessions (Jun–Sep 2026) |
| Effects of *own actions*? | No (world events) | No (world events) | Partly: P&L depends on the agent's trades, but it is predicting the world | Yes, in benchmark environments | Yes in kind: the effect of an action (posting) on people | Yes: the effect of the agent's own actions in the real world |
| Delay before scoring | None when evaluated, but it goes stale once models are trained past Mar 2026 | Weeks to years (horizons from 7 days to 10 years) | Days to weeks (study ran 57 days) | Instant | About a week of data collection, then instant | Instant (traces are recorded once) |
| Contamination control | Window after training cutoff, plus a date-gated search corpus in a sandbox | Fully live (only unresolved questions) | Fully live | Static release of recorded trajectories | Window after training cutoff; refresh by pulling new weeks | Sessions after the training cutoff; refresh with new public or private sessions |
| Scoring | Top-1 accuracy, Brier skill score | Brier score, now a difficulty-adjusted "Brier Index" | Return, settlement win rate | LLM judge on 5 dimensions, 0–100 | Spearman, log-MAE, Brier, AUC (continuous) | Blind LLM judge 0–10, outcome accuracy, string similarity |
| Cost per model run | High: an agentic multi-month replay, roughly $50–2,000 | Low (plain LLM calls), but you wait for resolution | High: real capital at risk plus agent compute | Low (one call per sample) | Very low: 8 calls | Low: 249 calls plus judging |
| Headline result | Best: GPT-5.5 in Codex, ~25% accuracy. Open models have negative Brier skill score. | Top AI systems are roughly at superforecaster parity (FRI, Jul 2026); disputed on market questions | Every model in the main cohort lost money on Kalshi (−16% to −31%) | Frontier models tightly clustered at ~54–59 | Opus ρ = 0.36, AUC 0.82, but worse calibrated than a constant | Opus 5.3, Sonnet 4.4, Haiku 3.2 out of 10; outcome right 78% for Opus |
| Saturation risk | Medium (accuracy ~25%) | Near-saturated relative to the human reference | Noisy, so hard to tell | Clustered scores suggest limited spread | Low: irreducible noise caps achievable ρ well below 1 | Low: real-world state is hard to predict, and scores are well spread |

**Takeaways.**
- **Prediction target.** The three forecasting benchmarks predict *world events*. ReplyBench and RolloutBench
  instead predict the *consequences of a specific action*, which is the capability that matters for an agent
  pursuing goals.
- **Scoring delay.** The existing benchmarks have to wait for the world to resolve (ForecastBench,
  PredictionArena) or go stale (FutureSim). Both prototypes here are scored at once, because the ground truth
  already exists in a dataset nobody has seen.
- **What that buys.** Benchmark runs are cheap and repeatable.
- **What it costs.**
  - The private dataset has to stay private and fresh.
  - For ReplyBench, the setup is observational rather than causal.
- **Versus AgentWorldBench.** It also predicts the results of agent actions, but its trajectories come from
  benchmark tasks in sandboxes. RolloutBench uses real-world sessions, where results depend on the actual
  state of machines, websites, jobs and people.
- Sources for the comparison: arXiv 2605.15188 (FutureSim), arXiv 2606.24597 (AgentWorldBench), arXiv 2409.19839 and forecastbench.org
  (ForecastBench), and arXiv 2604.07355 (PredictionArena). Figures are as reported by the authors and were not
  re-verified here.

## Caveats

- **Sample size.** Both benchmarks are small, so differences between models are noisy. For example, the
  standard error on Spearman ρ with n = 200 is about 0.07.
- **RolloutBench sources are narrow and the judge is Opus.** The 249 calls come from two public datasets, and
  the judge may favour its own model family. See [its caveats](rolloutbench/README.md#caveats).
- **Batched predictions.** ReplyBench predicts 25 stories per call, so the model can calibrate them against
  each other within a batch.
