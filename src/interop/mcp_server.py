#!/usr/bin/env python3
"""Minimal stdio MCP server exposing read-only Task-Spec inspection tools."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOLS = [
    {"name": "taskspec_validate", "description": "Validate a Task-Spec without changing state", "inputSchema": {"type": "object", "required": ["spec"], "properties": {"spec": {"type": "string"}}}},
    {"name": "taskspec_handoff", "description": "Create an authorized read-only handoff", "inputSchema": {"type": "object", "required": ["spec", "backend"], "properties": {"spec": {"type": "string"}, "backend": {"type": "string"}}}},
]


def invoke(name: str, args: dict[str, Any]) -> tuple[int, str]:
    if name == "taskspec_validate": argv = [str(ROOT / "bin" / "taskspec"), "validate", "--no-state", args["spec"]]
    elif name == "taskspec_handoff": argv = [str(ROOT / "bin" / "taskspec"), "handoff", args["spec"], "--backend", args["backend"]]
    else: return 1, f"unknown tool {name}"
    result = subprocess.run(argv, text=True, capture_output=True, check=False)
    return result.returncode, result.stdout + result.stderr


def response(request: dict[str, Any]) -> dict[str, Any] | None:
    method, ident = request.get("method"), request.get("id")
    if ident is None: return None
    if method == "initialize": result = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "taskspec", "version": (ROOT / "VERSION").read_text().strip()}}
    elif method == "tools/list": result = {"tools": TOOLS}
    elif method == "tools/call":
        params = request.get("params", {}); code, output = invoke(params.get("name", ""), params.get("arguments", {}))
        result = {"content": [{"type": "text", "text": output}], "isError": code != 0}
    else: return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32601, "message": "Method not found"}}
    return {"jsonrpc": "2.0", "id": ident, "result": result}


def main() -> int:
    for line in sys.stdin:
        try:
            request = json.loads(line); result = response(request)
            if result is not None: print(json.dumps(result), flush=True)
        except (json.JSONDecodeError, KeyError) as exc:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32602, "message": str(exc)}}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
