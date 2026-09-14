#!/usr/bin/env python3
"""Register read-only toolkit tools on the retained protocol implementation.

The protocol implementation remains byte-identical to its frozen conformance
evidence. This module adds product tools without introducing a second MCP stack.
"""
from pathlib import Path
import re
import subprocess

import mcp_server as protocol

ROOT = Path(__file__).resolve().parents[2]
BASE_INVOKE = protocol.invoke
NATIVE_TOOLS = {
    "taskspec_initiative_status": "Inspect native planning, acceptance, and proof gaps",
    "taskspec_initiative_graph": "Inspect capability structure and leaf provenance",
}


def invoke(name, args):
    if name not in NATIVE_TOOLS:
        return BASE_INVOKE(name, args)
    initiative = args.get("initiative", "") if isinstance(args, dict) else ""
    if not isinstance(initiative, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", initiative):
        return 1, "invalid initiative; use a lowercase initiative identifier"
    command = [str(ROOT / "bin/taskspec"), "--json", "status" if name.endswith("status") else "graph", "--initiative", initiative]
    if name.endswith("graph"):
        command += ["--view", "capabilities"]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    return result.returncode, result.stdout + result.stderr


def main():
    for name, description in NATIVE_TOOLS.items():
        protocol.TOOLS.append({
            "name": name, "description": description,
            "inputSchema": {"type": "object", "required": ["initiative"], "properties": {"initiative": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{0,79}$"}}},
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
        })
    protocol.invoke = invoke
    return protocol.main()


if __name__ == "__main__":
    raise SystemExit(main())
