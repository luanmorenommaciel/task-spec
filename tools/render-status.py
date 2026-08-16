#!/usr/bin/env python3
"""Render/check README status from release evidence and its scorecard."""

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
        "working": "Working release",
        "rc": "Release candidate",
        "published": "Published",
        "blocked": "Blocked",
        "not_run": "Not run",
        "unavailable": "Unavailable",
        "fail": "Failed",
        "pending": "Pending",
    }.get(value, value.replace("_", " ").capitalize())


def load_scorecard(evidence: dict) -> dict:
    pointer = evidence["quality_scorecard"]
    path = (ROOT / pointer["path"]).resolve()
    path.relative_to(ROOT.resolve())
    return json.loads(path.read_text(encoding="utf-8"))


def render(evidence: dict, scorecard: dict) -> str:
    dimensions = {item["id"]: item for item in scorecard["dimensions"]}

    def dimension(dimension_id: str) -> str:
        item = dimensions[dimension_id]
        return f"{item['awarded_points']}/{item['max_points']}"

    total = scorecard["total"]
    release_label = label(evidence["release_status"])
    ready = "Release gate passed" if total["passed"] else "Release gate blocked"
    rows = [
        ("Evidence-derived score", "Only digest-matching retained artifacts earn points", f"**{total['awarded']}/{total['maximum']}**; target {total['target']}; {ready.lower()}"),
        ("Contract and trust", "Revision-bound authorization, compatibility, and the explicit HMAC boundary", dimension("contract_trust")),
        ("Lifecycle and recovery", "Nested workspaces, graph recovery, atomic acceptance, and replay resistance", dimension("lifecycle_recovery")),
        ("Documentation and DX", "Installed reviewer route, executable docs, and generated status", dimension("documentation_dx")),
        ("Harness and packaging", "All installation doors plus frozen Codex and Claude execution", dimension("harness_packaging")),
        ("Standards interoperability", "Pinned official A2A and MCP SDK conformance", dimension("standards_interoperability")),
        ("Private distribution and external proof", "Hosted CI, private signed provenance, authenticated installs, and externally signed sandbox evidence", dimension("public_external_proof")),
        ("Publication", f"Task-Spec {evidence['version']} at `{evidence['source']['commit'][:12]}`", release_label),
        ("Deliberately unclaimed", "Semantic truth, ecosystem-wide certification, and long-running production reliability", "3 points remain unavailable by design"),
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
    if evidence.get("contract") != "TaskSpecReleaseEvidence/v2":
        print("RELEASE_STATUS=STALE unsupported release evidence contract", file=sys.stderr)
        return 1
    expected = render(evidence, load_scorecard(evidence))
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
