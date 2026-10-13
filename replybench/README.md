# ReplyBench

**Can a model predict how people will respond to what it does?** Show the model an action (an email, a
merge request, a post) and ask it to predict the response: will anyone reply, will it be merged, will
people upvote it? The ground truth already sits in public data from after the model's training cutoff, so
nothing has to resolve in the future.

[← all benchmarks](../README.md) · [how it compares](../docs/comparison.md)

| Task | The action | The response to predict | Data | n |
|---|---|---|---|---|
| **Email** | A new thread on an Apache mailing list | Does anyone other than the sender reply? | 66 public `@apache.org` lists, Aug – mid-Sep 2026 | 191 |
| **PR** | A merge request on an open-source project | Is it merged within 30 days? | 20 GitLab projects (Mesa, GTK, KDE Plasma, Inkscape, KiCad, …), opened Jul–Aug 2026 | 234 |
| **HN** | A Hacker News submission | Points, comments, P(≥ 50 points) | Random HN stories, 1–6 Oct 2026 | 200 |

<p align="center"><img src="figures/headline.svg" alt="AUC and Brier skill with 95% CIs for Haiku, Sonnet and Opus on the email, PR and HN tasks" width="100%"></p>

## Takeaways

- **Models are good at predicting whether people will reply to an email.** On real thread starters (a
  call for votes, a design proposal, a newcomer's question) the AUC is 0.84–0.88, and the probabilities beat
  the base rate by a wide margin (Brier skill +0.33 to +0.47). It isn't just the subject tags: on emails
  without a `[VOTE]`/`[DISCUSS]`-style tag, AUC is about 0.89.
- **Merge prediction is harder, and only slightly better than a simple prior.** AUC is 0.76–0.79, against
  0.70 for a baseline that just uses each project's merge rate. On Brier score, only Sonnet's Brier skill
  (+0.14, CI [0.00, 0.26]) edges past that baseline (+0.11), and its interval overlaps it. Most of what
  models know is "which projects merge things"; the content of the MR adds a little.
- **Calibration depends on the setting.** On HN, models expect far more attention than a typical post gets,
  so they're *worse* than the base rate. On email and MRs they're under-confident: they hedge, and the
  things they rate as likely happen more often than they predict (see the reliability chart below).
- **Differences between models are small relative to the noise.** Opus is best or tied on most metrics, but
  at n ≈ 200 most of the confidence intervals overlap. Separating models will need about 1,000+ items per
  task.

<p align="center"><img src="figures/reliability.svg" alt="Reliability diagrams for email and PR tasks: curves lie above the diagonal, meaning models are under-confident" width="100%"></p>

## Why this matters

An agent pursuing a goal, whether that's persuading, organising, selling or attacking, has to predict how
people will react to each thing it does. Accurately predicting the effects of actions is a prerequisite for
taking good actions. ReplyBench measures that directly and cheaply, without anyone having to take the
actions.

## The three tasks

### Email: will anyone reply? ([`email/`](email/))

- **Data.** All Apache Software Foundation mailing lists are public. We took the 80 most active `user@`,
  `users@` and `dev@` lists, collected every human-written email that started a thread between 1 Aug and
  15 Sep 2026, and sampled up to 6 per list. Bot traffic is filtered out: JIRA, GitHub, CI and git-commit
  notifications.
- **Label.** Whether anyone other than the sender replied, checked about 6 weeks later. 58% got a reply.
- **Inputs.** The model sees the list, sender, date, subject and body, and gives P(reply).
- **Examples (Opus 5.5).**
  - "[VOTE] Release Apache Avro 1.12.2 RC2" (dev@avro): Opus said 95% reply, but nobody replied. The RC was
    superseded by RC3, the kind of context a model can't see.
  - Votes and design discussions are rated highly and usually do get replies. Announcements and board
    reports are rated low.

| predictor | AUC [95% CI] | Brier [95% CI] | Brier skill [95% CI] |
|---|---|---|---|
| baseline: base rate | – | 0.243 | 0 |
| claude-haiku-5-5 | 0.84 [0.77, 0.89] | 0.162 [0.134, 0.191] | +0.33 [+0.21, +0.45] |
| claude-sonnet-5-5 | 0.87 [0.81, 0.92] | 0.154 [0.128, 0.181] | +0.37 [+0.24, +0.48] |
| claude-opus-5-5 | **0.88** [0.83, 0.93] | **0.130** [0.103, 0.158] | **+0.47** [+0.35, +0.57] |

### PR: merged within 30 days? ([`pr/`](pr/))

- **Data.** GitHub's API isn't reachable from our environment, so this uses four public GitLab instances:
  GitLab.com, freedesktop, GNOME and KDE.
  - Up to 12 human-authored MRs were sampled per project from *all* MRs opened between 15 July and
    31 Aug 2026, whatever happened to them, so there's no survivorship bias.
  - Label: merged within 30 days. 65% were.
- **Inputs.** The model sees the project, author, title, description, draft flag, the number of files
  changed and the first ~1,500 characters of the diff, and gives P(merge).
- **Examples (Opus 5.5).**
  - "Draft: Test merge request, please ignore." (GTK): 2%, correct.
  - "Qt: Add packet list column freezing and row pinning" (Wireshark): 12%, but it was merged. A large UI
    feature from an outside contributor looks risky, yet Wireshark merges nearly everything.

| predictor | AUC [95% CI] | Brier [95% CI] | Brier skill [95% CI] |
|---|---|---|---|
| baseline: base rate | – | 0.228 | 0 |
| baseline: project merge rate (leave-one-out) | 0.70 [0.63, 0.77] | 0.202 [0.176, 0.227] | +0.11 [+0.01, +0.21] |
| claude-haiku-5-5 | 0.77 [0.70, 0.83] | 0.221 [0.199, 0.244] | +0.03 [−0.14, +0.16] |
| claude-sonnet-5-5 | 0.76 [0.69, 0.82] | **0.195** [0.171, 0.220] | **+0.14** [+0.00, +0.26] |
| claude-opus-5-5 | **0.79** [0.73, 0.85] | 0.203 [0.179, 0.228] | +0.11 [−0.06, +0.23] |

### HN: how much attention will a post get? ([`hn/`](hn/))

- **Data.** 200 stories drawn uniformly at random from all 4,687 HN submissions between 1 and 6 Oct 2026.
- **Inputs and outputs.** The model sees the title, domain, author and time, and predicts points, comments
  and P(≥ 50 points).

| predictor | Spearman (points) [95% CI] | AUC P(≥50) [95% CI] | Brier skill [95% CI] |
|---|---|---|---|
| baseline: median / base rate | 0 | 0.5 | 0 |
| claude-haiku-5-5 | 0.27 [0.14, 0.40] | 0.74 [0.59, 0.88] | −0.27 [−1.16, +0.09] |
| claude-sonnet-5-5 | 0.32 [0.19, 0.45] | 0.81 [0.69, 0.91] | −0.33 [−1.33, +0.05] |
| claude-opus-5-5 | **0.36** [0.23, 0.49] | **0.82** [0.70, 0.92] | **−0.05** [−0.66, +0.20] |

<p align="center"><img src="figures/calibration.svg" alt="Scatter plots of predicted vs actual HN points for three models; most dots lie below the diagonal, meaning stories were over-predicted" width="100%"></p>

## Next steps

1. **Scale each task to 1,000+ items** so that differences between models fall outside the CIs.
2. **Use private data.** METR's own email, Slack and PRs are contamination-proof and are exactly "the
   response to an action". Gmail and Slack connectors exist, but only with the people involved agreeing.
3. **Get causal data.** A/B-test archives answer the observational-not-causal objection: "which of two
   variants won?", with the audience held fixed.
4. **Predict richer responses:** time to reply, the content of the reply, review comments, and the
   reviewer's verdict.
5. **Add GitHub PRs** where API access is available. GH Archive is reachable and could provide outcomes at
   scale.

## Caveats

- **Observational data.** The sender's identity, the timing and the project all confound the effect of the
  content itself.
- **Batching.** Items are predicted in batches (10 emails, 5 MRs, or 25 HN stories per call), so a model can
  calibrate them against each other.
- **Email selection.** The most active lists are mostly `dev@` lists, so email covers developer
  communication more than user questions.
- **Not every bot is caught.** Nine automated git-commit emails slipped past the first filter; they were
  removed and the filter fixed.

## Running

```bash
python3 replybench/email/fetch.py && python3 replybench/pr/fetch.py      # build datasets
python3 replybench/run_binary.py --task email --model claude-opus-5-5     # predict (also --task pr)
python3 replybench/score_binary.py --task email                           # scores + CIs (also --task pr)
python3 replybench/hn/fetch.py && python3 replybench/hn/run.py --model claude-opus-5-5 && python3 replybench/hn/score.py
python3 replybench/make_figures.py                                        # figures/
```
