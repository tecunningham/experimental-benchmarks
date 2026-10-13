8 traces, 76 tool calls (54 with non-empty output)

| model | similarity_all | similarity_nontrivial | exact_all | exact_nontrivial |
|---|---|---|---|---|
| baseline: always empty-output marker | 0.372 | 0.117 | 0.289 | 0 |
| baseline: repeat previous output | 0.297 | 0.135 | 0.184 | 0 |
| claude-fable-5-1 | 0.858 | 0.8 | 0.539 | 0.352 |
| claude-fable-5 | 0.872 | 0.819 | 0.566 | 0.389 |
| claude-haiku-4-5 | 0.755 | 0.673 | 0.434 | 0.222 |
| claude-haiku-5-5 | 0.735 | 0.756 | 0.461 | 0.37 |
| claude-opus-4-5 | 0.824 | 0.753 | 0.5 | 0.296 |
| claude-opus-4-6 | 0.791 | 0.705 | 0.513 | 0.315 |
| claude-opus-4-7 | 0.781 | 0.747 | 0.513 | 0.37 |
| claude-opus-4-8 | 0.811 | 0.748 | 0.526 | 0.352 |
| claude-opus-5-5 | 0.881 | 0.832 | 0.553 | 0.37 |
| claude-opus-5 | 0.842 | 0.777 | 0.553 | 0.37 |
| claude-sonnet-4-5 | 0.799 | 0.717 | 0.5 | 0.296 |
| claude-sonnet-4-6 | 0.828 | 0.77 | 0.5 | 0.315 |
| claude-sonnet-5-5 | 0.834 | 0.766 | 0.553 | 0.37 |
| claude-sonnet-5 | 0.783 | 0.694 | 0.513 | 0.315 |

Mean similarity on non-trivial steps, by task:

| model | collatz | sysinfo | sqlite | c_program | git_repo | text_stats | bugfix | pystdlib |
|---|---|---|---|---|---|---|---|---|
| baseline: always empty-output marker | 0.13 | 0.1 | 0.2 | 0.1 | 0.15 | 0.08 | 0.12 | 0.09 |
| baseline: repeat previous output | 0.12 | 0.13 | 0.19 | 0.1 | 0.12 | 0.11 | 0.11 | 0.19 |
| claude-fable-5-1 | 0.76 | 0.66 | 1.0 | 1.0 | 0.88 | 0.99 | 0.95 | 0.78 |
| claude-fable-5 | 0.85 | 0.72 | 1.0 | 1.0 | 0.88 | 1.0 | 0.95 | 0.72 |
| claude-haiku-4-5 | 0.64 | 0.54 | 1.0 | 1.0 | 0.76 | 0.91 | 0.83 | 0.5 |
| claude-haiku-5-5 | 0.87 | 0.59 | 1.0 | 1.0 | 0.88 | 1.0 | 0.95 | 0.57 |
| claude-opus-4-5 | 0.83 | 0.65 | 1.0 | 1.0 | 0.76 | 0.89 | 0.92 | 0.67 |
| claude-opus-4-6 | 0.58 | 0.58 | 1.0 | 1.0 | 0.76 | 1.0 | 0.92 | 0.58 |
| claude-opus-4-7 | 0.86 | 0.62 | 1.0 | 1.0 | 0.85 | 1.0 | 0.9 | 0.52 |
| claude-opus-4-8 | 0.84 | 0.58 | 1.0 | 1.0 | 0.81 | 0.98 | 0.95 | 0.69 |
| claude-opus-5-5 | 0.85 | 0.74 | 1.0 | 1.0 | 0.88 | 0.99 | 0.96 | 0.73 |
| claude-opus-5 | 0.85 | 0.62 | 1.0 | 1.0 | 0.81 | 1.0 | 0.95 | 0.78 |
| claude-sonnet-4-5 | 0.61 | 0.57 | 1.0 | 1.0 | 0.77 | 0.91 | 0.93 | 0.7 |
| claude-sonnet-4-6 | 0.84 | 0.68 | 1.0 | 1.0 | 0.81 | 1.0 | 0.92 | 0.58 |
| claude-sonnet-5-5 | 0.84 | 0.65 | 1.0 | 1.0 | 0.85 | 0.97 | 0.78 | 0.66 |
| claude-sonnet-5 | 0.65 | 0.53 | 1.0 | 1.0 | 0.77 | 0.91 | 0.78 | 0.7 |
