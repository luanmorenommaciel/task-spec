#!/usr/bin/env python3
"""Translate TaskHandoff contracts to portable A2A and MCP task envelopes."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any


def load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("contract") not in {"TaskHandoff/v1", "TaskHandoff/v2"}:
        raise ValueError("input must be TaskHandoff/v1 or TaskHandoff/v2")
    return value


def export(handoff: dict[str, Any], protocol: str) -> dict[str, Any]:
    identity = {"task_id": handoff["task_id"], "spec_digest": handoff["spec_digest"]}
    if protocol == "a2a":
        return {
            "contract": "TaskSpecA2AArtifact/v1", "artifactId": handoff["task_id"], "name": "task-spec-handoff",
            "parts": [{"kind": "data", "data": handoff}], "metadata": {**identity, "task_state": "submitted"},
        }
    return {
        "contract": "TaskSpecMCPTask/v1", "task": {"id": handoff["task_id"], "status": "working", "input": handoff},
        "metadata": identity,
    }


def validate(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if value.get("contract") == "TaskSpecA2AArtifact/v1":
        try: embedded = value["parts"][0]["data"]
        except (KeyError, IndexError, TypeError): return ["A2A artifact has no embedded handoff"]
    elif value.get("contract") == "TaskSpecMCPTask/v1":
        try: embedded = value["task"]["input"]
        except (KeyError, TypeError): return ["MCP task has no embedded handoff"]
    else: return ["unsupported bridge contract"]
    metadata = value.get("metadata", {})
    for field in ("task_id", "spec_digest"):
        if metadata.get(field) != embedded.get(field): errors.append(f"round-trip {field} mismatch")
    if embedded.get("contract") not in {"TaskHandoff/v1", "TaskHandoff/v2"}: errors.append("embedded handoff contract is invalid")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest="command", required=True)
    emit = sub.add_parser("export"); emit.add_argument("handoff"); emit.add_argument("--protocol", choices=["a2a", "mcp"], required=True); emit.add_argument("--out")
    check = sub.add_parser("validate"); check.add_argument("artifact")
    args = parser.parse_args()
    try:
        if args.command == "export":
            value = export(load(pathlib.Path(args.handoff)), args.protocol)
            rendered = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
            if args.out: pathlib.Path(args.out).write_text(rendered, encoding="utf-8")
            else: print(rendered, end="")
        else:
            value = json.loads(pathlib.Path(args.artifact).read_text(encoding="utf-8")); errors = validate(value)
            if errors: raise ValueError("; ".join(errors))
            print(f"BRIDGE=VALID contract={value['contract']}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"BRIDGE=INVALID error={exc}", file=sys.stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())
