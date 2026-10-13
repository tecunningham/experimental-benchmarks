8 traces, 76 tool calls (54 with non-empty output)

| model | similarity_all | similarity_nontrivial | exact_all | exact_nontrivial |
|---|---|---|---|---|
| baseline: always empty-output marker | 0.372 | 0.117 | 0.289 | 0 |
| baseline: repeat previous output | 0.297 | 0.135 | 0.184 | 0 |
| claude-haiku-5-5 | 0.735 | 0.756 | 0.461 | 0.37 |
| claude-opus-5-5 | 0.881 | 0.832 | 0.553 | 0.37 |
| claude-sonnet-5-5 | 0.834 | 0.766 | 0.553 | 0.37 |

Mean similarity on non-trivial steps, by task:

| model | collatz | sysinfo | sqlite | c_program | git_repo | text_stats | bugfix | pystdlib |
|---|---|---|---|---|---|---|---|---|
| baseline: always empty-output marker | 0.13 | 0.1 | 0.2 | 0.1 | 0.15 | 0.08 | 0.12 | 0.09 |
| baseline: repeat previous output | 0.12 | 0.13 | 0.19 | 0.1 | 0.12 | 0.11 | 0.11 | 0.19 |
| claude-haiku-5-5 | 0.87 | 0.59 | 1.0 | 1.0 | 0.88 | 1.0 | 0.95 | 0.57 |
| claude-opus-5-5 | 0.85 | 0.74 | 1.0 | 1.0 | 0.88 | 0.99 | 0.96 | 0.73 |
| claude-sonnet-5-5 | 0.84 | 0.65 | 1.0 | 1.0 | 0.85 | 0.97 | 0.78 | 0.66 |
