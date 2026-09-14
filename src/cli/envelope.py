#!/usr/bin/env python3
"""Capture machine output in memory, including inside read-only harness sandboxes."""
import json
import pathlib
import sys
import os
import subprocess

cli = pathlib.Path(sys.argv[1])
version = (cli.parent.parent / "VERSION").read_text().strip()
arguments = sys.argv[2:]
command = arguments[0] if arguments else "help"
environment = dict(os.environ, TASKSPEC_JSON_CHILD="1")
options = ["--json"] + (["--dry-run"] if environment.get("TASKSPEC_DRY_RUN") == "1" else [])
try:
    result = subprocess.run(["bash", str(cli), *options, *arguments], env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace", check=False)
    code, stdout, stderr = result.returncode, result.stdout, result.stderr
except KeyboardInterrupt:
    code, stdout, stderr = 130, "", "cancelled"
if code < 0: code = 128 - code

data = None
try:
    data = json.loads(stdout)
except (json.JSONDecodeError, ValueError):
    pass
if command == "accept" and data is None:
    import re
    if code == 0:
        tier = re.search(r"VERDICT: ACCEPT.*?Tier ([12])", stdout)
        data = {"contract": "AcceptanceResult/v1", "accepted": True, "tier": int(tier.group(1)) if tier else None}
    else:
        failure = re.search(r"ACCEPTANCE_FAILURE=([A-Z_]+)", stdout + "\n" + stderr)
        data = {"contract": "AcceptanceFailure/v1", "accepted": False, "code": failure.group(1) if failure else "POLICY_TAMPER"}
envelope = {
    "contract": "TaskSpecCLIResult/v1",
    "engine_version": version,
    "command": command,
    "ok": code == 0,
    "exit_code": code,
    "data": data,
    "stdout": "" if data is not None else stdout,
    "stderr": stderr,
}
print(json.dumps(envelope, indent=2, ensure_ascii=False))
raise SystemExit(code)
