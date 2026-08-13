#!/usr/bin/env python3
"""Require every Task-Spec command in README code fences to name executed proof."""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
text = (ROOT / "README.md").read_text(encoding="utf-8")
coverage = json.loads((ROOT / "docs" / "readme-command-coverage.json").read_text(encoding="utf-8"))
if coverage.get("contract") != "ReadmeCommandCoverage/v1":
    raise SystemExit("README_COMMANDS=INVALID coverage contract")
mentioned = set()
for block in re.findall(r"^```(?:bash|console)\n(.*?)^```", text, re.M | re.S):
    for raw in block.splitlines():
        line = raw.strip()
        if line.startswith("$ "):
            line = line[2:]
        match = re.match(r"taskspec\s+([a-z][a-z-]*)\b", line)
        if match:
            mentioned.add(match.group(1))
declared = set(coverage.get("commands", {}))
missing, stale = mentioned - declared, declared - mentioned
if missing or stale:
    print(f"README_COMMANDS=INVALID missing={sorted(missing)} stale={sorted(stale)}", file=sys.stderr)
    raise SystemExit(1)
for command, proof in coverage["commands"].items():
    paths = re.findall(r"tests/[A-Za-z0-9_.-]+", proof)
    if not paths or any(not (ROOT / path).is_file() for path in paths):
        raise SystemExit(f"README_COMMANDS=INVALID {command} has no existing proof script")
print(f"README_COMMANDS=READY commands={len(mentioned)}")
