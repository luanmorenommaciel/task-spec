#!/usr/bin/env python3
"""Emit a credential-free, read-only TaskHandoff v1 contract."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
from taskspec_data import DataError, frontmatter, parse_yaml_subset, sensitive_key_paths, sha256_file  # noqa: E402


def section(text: str, name: str) -> str:
    match = re.search(rf"^##\s+{re.escape(name)}\s*$\n(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    return match.group(1) if match else ""


def fenced_yaml(text: str) -> dict:
    match = re.search(r"```ya?ml\s*\n(.*?)```", text, re.S | re.I)
    if not match:
        raise DataError("Validation Card has no YAML fence")
    data = parse_yaml_subset(match.group(1))
    if not isinstance(data, dict):
        raise DataError("Validation Card must be a mapping")
    return data


def workspace_for(spec: pathlib.Path) -> pathlib.Path:
    configured = os.environ.get("TASKSPEC_BACKLOG_DIR")
    if configured:
        backlog = pathlib.Path(configured).resolve()
        try:
            spec.relative_to(backlog)
            return backlog.parent
        except ValueError:
            pass
    for parent in spec.parents:
        if parent.name == "tasks":
            return parent.parent
    return spec.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec")
    parser.add_argument("--backend", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    spec = pathlib.Path(args.spec).resolve()
    try:
        text = spec.read_text(encoding="utf-8")
        fm = frontmatter(text)
        card = fenced_yaml(section(text, "Validation Card"))
    except (OSError, DataError) as exc:
        print(f"HANDOFF=INVALID\nerror: {exc}", file=sys.stderr)
        return 1
    if fm.get("effort") in {"XL", "XXL"}:
        print("HANDOFF=REFUSED\nerror: decomposition nodes are not executable; hand off a child leaf", file=sys.stderr)
        return 1
    if fm.get("signed_off") is not True:
        print("HANDOFF=REFUSED\nerror: spec is not authorized; run taskspec gate --stamp first", file=sys.stderr)
        return 1
    credential_paths = sensitive_key_paths(card.get("agent_contract", {}), "$.agent_contract")
    if credential_paths:
        print(
            f"HANDOFF=REFUSED\nerror: credential-bearing keys are forbidden in TaskHandoff: {credential_paths}",
            file=sys.stderr,
        )
        return 1
    declared_backend = str(fm.get("execution_backend", "any"))
    if declared_backend != "any" and args.backend != declared_backend:
        print(f"HANDOFF=REFUSED\nerror: backend {args.backend!r} conflicts with sealed execution_backend {declared_backend!r}", file=sys.stderr)
        return 1

    validator = ROOT / "src" / "gate" / "validate-task-spec.sh"
    checked = subprocess.run(
        ["bash", str(validator), "--no-state", str(spec)],
        cwd=str(workspace_for(spec)), text=True, capture_output=True, check=False,
    )
    validation_output = checked.stdout + checked.stderr
    if checked.returncode:
        print(validation_output, file=sys.stderr, end="")
        print("HANDOFF=INVALID", file=sys.stderr)
        return 1
    tier = 1 if "OK(Tier 1)" in validation_output else 2
    do_not_touch = re.findall(r"`([^`]+)`", section(text, "Do-Not-Touch"))
    absolute = str(spec)
    handoff = {
        "contract": "TaskHandoff/v1",
        "task_id": fm.get("id"),
        "spec": absolute,
        "spec_digest": sha256_file(spec),
        "signoff_tier": tier,
        "backend": args.backend,
        "workspace": str(workspace_for(spec)),
        "write_scope": {
            "touches_paths": fm.get("touches_paths", []),
            "creates_paths": fm.get("creates_paths", []),
            "do_not_touch": do_not_touch,
        },
        "budgets": {
            "iterations": fm.get("budget_iterations"),
            "tokens": fm.get("budget_tokens"),
            "effort": fm.get("effort"),
        },
        "agent_contract": card.get("agent_contract", {}),
        "eval_command": ["taskspec", "run", "--ci", absolute],
        "acceptance_command": ["taskspec", "accept", "--stamp", absolute],
    }
    print(json.dumps(handoff, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
