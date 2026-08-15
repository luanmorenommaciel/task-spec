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

reviewer_route = ROOT / "docs" / "getting-started" / "reviewer-route.md"
if "docs/getting-started/reviewer-route.md" not in text or not reviewer_route.is_file():
    raise SystemExit("README_VISUALS=INVALID reviewer route is missing")

images = re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", text)
if len(images) < 3:
    raise SystemExit(f"README_VISUALS=INVALID expected at least 3 images, found {len(images)}")
for alt, raw_path in images:
    if not alt.strip():
        raise SystemExit("README_VISUALS=INVALID image has empty alt text")
    path = raw_path.split(maxsplit=1)[0].strip("<>")
    if re.match(r"^[a-z]+://", path):
        continue
    if not (ROOT / path).is_file():
        raise SystemExit(f"README_VISUALS=INVALID missing image: {path}")

mermaid_blocks = len(re.findall(r"^```mermaid\s*$", text, re.M))
if mermaid_blocks < 2:
    raise SystemExit(f"README_VISUALS=INVALID expected at least 2 Mermaid diagrams, found {mermaid_blocks}")

print(
    f"README_COMMANDS=READY commands={len(mentioned)} "
    f"images={len(images)} mermaid={mermaid_blocks}"
)
