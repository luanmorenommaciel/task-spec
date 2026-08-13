#!/usr/bin/env python3
"""Render or verify the CLI table sourced from TaskSpecAgentContext/v1."""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
START = "<!-- agent-context:start -->"
END = "<!-- agent-context:end -->"


def escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render() -> str:
    context = json.loads(subprocess.check_output(
        [str(ROOT / "bin" / "taskspec"), "agent-context"], cwd=ROOT, text=True,
    ))
    lines = [START, "| Command | Mutation contract | Stable tokens |", "|---|---|---|"]
    for command, contract in context["commands"].items():
        tokens = ", ".join(f"`{token}`" for token in contract["tokens"]) or "—"
        lines.append(f"| `taskspec {escape(command)}` | {escape(contract['mutation'])} | {tokens} |")
    lines.append(END)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", metavar="MARKDOWN")
    args = parser.parse_args()
    expected = render()
    if not args.check:
        print(expected)
        return 0
    path = pathlib.Path(args.check)
    text = path.read_text(encoding="utf-8")
    start, end = text.find(START), text.find(END)
    if start < 0 or end < 0:
        print("CLI_REFERENCE=STALE missing markers", file=sys.stderr)
        return 1
    if text[start:end + len(END)] != expected:
        print("CLI_REFERENCE=STALE run: python3 tools/render-cli-reference.py", file=sys.stderr)
        return 1
    print("CLI_REFERENCE=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
