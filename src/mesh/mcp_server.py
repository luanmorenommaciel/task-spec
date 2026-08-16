#!/usr/bin/env python3
"""Stateless local MCP facade for a durable repository TaskMesh daemon."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[2]
PROTOCOL = "2026-07-28"
LEGACY_PROTOCOL = "2025-06-18"
PROTOCOL_KEY = "io.modelcontextprotocol/protocolVersion"
CLIENT_INFO_KEY = "io.modelcontextprotocol/clientInfo"
CLIENT_CAPABILITIES_KEY = "io.modelcontextprotocol/clientCapabilities"


def schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"type": "object", "additionalProperties": False, "properties": properties}
    if required:
        value["required"] = required
    return value


DRY_RUN = {"dry_run": {"type": "boolean", "default": False}}
TOOLS = [
    {"name": "taskmesh.frontier", "description": "Read the authorized ready frontier", "inputSchema": schema({}), "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}},
    {"name": "taskmesh.explain_route", "description": "Explain the deterministic eligible executor route for one task", "inputSchema": schema({"task_id": {"type": "string"}, "adapter": {"type": "string"}}, ["task_id"]), "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}},
    {"name": "taskmesh.start_run", "description": "Start a supervised or explicitly verified autonomous run", "inputSchema": schema({"task_id": {"type": "string"}, "frontier": {"type": "boolean"}, "mode": {"enum": ["supervised", "autonomous"]}, "adapter": {"type": "string"}, "provider": {"type": "string"}, "model": {"type": "string"}, "max_parallel": {"type": "integer", "minimum": 1}, "execute": {"type": "boolean"}, **DRY_RUN}), "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}},
    {"name": "taskmesh.get_run", "description": "Read a durable run or attempt view with its ordered event history", "inputSchema": schema({"id": {"type": "string"}}, ["id"]), "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}},
    {"name": "taskmesh.cancel_attempt", "description": "Cancel and fence one authoritative attempt", "inputSchema": schema({"attempt_id": {"type": "string"}, **DRY_RUN}, ["attempt_id"]), "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}},
    {"name": "taskmesh.accept_attempt", "description": "Explicitly supervise and invoke canonical Task-Spec acceptance", "inputSchema": schema({"attempt_id": {"type": "string"}, "supervised_by": {"type": "string"}, "reason": {"type": "string"}, **DRY_RUN}, ["attempt_id", "supervised_by", "reason"]), "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}},
    {"name": "taskmesh.finish_run", "description": "Freeze a completed run and return the human merge route without mutating the target", "inputSchema": schema({"run_id": {"type": "string"}, **DRY_RUN}, ["run_id"]), "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}},
]


def metadata_error(request: dict[str, Any]) -> str | None:
    params = request.get("params")
    if not isinstance(params, dict):
        return "MCP 2026-07-28 requests require params._meta"
    metadata = params.get("_meta")
    if not isinstance(metadata, dict):
        return "MCP 2026-07-28 requests require params._meta"
    missing = [key for key in (PROTOCOL_KEY, CLIENT_INFO_KEY, CLIENT_CAPABILITIES_KEY) if key not in metadata]
    if missing:
        return "modern request is missing required _meta: " + ", ".join(missing)
    if metadata[PROTOCOL_KEY] != PROTOCOL:
        return "unsupported protocol version " + str(metadata[PROTOCOL_KEY])
    if not isinstance(metadata[CLIENT_INFO_KEY], dict) or not isinstance(metadata[CLIENT_CAPABILITIES_KEY], dict):
        return "modern clientInfo and clientCapabilities must be objects"
    return None


def rpc_error(ident: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": ident, "error": error}


def mesh(arguments: list[str], *, dry_run: bool = False) -> dict[str, Any]:
    command = [str(ROOT / "bin" / "taskspec"), "--json"]
    if dry_run:
        command.append("--dry-run")
    command.extend(["mesh", *arguments])
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    try:
        outer = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"contract": "TaskMeshMCPInvocation/v1", "ok": False, "code": "MESH_API_INVALID", "message": (completed.stdout + completed.stderr).strip()}
    result = outer.get("data") if isinstance(outer, dict) else None
    if isinstance(result, dict):
        return result
    return {"contract": "TaskMeshMCPInvocation/v1", "ok": False, "code": "MESH_API_INVALID", "message": outer.get("stderr", "TaskMesh returned no typed data") if isinstance(outer, dict) else "TaskMesh returned no typed data"}


def tool_arguments(name: str, arguments: dict[str, Any]) -> list[str]:
    if name == "taskmesh.frontier":
        return ["frontier"]
    if name == "taskmesh.explain_route":
        result = ["explain", "--task", arguments["task_id"]]
        if arguments.get("adapter"):
            result.extend(["--adapter", arguments["adapter"]])
        return result
    if name == "taskmesh.start_run":
        result = ["run"]
        if arguments.get("task_id"):
            result.extend(["--task", arguments["task_id"]])
        elif arguments.get("frontier"):
            result.append("--frontier")
        else:
            raise ValueError("start_run requires task_id or frontier=true")
        for field, flag in (("mode", "--mode"), ("adapter", "--adapter"), ("provider", "--provider"), ("model", "--model"), ("max_parallel", "--max-parallel")):
            if arguments.get(field) is not None:
                result.extend([flag, str(arguments[field])])
        if arguments.get("execute"):
            result.append("--execute")
        return result
    if name == "taskmesh.get_run":
        return ["status", arguments["id"]]
    if name == "taskmesh.cancel_attempt":
        return ["cancel", arguments["attempt_id"]]
    if name == "taskmesh.accept_attempt":
        return ["accept", arguments["attempt_id"], "--supervised-by", arguments["supervised_by"], "--reason", arguments["reason"]]
    if name == "taskmesh.finish_run":
        return ["finish", arguments["run_id"]]
    raise ValueError("unknown TaskMesh MCP tool " + name)


def invoke_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    result = mesh(tool_arguments(name, arguments), dry_run=bool(arguments.get("dry_run")))
    if name == "taskmesh.get_run" and result.get("ok") is True:
        data = result.get("data", {})
        run = data.get("run", {}) if isinstance(data, dict) else {}
        run_id = run.get("run_id")
        if run_id:
            history = mesh(["watch", run_id])
            result = dict(result)
            result["history"] = history.get("data") if isinstance(history, dict) else history
    return result


def repository_resources() -> list[dict[str, Any]]:
    status = mesh(["status"])
    resources = [{"uri": "taskmesh://repository", "name": "TaskMesh repository view", "mimeType": "application/json"}]
    data = status.get("data", {}) if isinstance(status, dict) else {}
    seen: set[str] = set()
    for event in data.get("events", []) if isinstance(data, dict) else []:
        run_id = event.get("run_id")
        if run_id and run_id not in seen:
            seen.add(run_id)
            resources.append({"uri": f"taskmesh://run/{run_id}", "name": f"TaskMesh run {run_id}", "mimeType": "application/json"})
    return resources


def read_resource(uri: str) -> dict[str, Any]:
    if uri == "taskmesh://repository":
        value = mesh(["status"])
    elif uri.startswith("taskmesh://run/") or uri.startswith("taskmesh://attempt/"):
        value = mesh(["status", uri.rsplit("/", 1)[-1]])
    else:
        raise ValueError("unknown TaskMesh resource")
    return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(value, indent=2)}], "resultType": "complete"}


def response(request: dict[str, Any]) -> dict[str, Any] | None:
    ident, method = request.get("id"), request.get("method")
    if ident is None:
        return None
    if method == "initialize":
        params = request.get("params", {})
        requested = params.get("protocolVersion", LEGACY_PROTOCOL) if isinstance(params, dict) else LEGACY_PROTOCOL
        if requested != LEGACY_PROTOCOL:
            return rpc_error(ident, -32022, "legacy initialization supports " + LEGACY_PROTOCOL, {"supported": [PROTOCOL, LEGACY_PROTOCOL]})
        result = {"protocolVersion": LEGACY_PROTOCOL, "capabilities": {"tools": {}, "resources": {}}, "serverInfo": {"name": "taskmesh-legacy", "version": (ROOT / "VERSION").read_text().strip()}}
        return {"jsonrpc": "2.0", "id": ident, "result": result}
    error = metadata_error(request)
    if error:
        code = -32022 if error.startswith("unsupported protocol") else -32602
        return rpc_error(ident, code, error, {"supported": [PROTOCOL]} if code == -32022 else None)
    if method == "server/discover":
        result = {"supportedVersions": [PROTOCOL], "capabilities": {"tools": {"listChanged": False}, "resources": {"listChanged": False}}, "instructions": "TaskMesh is a local durable cockpit. Task-Spec remains the only acceptance authority.", "ttlMs": 300000, "cacheScope": "private", "resultType": "complete"}
    elif method == "tools/list":
        result = {"tools": TOOLS, "ttlMs": 300000, "cacheScope": "private", "resultType": "complete"}
    elif method == "tools/call":
        params = request.get("params", {})
        try:
            value = invoke_tool(params.get("name", ""), params.get("arguments", {}))
            result = {"content": [{"type": "text", "text": json.dumps(value, indent=2)}], "structuredContent": value, "isError": value.get("ok") is False, "resultType": "complete"}
        except (KeyError, TypeError, ValueError) as exc:
            return rpc_error(ident, -32602, str(exc))
    elif method == "resources/list":
        result = {"resources": repository_resources(), "resultType": "complete"}
    elif method == "resources/read":
        try:
            result = read_resource(request.get("params", {}).get("uri", ""))
        except ValueError as exc:
            return rpc_error(ident, -32602, str(exc))
    else:
        return rpc_error(ident, -32601, "Method not found")
    return {"jsonrpc": "2.0", "id": ident, "result": result}


def main() -> int:
    for line in sys.stdin:
        try:
            request = json.loads(line)
            result = response(request)
            if result is not None:
                print(json.dumps(result, ensure_ascii=False), flush=True)
        except json.JSONDecodeError as exc:
            print(json.dumps(rpc_error(None, -32700, str(exc))), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
