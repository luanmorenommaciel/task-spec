#!/usr/bin/env python3
"""Print the stable machine-facing Task-Spec CLI contract."""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

commands = {
    "init": {"mutation": "creates missing tasks/ and .taskspec/config", "tokens": ["INIT=OK", "INIT=DRY_RUN"]},
    "setup": {"mutation": "none", "tokens": ["SETUP=READY"]},
    "setup signing": {"mutation": "creates or explicitly rotates the repository-private HMAC key", "tokens": []},
    "new": {"mutation": "creates one Task-Spec scaffold and derived state", "tokens": []},
    "plan": {"mutation": "none", "tokens": ["TASK_PLAN=OK", "TASK_PLAN=INVALID"]},
    "batch": {"mutation": "creates declared Task-Spec scaffolds; --dry-run writes nothing", "tokens": ["TASK_BATCH=OK", "TASK_BATCH=DRY_RUN", "TASK_BATCH=REFUSED"]},
    "validate": {"mutation": "refreshes deterministic derived state unless --no-state", "tokens": []},
    "dod": {"mutation": "none", "tokens": ["DOD=COMPLETE", "DOD=GAPS"]},
    "gate": {"mutation": "--stamp writes the sign-off envelope; otherwise none", "tokens": ["TIER=1", "TIER=2"]},
    "handoff": {"mutation": "none", "tokens": ["HANDOFF=INVALID", "HANDOFF=REFUSED"]},
    "run": {"mutation": "runs declared eval commands in the task workspace", "tokens": []},
    "accept": {"mutation": "--stamp writes accepted fields; otherwise none", "tokens": ["ACCEPTED=1", "ACCEPTED=0"]},
    "ready": {"mutation": "none", "tokens": []},
    "lint": {"mutation": "none", "tokens": []},
    "transition": {"mutation": "changes lifecycle status and derived state", "tokens": []},
    "rebuild-state": {"mutation": "rewrites deterministic tasks/_state.yaml", "tokens": []},
    "conformance": {"mutation": "self-test uses disposable fixtures only", "tokens": []},
}

contract = {
    "contract": "TaskSpecAgentContext/v1",
    "engine_version": VERSION,
    "format_version": 3,
    "binary": "taskspec",
    "global_options": {
        "--json": "wrap command stdout/stderr and exit status in one JSON envelope",
        "--dry-run": "prevent supported mutations and report intended action",
        "NO_COLOR": "disable ANSI color when present",
        "TASKSPEC_COLOR": "0 disables and 1 forces ANSI color",
    },
    "exit_codes": {"0": "success", "1": "validation, gate, eval, or acceptance failure", "2": "usage error", "3": "unsupported runtime requirement"},
    "commands": commands,
    "contracts": {
        "task_spec": "spec/schemas/task-spec-frontmatter.schema.json",
        "task_plan": "spec/schemas/task-plan.schema.json",
        "task_handoff": "spec/schemas/task-handoff.schema.json",
        "authoring_evidence": "spec/schemas/authoring-evidence.schema.json",
    },
    "credentials": "TaskHandoff and AgentContext never contain credentials; provider and model credentials remain external to core.",
}

print(json.dumps(contract, indent=2, ensure_ascii=False))
