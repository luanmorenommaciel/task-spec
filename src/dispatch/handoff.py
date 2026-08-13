#!/usr/bin/env python3
"""Emit credential-free, attempt-bound TaskHandoff/v3 contracts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import pathlib
import re
import subprocess
import sys
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
sys.path.insert(0, str(ROOT / "src" / "security"))
sys.path.insert(0, str(ROOT / "src" / "graph"))
from taskspec_data import DataError, frontmatter, parse_yaml_subset, sensitive_key_paths, sha256_file  # noqa: E402
from task_revision import revision  # noqa: E402
from task_graph import active_write_conflicts, build as build_graph, dependency_closure  # noqa: E402


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


def backlog_for(spec: pathlib.Path) -> pathlib.Path:
    configured = os.environ.get("TASKSPEC_BACKLOG_DIR")
    if configured:
        candidate = pathlib.Path(configured).resolve()
        try:
            spec.relative_to(candidate)
            return candidate
        except ValueError:
            pass
    for parent in spec.parents:
        if parent.name == "tasks":
            return parent
    raise DataError("spec is not inside a tasks backlog")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_head(workspace: pathlib.Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(workspace), text=True, capture_output=True, check=False
    )
    value = completed.stdout.strip()
    if completed.returncode or not re.fullmatch(r"[0-9a-f]{40,64}", value):
        raise DataError("TaskHandoff/v3 requires a Git workspace with a committed HEAD")
    return value


def write_non_clobbering(path: pathlib.Path, value: str, force: bool) -> None:
    if path.exists() and not force:
        raise DataError(f"refusing to overwrite {path}; pass --force")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        temporary.write_text(value, encoding="utf-8")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec")
    parser.add_argument("--backend", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--attempt-id")
    parser.add_argument("--out")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--legacy-version", choices=("1", "2"))
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
    credential_paths = sensitive_key_paths({"frontmatter": fm, "agent_contract": card.get("agent_contract", {})})
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
    format_version = int(str(fm.get("format_version", 0)).split(".")[0])
    task_rev = revision(spec)
    authorization_ref = str(fm.get("signed_off_sig", ""))
    attempt_id = args.attempt_id or str(uuid.uuid4())
    try:
        uuid.UUID(attempt_id)
    except ValueError:
        print("HANDOFF=INVALID\nerror: --attempt-id must be a UUID", file=sys.stderr)
        return 2
    workspace = workspace_for(spec).resolve()
    try:
        source_commit = git_head(workspace)
        graph = build_graph(backlog_for(spec))
        graph_errors = [issue for issue in graph["issues"] if issue.get("severity") == "error"]
        if graph_errors:
            raise DataError(f"backlog graph is invalid: {graph_errors[0]['code']}")
        active_conflicts = active_write_conflicts(graph, str(fm.get("id")))
        if active_conflicts:
            other = active_conflicts[0]["to"] if active_conflicts[0]["from"] == fm.get("id") else active_conflicts[0]["from"]
            raise DataError(f"write scope conflicts with in-progress task {other}")
        closure = dependency_closure(graph, str(fm.get("id")))
    except DataError as exc:
        print(f"HANDOFF=INVALID\nerror: {exc}", file=sys.stderr)
        return 1

    if args.legacy_version:
        if args.legacy_version == "1" and format_version >= 4:
            print("HANDOFF=REFUSED\nerror: TaskHandoff/v1 cannot carry required format-v4 evidence policy", file=sys.stderr)
            return 1
        legacy = {
            "contract": f"TaskHandoff/v{args.legacy_version}",
            "task_id": fm.get("id"),
            "spec": absolute,
            "spec_digest": sha256_file(spec),
            "signoff_tier": tier,
            "backend": args.backend,
            "workspace": str(workspace),
            "write_scope": {"touches_paths": fm.get("touches_paths", []), "creates_paths": fm.get("creates_paths", []), "do_not_touch": do_not_touch},
            "budgets": {"iterations": fm.get("budget_iterations"), "tokens": fm.get("budget_tokens"), "effort": fm.get("effort")},
            "agent_contract": card.get("agent_contract", {}),
            "eval_command": ["taskspec", "run", "--ci", absolute],
            "acceptance_command": ["taskspec", "accept", "--stamp", absolute],
        }
        if args.legacy_version == "2":
            legacy.update({
                "format_version": format_version,
                "evaluation_policy": fm.get("evaluation_policy", {}),
                "environment_contract": fm.get("environment_contract", {}),
                "identity_policy": fm.get("identity_policy", {}),
                "receipt_requirements": ["deterministic"],
            })
        rendered = json.dumps(legacy, indent=2, ensure_ascii=False) + "\n"
        if args.out:
            try:
                write_non_clobbering(pathlib.Path(args.out), rendered, args.force)
            except (OSError, DataError) as exc:
                print(f"HANDOFF=INVALID\nerror: {exc}", file=sys.stderr); return 1
            print(f"HANDOFF=WRITTEN contract={legacy['contract']} path={args.out}")
        else:
            print(rendered, end="")
        return 0

    handoff = {
        "contract": "TaskHandoff/v3",
        "task_id": fm.get("id"),
        "format_version": format_version,
        "spec": absolute,
        "spec_digest": f"sha256:{sha256_file(spec)}",
        "task_revision_digest": task_rev["task_revision_digest"],
        "signoff_tier": tier,
        "backend": args.backend,
        "workspace": str(workspace),
        "authorization": {
            "scheme": authorization_ref.split(":", 1)[0] if ":" in authorization_ref else "structural",
            "ref": authorization_ref,
            "tier": tier,
            "signed_by": fm.get("signed_off_by"),
            "signed_at": fm.get("signed_off_at"),
        },
        "attempt": {"id": attempt_id, "issued_at": now()},
        "source": {"workspace": str(workspace), "base_commit": source_commit},
        "dependency_closure": closure,
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
        "acceptance_command": ["taskspec", "accept", "--stamp", "--handoff", "<handoff.json>", absolute],
        "evaluation_policy": fm.get("evaluation_policy", {}) if format_version >= 4 else {},
        "environment_contract": fm.get("environment_contract", {}) if format_version >= 4 else {},
        "identity_policy": fm.get("identity_policy", {}) if format_version >= 4 else {},
        "receipt_requirements": ["deterministic"],
    }
    if format_version >= 4:
        policy = fm.get("evaluation_policy", {})
        requirements = ["deterministic"]
        for name, contract in (
            ("holdout", "EvaluationReceipt/v2"), ("graded", "GradedEvaluationReceipt/v2"),
            ("human", "HumanAcceptanceReceipt/v2"),
        ):
            if isinstance(policy.get(name), dict) and policy[name].get("required") is True:
                requirements.append(contract)
        if isinstance(fm.get("environment_contract"), dict) and fm["environment_contract"].get("required") is True:
            requirements.append("EnvironmentReceipt/v2")
        if isinstance(fm.get("identity_policy"), dict) and fm["identity_policy"].get("required") is True:
            requirements.append("AuthorizationReceipt/v1")
        handoff["receipt_requirements"] = requirements
    rendered = json.dumps(handoff, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        try:
            write_non_clobbering(pathlib.Path(args.out), rendered, args.force)
        except (OSError, DataError) as exc:
            print(f"HANDOFF=INVALID\nerror: {exc}", file=sys.stderr)
            return 1
        print(f"HANDOFF=WRITTEN contract=TaskHandoff/v3 path={args.out} attempt_id={attempt_id}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
