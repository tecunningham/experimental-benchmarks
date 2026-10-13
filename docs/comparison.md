# How these benchmarks compare with existing prediction benchmarks

[← back to the benchmark list](../README.md)

|  | **FutureSim** (Goel et al. 2026) | **ForecastBench** (Karger et al.) | **PredictionArena** (Zhang et al. 2026) | **AgentWorldBench** (Zuo et al. 2026) | **ReplyBench-HN** (this repo) | **RolloutBench** (this repo) |
|---|---|---|---|---|---|---|
| What is predicted | Short-answer questions about world events. An agent replays the news day by day (24 Dec 2025 – Mar 2026) and updates its forecasts. | Binary probabilities on future events: market questions plus questions generated from time-series data (FRED, ACLED, Wikipedia, …) | Nothing stated explicitly. Agents trade Kalshi and Polymarket markets with real money ($10k each). | The next environment observation given an agent's action/observation history (MCP, search, terminal, SWE, Android, web, OS) | Human responses to actions: email replies, MR merges, HN points | The result of each tool call in a real agent session: shell, web, APIs, GPU jobs, sub-agents, human replies |
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
