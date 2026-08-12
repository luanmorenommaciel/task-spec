#!/usr/bin/env python3
"""Explain authoring weaknesses before a Task-Spec is sealed or delegated."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
from taskspec_data import DataError, frontmatter  # noqa: E402


def section(text: str, name: str) -> str:
    match = re.search(rf"^##\s+{re.escape(name)}\s*$\n(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    return match.group(1).strip() if match else ""


def inspect(path: pathlib.Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8"); fm = frontmatter(text); findings: list[dict[str, str]] = []
    goal = section(text, "Goal")
    if len(goal.split()) < 8: findings.append({"severity": "block", "code": "GOAL_VAGUE", "message": "Goal is too short to establish an observable outcome."})
    success = section(text, "Success Criteria")
    if re.search(r"test\s+-[fde]\s+", success) and not re.search(r"pytest|python|node|npm|make|cargo|go test|\./", success):
        findings.append({"severity": "warn", "code": "EXISTENCE_ONLY", "message": "Success criteria can be satisfied by a stub; execute the artifact."})
    if not fm.get("baseline_ref") and not fm.get("reference_solution"):
        findings.append({"severity": "warn", "code": "NO_BASELINE", "message": "No baseline is declared for discrimination testing."})
    paths = [*fm.get("touches_paths", []), *fm.get("creates_paths", [])]
    if any(item in {".", "*", "**", "/"} or str(item).endswith("/**") for item in paths):
        findings.append({"severity": "block", "code": "UNBOUNDED_WRITES", "message": "Write scope is too broad for safe delegation."})
    if fm.get("profile", "standard") == "full" and not isinstance(fm.get("requires"), dict):
        findings.append({"severity": "warn", "code": "NO_ENVIRONMENT", "message": "Full profile does not declare runtime requirements."})
    questions = section(text, "Open Questions")
    if questions and questions.lower() not in {"(none)", "none", "- (none)"} and fm.get("status") != "blocked":
        findings.append({"severity": "block", "code": "OPEN_DECISION", "message": "Open questions remain but status is not blocked."})
    if int(str(fm.get("format_version", 0)).split(".")[0]) >= 4 and not isinstance(fm.get("evaluation_policy"), dict):
        findings.append({"severity": "block", "code": "NO_EVALUATION_POLICY", "message": "Format v4 requires an explicit evaluation policy."})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("spec"); parser.add_argument("--json", action="store_true"); args = parser.parse_args()
    try: findings = inspect(pathlib.Path(args.spec))
    except (OSError, DataError, ValueError) as exc: print(f"AUTHOR_DOCTOR=INVALID error={exc}", file=sys.stderr); return 1
    blockers = sum(item["severity"] == "block" for item in findings)
    if args.json: print(json.dumps({"contract": "AuthorDoctorResult/v1", "ok": blockers == 0, "findings": findings}, indent=2))
    elif not findings: print("AUTHOR_DOCTOR=READY no findings")
    else:
        for item in findings: print(f"{item['severity'].upper()} {item['code']} — {item['message']}")
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
