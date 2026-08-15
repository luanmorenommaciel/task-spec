#!/usr/bin/env python3
"""Stateless MCP 2026-07-28 stdio server with explicit legacy compatibility."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODERN_PROTOCOL = "2026-07-28"
LEGACY_PROTOCOL = "2025-06-18"
PROTOCOL_VERSION_KEY = "io.modelcontextprotocol/protocolVersion"
CLIENT_INFO_KEY = "io.modelcontextprotocol/clientInfo"
CLIENT_CAPABILITIES_KEY = "io.modelcontextprotocol/clientCapabilities"
TOOLS = [
    {"name": "taskspec_handoff", "description": "Create an authorized read-only handoff", "inputSchema": {"type": "object", "required": ["spec", "backend"], "properties": {"spec": {"type": "string"}, "backend": {"type": "string"}}}, "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}},
    {"name": "taskspec_validate", "description": "Validate a Task-Spec without changing state", "inputSchema": {"type": "object", "required": ["spec"], "properties": {"spec": {"type": "string"}}}, "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}},
]


def invoke(name: str, args: dict[str, Any]) -> tuple[int, str]:
    if name == "taskspec_validate": argv = [str(ROOT / "bin" / "taskspec"), "validate", "--no-state", args["spec"]]
    elif name == "taskspec_handoff": argv = [str(ROOT / "bin" / "taskspec"), "handoff", args["spec"], "--backend", args["backend"]]
    else: return 1, f"unknown tool {name}"
    result = subprocess.run(argv, text=True, capture_output=True, check=False)
    return result.returncode, result.stdout + result.stderr


def modern_metadata(request: dict[str, Any]) -> tuple[bool, str | None]:
    params = request.get("params")
    if not isinstance(params, dict):
        return False, None
    metadata = params.get("_meta")
    if not isinstance(metadata, dict) or PROTOCOL_VERSION_KEY not in metadata:
        return False, None
    missing = [
        key for key in (PROTOCOL_VERSION_KEY, CLIENT_INFO_KEY, CLIENT_CAPABILITIES_KEY)
        if key not in metadata
    ]
    if missing:
        return True, "modern request is missing required _meta: {}".format(", ".join(missing))
    if metadata[PROTOCOL_VERSION_KEY] != MODERN_PROTOCOL:
        return True, "unsupported protocol version {}".format(metadata[PROTOCOL_VERSION_KEY])
    if not isinstance(metadata[CLIENT_INFO_KEY], dict) or not isinstance(metadata[CLIENT_CAPABILITIES_KEY], dict):
        return True, "modern clientInfo and clientCapabilities must be objects"
    return True, None


def rpc_error(ident: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": ident, "error": error}


def response(request: dict[str, Any]) -> dict[str, Any] | None:
    method, ident = request.get("method"), request.get("id")
    if ident is None: return None
    modern, metadata_error = modern_metadata(request)
    if metadata_error:
        code = -32022 if metadata_error.startswith("unsupported protocol") else -32602
        data = {"supported": [MODERN_PROTOCOL]} if code == -32022 else None
        return rpc_error(ident, code, metadata_error, data)
    if method == "server/discover":
        if not modern:
            return rpc_error(ident, -32602, "server/discover requires the MCP 2026-07-28 request envelope")
        result = {
            "supportedVersions": [MODERN_PROTOCOL],
            "capabilities": {"tools": {"listChanged": False}},
            "instructions": "Read-only Task-Spec validation and handoff inspection.",
            "ttlMs": 300000,
            "cacheScope": "private",
            "resultType": "complete",
        }
    elif method == "initialize":
        params = request.get("params", {})
        requested = params.get("protocolVersion", LEGACY_PROTOCOL) if isinstance(params, dict) else LEGACY_PROTOCOL
        if requested != LEGACY_PROTOCOL:
            return rpc_error(ident, -32022, "legacy initialization supports {}".format(LEGACY_PROTOCOL), {"supported": [MODERN_PROTOCOL, LEGACY_PROTOCOL]})
        result = {"protocolVersion": LEGACY_PROTOCOL, "capabilities": {"tools": {}}, "serverInfo": {"name": "taskspec-legacy", "version": (ROOT / "VERSION").read_text().strip()}}
    elif method == "tools/list":
        result = {"tools": TOOLS, "ttlMs": 300000, "cacheScope": "private", "resultType": "complete"}
    elif method == "tools/call":
        params = request.get("params", {}); code, output = invoke(params.get("name", ""), params.get("arguments", {}))
        result = {"content": [{"type": "text", "text": output}], "isError": code != 0, "resultType": "complete"}
    else: return rpc_error(ident, -32601, "Method not found")
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
