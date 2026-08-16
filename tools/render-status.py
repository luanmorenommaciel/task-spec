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
        "pass_ubuntu_macos": "Pass on Ubuntu and macOS",
        "pending_release_tag": "Pending release tag",
        "published_main": "Published on main",
        "unpublished_worktree": "Unpublished worktree",
        "implemented_local_unpublished": "Implemented locally; unpublished",
        "pending_final_run": "Pending final run",
        "not_run": "Not run",
        "not_updated": "Not updated",
        "pending_v3.8.0_release_tag": "Pending v3.8.0 release tag",
        "unavailable_while_repository_private": "Unavailable while repository is private",
    }.get(value, value.replace("_", " ").capitalize())


def render(evidence: dict) -> str:
    gates = evidence["gates"]
    rows = [
        ("Engine", "Bash 3.2 portability, schemas, formats v1-v4, HMAC v1/v2/v3, TaskRevision, graph, DoD, conformance", f"{label(gates['make_check'])} — `make check` → `CHECK=READY`"),
        ("Trust hardening", "Downgrade, receipt replay/staleness, committed scope, symlink escape, base divergence, closure drift, and crash recovery", f"Evidence {gates['v38_adversarial_suite']}"),
        ("v4 evidence", "Policy validation, hidden holdout, v2 receipt subjects/signatures, mutation audit, identity/revocation, A2A/MCP round trip", f"Evidence suite {gates['v37_evidence_suite']}"),
        ("Experience", "Global/copy/symlink installs, isolated demo, and init → sign → plan → generate → gate → handoff → execute → accept", f"{label(gates['clean_room'])}; experience suite {gates['experience_suite']}"),
        ("Hosted CI", "Full repository gate on Ubuntu and macOS", f"{label(gates['hosted_ci'])} — [run]({gates['hosted_ci_run']})"),
        ("Package", "`npm pack --dry-run` and local global npm install", f"{label(gates['npm_pack_dry_run'])}; GitHub install {label(gates['npm_github_install']).lower()}"),
        ("Research", "Offline fake Firecrawl/Tavily/Exa adapters and named failure states", f"{label(gates['research_fake_adapters'])}; live providers not advertised"),
        ("Converge consumption", "Deterministic generated mirror plus per-file SHA-256 lock", f"{label(gates['converge_mirror'])}"),
        ("External engines", "Nine-family matrix contract and honest unavailable state", f"{label(gates['real_engine_matrix'])}; no real-engine result claimed"),
        (
            "Publication",
            "Canonical source commit, main branch, v3.8.0 tag, checksum assets, and authenticated release doors",
            f"{label(evidence['release_status'])}; hosted install {label(gates['release_install_workflow']).lower()}",
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
