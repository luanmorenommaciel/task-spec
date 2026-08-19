#!/usr/bin/env python3
"""Stable TaskMesh CLI shim for the optional taskspec-meshd helper."""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
from typing import NoReturn


ROOT = pathlib.Path(__file__).resolve().parents[2]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
API = "TaskMeshAPI/v1alpha1"

USAGE = """taskspec mesh — optional portable execution control plane

Usage: taskspec mesh <command> [args...]

Repository:
  init
  doctor
  serve --foreground
  frontier [--json]

Runs:
  run --task <id> [--adapter <name>] [--mode supervised|autonomous] [--model <id>] [--execute]
  run --frontier [--max-parallel <n>] [--mode supervised|autonomous] [--execute]
    autonomous requires --provider <id> --model <id> and verified sandbox setup
    supervised may take --model; otherwise tasks/.mesh/roster.json names one
  status [<run-or-attempt>] [--json]
  watch <run> [--after <sequence>]
  explain --task <id>
    prints adapter + named model from flags or the effort/kind roster
  cancel <attempt>
  resume <run-or-attempt> [--execute]
  accept <attempt> --supervised-by <identity> --reason <text>
  finish <run>

Adapters and isolation:
  adapters list
  adapters probe [<name>]
  setup sandbox
  mcp

TaskMesh is optional. Install the matching private release with:
  install.sh --with-mesh
"""

COMMANDS = {
    "init", "doctor", "serve", "frontier", "run", "status", "watch",
    "explain", "cancel", "resume", "accept", "finish", "adapters", "setup", "mcp",
}
MUTATING = {"init", "serve", "run", "cancel", "resume", "accept", "finish", "setup"}


def json_mode() -> bool:
    return os.environ.get("TASKSPEC_JSON_MODE") == "1"


def emit_error(code: str, message: str, exit_code: int, *, next_command: str | None = None) -> NoReturn:
    payload = {
        "contract": "TaskMeshError/v1",
        "api": API,
        "code": code,
        "message": message,
        "next_command": next_command,
    }
    if json_mode():
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"TASKMESH_ERROR={code}: {message}", file=sys.stderr)
        if next_command:
            print(f"NEXT={next_command}", file=sys.stderr)
    raise SystemExit(exit_code)


def helper_path() -> pathlib.Path | None:
    explicit = os.environ.get("TASKSPEC_MESH_HELPER")
    candidates = []
    if explicit:
        candidates.append(pathlib.Path(explicit).expanduser())
    candidates.extend((ROOT / "libexec" / "taskspec-meshd", ROOT / "bin" / "taskspec-meshd"))
    on_path = shutil.which("taskspec-meshd")
    if on_path:
        candidates.append(pathlib.Path(on_path))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    return None


def repository_root() -> pathlib.Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        emit_error("MESH_REPOSITORY_NOT_FOUND", "TaskMesh requires a Git repository", 3, next_command="git init")
    return pathlib.Path(result.stdout.strip()).resolve()


def negotiate(helper: pathlib.Path) -> dict:
    result = subprocess.run(
        [str(helper), "--version-json"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    try:
        identity = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        identity = None
    if result.returncode != 0 or not isinstance(identity, dict):
        emit_error("MESH_HELPER_INVALID", "taskspec-meshd did not return a valid version handshake", 3)
    if identity.get("contract") != API:
        emit_error(
            "MESH_API_MISMATCH",
            f"helper API {identity.get('contract', '(missing)')} does not match {API}",
            3,
        )
    if identity.get("product_version") != VERSION:
        emit_error(
            "MESH_VERSION_MISMATCH",
            f"Task-Spec {VERSION} cannot use TaskMesh helper {identity.get('product_version', '(missing)')}",
            3,
            next_command="reinstall the matching private Task-Spec release with --with-mesh",
        )
    return identity


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"help", "--help", "-h"}:
        print(USAGE.rstrip())
        return 0
    command = argv[0]
    if command not in COMMANDS:
        emit_error("MESH_USAGE", f"unknown TaskMesh command: {command}", 2, next_command="taskspec mesh --help")
    if os.environ.get("TASKSPEC_DRY_RUN") == "1" and command in MUTATING:
        payload = {
            "contract": "TaskMeshDryRun/v1",
            "api": API,
            "command": command,
            "arguments": argv[1:],
            "would_mutate": True,
        }
        if json_mode():
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"TASKMESH_DRY_RUN: would run taskspec mesh {' '.join(argv)}")
        return 0

    helper = helper_path()
    if helper is None:
        emit_error(
            "MESH_NOT_INSTALLED",
            "the optional taskspec-meshd helper is not installed",
            3,
            next_command="install.sh --with-mesh",
        )
    negotiate(helper)
    if command == "mcp":
        os.environ["TASKSPEC_MESH_HELPER"] = str(helper)
        os.execv(sys.executable, [sys.executable, str(ROOT / "src" / "meshctl" / "mcp_server.py")])
    invocation = [str(helper), "--repository", str(repository_root())]
    if json_mode():
        invocation.append("--json")
    invocation.extend(argv)
    return subprocess.run(invocation, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
