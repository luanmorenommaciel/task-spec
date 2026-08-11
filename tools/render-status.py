#!/usr/bin/env python3
"""Render/check README's release-status table from release/evidence.json."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "release" / "evidence.json"
START = "<!-- release-status:start -->"
END = "<!-- release-status:end -->"


def label(value: str) -> str:
    return {
        "pass": "Pass",
        "pending_release_tag": "Pending release tag",
        "published_main": "Published on main",
        "unpublished_worktree": "Unpublished worktree",
    }.get(value, value.replace("_", " ").capitalize())


def render(evidence: dict) -> str:
    gates = evidence["gates"]
    rows = [
        ("Engine", "Bash 3.2 portability, schemas, compatibility, HMAC v1/v2, sizing, backlog, DoD, conformance", f"{label(gates['make_check'])} — `make check` → `CHECK=READY`"),
        ("Experience", "Copy/symlink installs plus init → sign → plan → generate → gate → handoff → execute → accept", f"{label(gates['clean_room'])}; experience suite {gates['experience_suite']}"),
        ("Package", "`npm pack --dry-run` and local global npm install", f"{label(gates['npm_pack_dry_run'])}; GitHub install {label(gates['npm_github_install']).lower()}"),
        ("Research", "Offline fake Firecrawl/Tavily/Exa adapters and named failure states", f"{label(gates['research_fake_adapters'])}; live providers not advertised"),
        ("Converge consumption", "Deterministic generated mirror plus per-file SHA-256 lock", f"{label(gates['converge_mirror'])}"),
        (
            "Publication",
            "Canonical source commit, main branch, v3.6.0 tag, and remote curl/npm doors",
            f"{label(evidence['release_status'])}; tag-dependent installs {label(gates['curl_pinned_install']).lower()}",
        ),
    ]
    lines = [START, "| Surface | Repository evidence | Status |", "|---|---|---|"]
    lines.extend(f"| {surface} | {proof} | {status} |" for surface, proof, status in rows)
    lines.append(END)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", metavar="README", help="fail when the marked README region is stale")
    args = parser.parse_args()
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    expected = render(evidence)
    if not args.check:
        print(expected)
        return 0
    path = pathlib.Path(args.check)
    text = path.read_text(encoding="utf-8")
    start = text.find(START)
    end = text.find(END, start + len(START))
    if start < 0 or end < 0:
        print("RELEASE_STATUS=STALE missing markers", file=sys.stderr)
        return 1
    actual = text[start:end + len(END)]
    if actual != expected:
        print("RELEASE_STATUS=STALE run: python3 tools/render-status.py", file=sys.stderr)
        return 1
    print("RELEASE_STATUS=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
