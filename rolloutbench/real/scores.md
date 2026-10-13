249 tool calls from 75 real sessions (88 wisp, 161 ml-intern), dated 2026-06-02 to 2026-09-09.

**All items** (n=249)

| predictor | judge score (0-10) | outcome right | similarity |
|---|---|---|---|
| baseline: copy last result of same tool | – | – | 0.24 |
| claude-fable-5 | 4.48 ± 0.21 | 74% | 0.45 |
| claude-fable-5-1 | 4.73 ± 0.21 | 77% | 0.48 |
| claude-haiku-4-5 | 3.13 ± 0.18 | 67% | 0.36 |
| claude-haiku-5-5 | 3.60 ± 0.19 | 65% | 0.35 |
| claude-opus-4-5 | 3.61 ± 0.19 | 71% | 0.40 |
| claude-opus-4-6 | 3.83 ± 0.19 | 70% | 0.41 |
| claude-opus-4-7 | 4.08 ± 0.21 | 70% | 0.42 |
| claude-opus-4-8 | 4.09 ± 0.20 | 69% | 0.42 |
| claude-opus-5 | 4.33 ± 0.20 | 74% | 0.43 |
| claude-opus-5-5 | 5.12 ± 0.21 | 79% | 0.51 |
| claude-sonnet-4-5 | 3.50 ± 0.19 | 68% | 0.39 |
| claude-sonnet-4-6 | 3.81 ± 0.20 | 69% | 0.41 |
| claude-sonnet-5 | 4.09 ± 0.20 | 73% | 0.41 |
| claude-sonnet-5-5 | 4.56 ± 0.21 | 74% | 0.47 |

**Novel items (answer not copyable from history)** (n=202)

| predictor | judge score (0-10) | outcome right | similarity |
|---|---|---|---|
| baseline: copy last result of same tool | – | – | 0.10 |
| claude-fable-5 | 4.12 ± 0.21 | 74% | 0.41 |
| claude-fable-5-1 | 4.27 ± 0.21 | 76% | 0.43 |
| claude-haiku-4-5 | 3.01 ± 0.18 | 70% | 0.33 |
| claude-haiku-5-5 | 3.55 ± 0.20 | 69% | 0.32 |
| claude-opus-4-5 | 3.36 ± 0.19 | 72% | 0.36 |
| claude-opus-4-6 | 3.49 ± 0.19 | 70% | 0.36 |
| claude-opus-4-7 | 3.71 ± 0.21 | 69% | 0.37 |
| claude-opus-4-8 | 3.83 ± 0.21 | 70% | 0.38 |
| claude-opus-5 | 3.85 ± 0.20 | 73% | 0.37 |
| claude-opus-5-5 | 4.66 ± 0.22 | 77% | 0.45 |
| claude-sonnet-4-5 | 3.25 ± 0.19 | 70% | 0.36 |
| claude-sonnet-4-6 | 3.39 ± 0.20 | 69% | 0.36 |
| claude-sonnet-5 | 3.81 ± 0.21 | 74% | 0.37 |
| claude-sonnet-5-5 | 4.00 ± 0.21 | 72% | 0.41 |

**Judge score by tool category, novel items** (n per category in header)

| predictor | shell (59) | web (29) | GPU job (27) | API call (35) | sub-agent (26) | file read (24) | human reply (2) |
|---|---|---|---|---|---|---|---|
| claude-fable-5 | 4.3 | 2.8 | 5.2 | 2.6 | 6.0 | 4.3 | 3.0 |
| claude-fable-5-1 | 4.5 | 3.6 | 5.5 | 2.6 | 5.4 | 4.4 | 3.5 |
| claude-haiku-4-5 | 3.5 | 2.7 | 4.6 | 1.6 | 3.0 | 2.8 | 0.0 |
| claude-haiku-5-5 | 3.2 | 2.8 | 4.9 | 2.3 | 5.4 | 3.8 | 1.0 |
| claude-opus-4-5 | 3.5 | 2.8 | 5.0 | 1.9 | 3.8 | 3.4 | 3.0 |
| claude-opus-4-6 | 3.7 | 3.2 | 4.6 | 2.1 | 3.7 | 3.8 | 3.0 |
| claude-opus-4-7 | 4.1 | 2.9 | 5.2 | 2.3 | 5.2 | 2.7 | 3.0 |
| claude-opus-4-8 | 4.0 | 3.1 | 5.0 | 2.3 | 5.4 | 3.8 | 1.0 |
| claude-opus-5 | 4.2 | 3.0 | 5.2 | 2.1 | 4.8 | 4.0 | 3.0 |
| claude-opus-5-5 | 4.8 | 4.6 | 5.5 | 2.8 | 6.0 | 4.7 | 3.5 |
| claude-sonnet-4-5 | 3.6 | 2.6 | 4.4 | 1.9 | 2.9 | 4.0 | 5.0 |
| claude-sonnet-4-6 | 3.8 | 2.6 | 5.1 | 2.0 | 3.3 | 3.9 | 0.0 |
| claude-sonnet-5 | 4.0 | 2.8 | 5.4 | 2.1 | 5.3 | 3.8 | 1.5 |
| claude-sonnet-5-5 | 4.1 | 3.7 | 5.2 | 2.3 | 5.6 | 3.7 | 0.5 |
