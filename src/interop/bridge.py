#!/usr/bin/env python3
"""Translate TaskHandoff contracts to optional A2A v1.0 and MCP envelopes."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any


def load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("contract") not in {"TaskHandoff/v1", "TaskHandoff/v2", "TaskHandoff/v3"}:
        raise ValueError("input must be TaskHandoff/v1, v2, or v3")
    return value


def handoff_digest(handoff: dict[str, Any]) -> str:
    payload = json.dumps(handoff, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def export(handoff: dict[str, Any], protocol: str, protocol_version: str | None = None) -> dict[str, Any]:
    identity = {
        "task_id": handoff["task_id"], "spec_digest": handoff["spec_digest"],
        "handoff_digest": handoff_digest(handoff),
    }
    if handoff.get("contract") == "TaskHandoff/v3":
        identity.update({
            "task_revision_digest": handoff["task_revision_digest"],
            "authorization_ref": handoff["authorization"]["ref"],
            "attempt_id": handoff["attempt"]["id"],
            "base_commit": handoff["source"]["base_commit"],
        })
    if protocol == "a2a":
        if protocol_version not in {None, "1.0"}:
            raise ValueError("A2A bridge supports protocol version 1.0")
        return {
            "contract": "TaskSpecA2AArtifact/v2", "protocol": {"name": "A2A", "version": "1.0"},
            "artifactId": handoff["task_id"], "name": "task-spec-handoff",
            "parts": [{"kind": "data", "data": handoff}], "metadata": {**identity, "task_state": "submitted"},
        }
    return {
        "contract": "TaskSpecMCPTask/v1", "task": {"id": handoff["task_id"], "status": "working", "input": handoff},
        "metadata": identity,
    }


def validate(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if value.get("contract") in {"TaskSpecA2AArtifact/v1", "TaskSpecA2AArtifact/v2"}:
        if value.get("contract") == "TaskSpecA2AArtifact/v2" and value.get("protocol") != {"name": "A2A", "version": "1.0"}:
            errors.append("A2A protocol negotiation did not preserve version 1.0")
        try: embedded = value["parts"][0]["data"]
        except (KeyError, IndexError, TypeError): return ["A2A artifact has no embedded handoff"]
    elif value.get("contract") == "TaskSpecMCPTask/v1":
        try: embedded = value["task"]["input"]
        except (KeyError, TypeError): return ["MCP task has no embedded handoff"]
    else: return ["unsupported bridge contract"]
    metadata = value.get("metadata", {})
    fields = ["task_id", "spec_digest"]
    if embedded.get("contract") == "TaskHandoff/v3":
        fields.extend(["task_revision_digest", "authorization_ref", "attempt_id", "base_commit"])
    expected = {
        "task_revision_digest": embedded.get("task_revision_digest"),
        "authorization_ref": embedded.get("authorization", {}).get("ref"),
        "attempt_id": embedded.get("attempt", {}).get("id"),
        "base_commit": embedded.get("source", {}).get("base_commit"),
    }
    for field in fields:
        embedded_value = expected.get(field, embedded.get(field))
        if metadata.get(field) != embedded_value: errors.append(f"round-trip {field} mismatch")
    if metadata.get("handoff_digest") != handoff_digest(embedded):
        errors.append("round-trip handoff digest mismatch")
    if embedded.get("contract") not in {"TaskHandoff/v1", "TaskHandoff/v2", "TaskHandoff/v3"}: errors.append("embedded handoff contract is invalid")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest="command", required=True)
    emit = sub.add_parser("export"); emit.add_argument("handoff"); emit.add_argument("--protocol", choices=["a2a", "mcp"], required=True); emit.add_argument("--protocol-version"); emit.add_argument("--out")
    check = sub.add_parser("validate"); check.add_argument("artifact")
    args = parser.parse_args()
    try:
        if args.command == "export":
            value = export(load(pathlib.Path(args.handoff)), args.protocol, args.protocol_version)
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
