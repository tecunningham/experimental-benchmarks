"""Minimal model backend: Anthropic SDK if ANTHROPIC_API_KEY is set, else the `claude` CLI.

Either way the model gets no tools and no internet access.
"""
import json
import os
import subprocess
import tempfile


def complete(prompt: str, model: str, system: str = "", max_tokens: int = 4096) -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic

        r = anthropic.Anthropic().messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system or anthropic.NOT_GIVEN,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in r.content if b.type == "text")

    cmd = [
        "claude", "-p", "--model", model, "--tools", "", "--setting-sources", "",
        "--no-session-persistence", "--output-format", "json",
        "--system-prompt", system or "You are a careful forecaster.",
    ]
    # Run from an empty dir so no project context leaks in.
    with tempfile.TemporaryDirectory() as d:
        out = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=d, timeout=900)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[-2000:] or out.stdout[-2000:])
    res = json.loads(out.stdout)
    served = list(res.get("modelUsage", {}))
    if served and model not in served:  # the CLI can silently substitute a different model
        raise RuntimeError(f"requested {model}, served by {served}")
    return res["result"]
