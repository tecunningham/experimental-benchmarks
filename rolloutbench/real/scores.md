249 tool calls from 75 real sessions (88 wisp, 161 ml-intern), dated 2026-06-02 to 2026-09-09.

**All items** (n=249)

| predictor | judge score (0-10) | outcome right | similarity |
|---|---|---|---|
| baseline: copy last result of same tool | – | – | 0.24 |
| claude-haiku-5-5 | 3.16 ± 0.19 | 65% | 0.35 |
| claude-opus-5-5 | 5.27 ± 0.21 | 80% | 0.51 |
| claude-sonnet-5-5 | 4.39 ± 0.21 | 74% | 0.47 |

**Novel items (answer not copyable from history)** (n=202)

| predictor | judge score (0-10) | outcome right | similarity |
|---|---|---|---|
| baseline: copy last result of same tool | – | – | 0.10 |
| claude-haiku-5-5 | 3.05 ± 0.19 | 67% | 0.32 |
| claude-opus-5-5 | 4.87 ± 0.22 | 78% | 0.45 |
| claude-sonnet-5-5 | 3.88 ± 0.21 | 72% | 0.41 |

**Judge score by tool category, novel items** (n per category in header)

| predictor | shell (59) | GPU job (27) | API call (35) | web (29) | sub-agent (26) | file read (24) | human reply (2) |
|---|---|---|---|---|---|---|---|
| claude-haiku-5-5 | 2.7 | 4.8 | 1.9 | 2.2 | 4.5 | 3.4 | 1.0 |
| claude-opus-5-5 | 4.9 | 5.7 | 3.1 | 5.0 | 6.3 | 4.8 | 3.5 |
| claude-sonnet-5-5 | 4.0 | 5.2 | 2.3 | 3.4 | 5.1 | 3.8 | 1.0 |
