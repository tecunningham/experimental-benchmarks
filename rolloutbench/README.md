# RolloutBench

**Can a model predict what happens when it acts?** Take a trace from a real model run. At each tool call,
hide the result and ask the model to predict it.

[← all benchmarks](../README.md) · [how it compares](../docs/comparison.md)

<p align="center"><img src="figures/headline.svg" alt="RolloutBench, 14 Claude models on 249 real-world tool calls: exact question score and independent judge score, with 95% CIs" width="100%"></p>

## Takeaways

- **Predicting tool results on real-world traces is far from solved, and it separates models well.** Across
  249 tool calls from real agent sessions, 14 Claude models span 46–74% accuracy on factual questions about
  the result. Judge scores run from 3.1 to 5.1 out of 10, and newer generations score clearly higher.
- **It tracks general capability closely.** Across the 13 models with an Epoch Capabilities Index score, the
  correlation with ECI is r = 0.93 for the exact question score and r = 0.97 for the judge score.
- **Graded exactly, no judge needed.** The main score comes from multiple-choice questions written from each
  real result before any model predicts. The models answer with probabilities, and scoring is exact, as in
  ReplyBench.
  - The independent LLM judge gives the same ranking, and shows no favouritism to its own model family.
  - A questions-only baseline shows how much the wording of the questions gives away.
- **The live world is the hard part.** API responses and web content score lowest. In a synthetic sandbox
  pilot, outputs that follow from code were nearly solved (similarity ≈ 0.9). That is why real-world traces
  matter, and it's the key difference from AgentWorldBench, which uses benchmark-task trajectories.

## Why

**The problem.** We want to know whether a model can achieve real-world outcomes, such as exfiltrating
itself, causing harm at scale, or making money. Evals that test this directly are expensive and dangerous to
run.

**The idea.** Instead, measure whether the model can *accurately predict the effects of its actions*. To act
well, an agent has to anticipate what each action will do. A model that could predict every tool result
perfectly wouldn't need the tools at all; it could plan entirely in its head.

**The advantages.**

| | |
|---|---|
| **Cheap** | It needs only one forward pass per tool call and no live environment: a few hundred calls per model. |
| **Real-world** | The traces come from real use, so the score measures exactly the predictions that matter for real decisions. |
| **Unsaturatable** | A slightly better prediction is always possible. Scores are continuous, and the ceiling is the world's own noise, not 100%. |
| **Decision-relevant** | A model that predicts better in a situation should be able to make better decisions there. |

## Construction

1. **Collect traces from previous model runs, ideally in the real world, not on benchmarks.** Each trace is a
   sequence of tool calls with the results that actually came back.
2. **Hide each tool result in turn.** For step *k*, the model sees everything up to and including call *k*,
   with the true results of the earlier steps, and predicts the result of call *k*.
3. **No internet access.** If the model could reach the internet, it could simply re-run the call (fetch the
   page, hit the API) and short-circuit the prediction.
4. **Score each prediction continuously** against what really came back.

The tool calls that matter, and what predicting each one means:

| Tool call | What the model predicts | Example signal | Covered by the real-trace test? |
|---|---|---|---|
| Run local software | stdout, stderr, exit code | Does the test pass? What number does the script print? | ✅ shell, file reads |
| Web fetch | The page content, or key facts from it | Price on a product page, contents of a docs page | ✅ web fetch and search |
| Run a GPU experiment | Metrics and logs | Loss after N steps, whether it OOMs, job status | ✅ Hugging Face GPU jobs |
| API call | The response body or status | Search results, the error an API returns | ✅ Hub and GitHub APIs |
| Run a biology experiment | The assay readout | Did the protein express? Yield, growth curve | – |
| Send an email | The reply, if any | Whether someone replies, what they say | ~ only 4 replies to the agent's questions |
| Spawn an agent | The sub-agent's final response | What the sub-agent concludes or returns | ✅ research sub-agents |

The "send email" row overlaps with [ReplyBench](../replybench/). A response from a person is just one more
kind of tool result, so RolloutBench is the general frame and ReplyBench is one slice of it.

## Results on real-world traces

**Data.** 249 tool calls sampled from 75 *real* agent sessions in two public Hugging Face datasets. These are
people's actual work, not benchmark tasks:

| Source | What it is | Calls used |
|---|---|---|
| [crispwisp/wisp-claude-code-sessions](https://huggingface.co/datasets/crispwisp/wisp-claude-code-sessions) | Claude Code on one person's real Arch Linux workstation: system config, agent tooling, a benchmark it was building | 88 |
| [lewtun/ml-intern-sessions](https://huggingface.co/datasets/lewtun/ml-intern-sessions) | An ML agent doing real training work: launching GPU jobs, searching the Hub, reading docs, running research sub-agents | 161 |

- **Dates.** Only calls from 2 June to 9 Sept 2026 are used, around and after the predictors' training cutoff.
- **Sampling.** Calls were sampled per tool category with a cap on each.
- **What's skipped.** File writes, edits and planning tools have trivial results, so they're left out.
- **What's not committed.** [`real/build.py`](real/build.py) downloads pinned revisions of both datasets and
  builds the items locally. Raw traces, items and predictions are kept out of git. Only per-item grades and
  scores are committed.

**Protocol.**
- **What the model sees.**
  - The session so far, up to 12k characters. This always includes the user's first message; earlier tool
    results are shown truncated to 600 characters.
  - The date.
  - The tool call itself.
  - Never the result, and no tools or internet.
- **Two ways of scoring.**
  1. **Questions (main score, exact).**
     - *Writing the questions.* Before any model predicts, Opus 5.5 reads each real result and writes 2–4
       multiple-choice questions about what matters for the agent's next step: did it succeed, which error,
       how many results, which item appears. That gives 930 questions in total, with the correct answer's
       position shuffled.
     - *Answering.* Each model gives a probability for every option.
     - *Scoring.* Brier skill against uniform guessing (0 = chance, 1 = perfect) and accuracy, scored exactly
       against the answer key ([`real/score_questions.py`](real/score_questions.py)).
  2. **Free-text prediction plus judge (secondary).** Each model writes out the full predicted result. A judge
     (Opus 5.5) grades each prediction *on its own* against the real result, 0–10, and marks whether the basic
     outcome was right. Grades are cached per model, so adding a model never changes anyone else's score.
- **Leakage check.** Opus 5.5 answers the questions with *no* session and *no* tool call. It gets 62% right,
  so question wording and plausible-option priors give a fair amount away.
  - We therefore also report a **hard-question** subset: the 454 questions where that questions-only
    predictor puts less than 50% on the right answer.
  - That subset is chosen using an Opus model, which may slightly understate Opus models' scores on it.
- **"Novel" items.** Agents often re-run the same call, for example polling a job's logs. A "copy the last
  result from the same tool" baseline flags the 202 items where the answer can't simply be copied from the
  history. Judge scores on these novel items are in [`real/scores.md`](real/scores.md).

**Results, 14 models** (95% bootstrap CIs over tool calls; best in bold):

| model | questions: Brier skill | questions: accuracy | hard questions: Brier skill | judge score (0–10) | outcome right |
|---|---|---|---|---|---|
| Haiku 4.5 | 0.08 [0.01, 0.14] | 46% [42%, 50%] | -0.06 [-0.15, 0.03] | 3.1 [2.8, 3.5] | 67% |
| Haiku 5.5 | 0.15 [0.08, 0.21] | 51% [47%, 55%] | 0.04 [-0.05, 0.12] | 3.6 [3.2, 4.0] | 65% |
| Sonnet 4.5 | 0.15 [0.08, 0.22] | 52% [48%, 56%] | 0.04 [-0.06, 0.12] | 3.5 [3.1, 3.9] | 68% |
| Sonnet 4.6 | 0.21 [0.15, 0.27] | 55% [51%, 59%] | 0.07 [-0.02, 0.15] | 3.8 [3.4, 4.2] | 69% |
| Sonnet 5 | 0.20 [0.15, 0.26] | 55% [51%, 59%] | 0.07 [0.00, 0.14] | 4.1 [3.7, 4.5] | 73% |
| Sonnet 5.5 | 0.36 [0.30, 0.43] | 65% [61%, 69%] | 0.14 [0.06, 0.23] | 4.6 [4.2, 5.0] | 74% |
| Opus 4.5 | 0.21 [0.15, 0.27] | 55% [51%, 59%] | 0.08 [0.00, 0.16] | 3.6 [3.3, 4.0] | 71% |
| Opus 4.6 | 0.17 [0.11, 0.24] | 52% [48%, 56%] | 0.02 [-0.07, 0.11] | 3.8 [3.5, 4.2] | 70% |
| Opus 4.7 | 0.25 [0.19, 0.32] | 58% [54%, 62%] | 0.08 [-0.00, 0.16] | 4.1 [3.7, 4.5] | 70% |
| Opus 4.8 | 0.23 [0.18, 0.30] | 58% [54%, 62%] | 0.08 [0.01, 0.16] | 4.1 [3.7, 4.5] | 69% |
| Opus 5 | 0.38 [0.32, 0.43] | 67% [63%, 71%] | 0.21 [0.14, 0.29] | 4.3 [4.0, 4.7] | 74% |
| Opus 5.5 | **0.49 [0.44, 0.55]** | 74% [70%, 77%] | 0.23 [0.16, 0.31] | **5.1 [4.7, 5.5]** | 79% |
| Fable 5 | 0.40 [0.34, 0.45] | 67% [63%, 71%] | 0.22 [0.15, 0.29] | 4.5 [4.1, 4.9] | 74% |
| Fable 5.1 | 0.46 [0.41, 0.52] | 73% [69%, 77%] | **0.28 [0.21, 0.35]** | 4.7 [4.3, 5.1] | 77% |
| *questions only (Opus 5.5, no session or call)* | 0.33 [0.28, 0.38] | 62% [58%, 66%] | -0.12 [-0.17, -0.08] | – | – |

**Correlation with general capability.** Across the 13 models with an Epoch Capabilities Index (ECI) score:

<p align="center"><img src="figures/eci.svg" alt="RolloutBench question score and judge score against ECI across 13 Claude models: Pearson r 0.93 and 0.97" width="100%"></p>

**By kind of tool call** (judge score):

<p align="center"><img src="figures/by_tool.svg" alt="Heatmap of judge score by model and tool category: GPU job and sub-agent highest, API call and web lowest" width="100%"></p>

**Examples (Opus 5.5, free-text prediction).**
- ✅ `WebFetch` of a GitHub API directory listing for Hyprland v0.54.3 → it predicted the single file
  `SetUtils.hpp`. Score 10.
- ✅ Fetching a Hugging Face docs page → it predicted the HTTP 429 rate-limit error, inferred from the recent
  history. Score 10.
- ❌ `hf_jobs ps` → it predicted a table with one running job. In fact there were "No running jobs found",
  which is exactly the fact that matters for the next decision. Score 0.

**What this shows.**
- **Well spread, and the spread tracks capability.**
  - The 5.x generation (Sonnet 5.5, Opus 5 and 5.5, Fable 5 and 5.1) is clearly ahead of the 4.x models on
    every metric.
  - Within a generation, larger tiers usually score higher.
- **Outcomes are easier than details.** Even the best models get the basic outcome right only about 80% of
  the time, and the specific facts far less often.
- **On hard questions, Fable 5.1 leads** (Brier skill 0.28), ahead of Opus 5.5 (0.23) and Fable 5 (0.22).
  Older models are near chance there.
- **No judge self-preference.** Across models, the judge score correlates with the judge-free string
  similarity at r = 0.95. The Opus judge's own family sits exactly on that line (mean residual 0.00).

Reproduce:
```bash
python3 rolloutbench/real/build.py                                  # download pinned sources, build items
python3 rolloutbench/real/make_questions.py                         # write questions from the real results
python3 rolloutbench/real/run_questions.py --model claude-opus-5-5   # answer questions (repeat per model; --blind for the leakage check)
python3 rolloutbench/real/score_questions.py                        # exact question scores
python3 rolloutbench/real/run.py --model claude-opus-5-5             # free-text predictions (repeat per model)
python3 rolloutbench/real/judge.py && python3 rolloutbench/real/score.py   # independent judge grades + scores
python3 common/eci_summary.py && python3 rolloutbench/make_figures.py      # ECI correlations, figures
```

## Sandbox pilot (synthetic traces)

The first prototype used traces from a Claude agent (Haiku 5.5, Bash only) working 8 small sandbox tasks in
[`tasks.json`](tasks.json). It produced 76 tool calls, scored by string similarity.

<p align="center"><img src="figures/sandbox.svg" alt="Sandbox pilot: similarity about 0.9 for outputs that follow from code, 0.59-0.74 for outputs that depend on the machine" width="100%"></p>

All 14 models (similarity on the 54 non-trivial steps): Haiku 4.5 0.67, Haiku 5.5 0.76, Sonnet 4.5 0.72,
Sonnet 4.6 0.77, Sonnet 5 0.69, Sonnet 5.5 0.77, Opus 4.5 0.75, Opus 4.6 0.71, Opus 4.7 0.75, Opus 4.8 0.75,
Opus 5 0.78, Opus 5.5 **0.83**, Fable 5 0.82, Fable 5.1 0.80. Full table: [`results/scores.md`](results/scores.md).

**What it showed.**
- When the output follows from code in the trace (SQL aggregates, the sum of primes below 10⁶), all models
  score about 0.9.
- When the output depends on machine state (Python version, file counts), scores drop to 0.59–0.74.
- So synthetic sandbox traces are too easy. The point of real-world traces is that more of each result
  depends on the world rather than on the code.

## Related work

The closest prior work is **AgentWorldBench**: Zuo et al., "Qwen-AgentWorld: Language World Models for
General Agents", [arXiv:2606.24597](https://arxiv.org/abs/2606.24597), 2026;
[dataset](https://huggingface.co/datasets/Qwen/AgentWorldBench).
- **What it does.** Models predict the next environment observation given the action/observation history.
  There are 2,170 samples across 7 domains (MCP, search, terminal, SWE, Android, web, OS), scored by an LLM
  judge on format, factuality, consistency, realism and quality.
- **Headline result.** Frontier models are tightly clustered at about 54–59 out of 100.
- **The key difference is the data source.** AgentWorldBench trajectories come from agents running
  *benchmark* tasks (Terminal-Bench, OSWorld, Tool Decathlon, …) in clean sandboxes. RolloutBench uses traces
  from *real-world use*: real machines, real ML jobs, real websites in their actual state, and replies from
  real people and sub-agents. Those are the outcomes that matter for whether an agent can act effectively in
  the world.
- **It also covers tool types AgentWorldBench lacks:** GPU jobs, sub-agents and human replies.

Other related work:

| Work | What is predicted | Data | Contrast with RolloutBench |
|---|---|---|---|
| ToolEmu ([Ruan et al., 2023](https://arxiv.org/abs/2309.15817)) | An LM emulates tool execution, used for safety red-teaming | Synthetic tools and scenarios | Emulation is a means to an end; its fidelity to real outputs isn't measured |
| StableToolBench ([Guo et al., 2024](https://arxiv.org/abs/2403.07714)) | Simulated API responses that replace unstable real APIs | ToolBench (RapidAPI) | The simulator is infrastructure, not the skill being evaluated |
| Simia ([2025](https://arxiv.org/abs/2511.01824)), DreamGym ([Chen et al., 2025](https://arxiv.org/abs/2511.03773)) | LLM-simulated environment transitions for agent training | Synthetic or benchmark environments | Fidelity is judged only indirectly, through downstream agent gains |
| Text world simulators ([Wang et al., 2024](https://arxiv.org/abs/2406.06485)) | State transitions in text games (ByteSized32-State-Prediction) | Synthetic games | Toy, fully specified state |
| WebDreamer ([Gu et al., 2024](https://arxiv.org/abs/2411.06559)), WMA ([Chae et al., 2024](https://arxiv.org/abs/2410.13232)) | Results of web actions, for planning | Benchmark websites (WebArena, Mind2Web) | Web only, benchmark sites |
| CRUXEval ([Gu et al., 2024](https://arxiv.org/abs/2401.03065)), LiveCodeBench output prediction ([Jain et al., 2024](https://arxiv.org/abs/2403.07974)) | Output of short programs | Synthetic or contest code | Deterministic and self-contained; our sandbox pilot shows this is close to solved |
| CWM ([FAIR, 2025](https://arxiv.org/abs/2510.02387)) | An LLM trained on execution traces to model code execution | Python and Docker traces | A training approach; RolloutBench could evaluate models like it |
| Text world models survey ([Li et al., 2026](https://arxiv.org/abs/2606.09032)) | Survey of models that predict webpages, terminal output, API responses and user replies | – | An umbrella reference |

As far as we can tell, no existing benchmark scores predictions of tool, sub-agent and human results against
ground truth from **real-world** agent sessions.

## Next steps

1. **Scale up the real-world traces.** The public-trace test above is a start; the next step is volume and
   breadth.
   - *More public sources:* the Hugging Face hub has many more shared sessions (real `pi` coding-agent
     sessions, Codex sessions, paper-reproduction runs). Refresh monthly so the traces stay after the
     training cutoff.
   - *Private sources:* staff coding-agent sessions (with consent) and METR agent runs on open-ended tasks
     can't be contaminated. Check the eval-data rules before sending held-out task transcripts to model APIs.
   - *What to record:* the full tool result plus a timestamp, so each prediction is conditioned on the right
     moment.
2. **Fill in the missing tools.** Many more human replies (emails, review comments) using ReplyBench
   scoring; biology, via partner labs' electronic lab notebooks; GPU jobs scored on final metrics (loss,
   accuracy) rather than status messages.
3. **Sharpen the questions.** Exact question-based scoring is in place; the questions themselves can be
   better.
   - Filter out questions that a questions-only model can answer, at generation time.
   - Use a question-writer from another model family.
   - Run a questions-only baseline for every model, not just Opus 5.5.
   - Add numeric questions scored with a log score.
4. **Measure the noise ceiling.** Re-run reproducible calls to measure irreducible nondeterminism (timestamps,
   hashes, noise between training seeds). Report each score as a fraction of the ceiling.
5. **Validate the claim further.** The scores already track ECI closely (r = 0.93–0.97). Next, check them
   against agentic success directly (e.g. METR time horizon), and run agents on *simulated* tool results to
   see how far they get.
6. **Report a cost curve.** Plot score against thinking budget, and against offline retrieval over a frozen
   snapshot of the world before the trace's date.

## Caveats

- **Small, narrow sources.** 249 calls come from two sources, one of them a single person's workstation.
  There are only 4 human replies.
- **One model writes the questions and judges.** Opus 5.5 writes the questions, judges the free-text
  predictions, and is the questions-only baseline. We found no judge self-preference (see above), but the
  questions could still suit its way of thinking. A question-writer from another model family would be a good
  cross-check.
- **Question leakage.** Questions-only Opus 5.5 gets 62% right, so part of the "all questions" score is
  multiple-choice skill and calibration rather than knowledge of the result. The hard-question subset and the
  judge score are the cleaner measures.
- **Only Claude models.** No other providers' models are available in this environment, and ECI correlations
  over 13 models from one family have wide intervals.
- **Truncation.** Long results are cut to 4,000 characters for grading and earlier results to 600 characters
  in the context. The model sometimes can't see information that the real agent saw.
- **Contamination.** The sessions were public on Hugging Face from June 2026, around the training cutoff.
  Future models may have trained on them, so the benchmark needs fresh traces over time.
- **Possible duplicate sessions.** The ML-agent dataset uploads some sessions more than once, under
  different dates.

Reproduce the sandbox pilot with `rolloutbench/make_traces.py`, `run.py` and `score.py`.
