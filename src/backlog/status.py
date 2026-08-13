#!/usr/bin/env python3
"""Render read-only TaskStatus/v1 from the canonical task, graph, and acceptance evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
sys.path.insert(0, str(ROOT / "src" / "security"))
sys.path.insert(0, str(ROOT / "src" / "graph"))
sys.path.insert(0, str(ROOT / "src" / "accept"))
from taskspec_data import DataError, frontmatter, sha256_file  # noqa: E402
from task_revision import revision  # noqa: E402
from task_graph import build as build_graph, resolve_task  # noqa: E402
from stamp import signing_key  # noqa: E402
from record import record_path as acceptance_record_path, verify as verify_acceptance_record  # noqa: E402


def resolve(backlog: pathlib.Path, target: str) -> pathlib.Path:
    return resolve_task(backlog, target)


def authoring_evidence(backlog: pathlib.Path, fm: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Report evidence age and integrity without turning freshness into acceptance."""
    workspace = backlog.parent.resolve()
    result: list[dict[str, Any]] = []
    problems: list[str] = []
    for index, item in enumerate(fm.get("evidence_refs", []) if isinstance(fm.get("evidence_refs"), list) else []):
        entry: dict[str, Any] = {
            "ref": item.get("ref") if isinstance(item, dict) else None,
            "role": item.get("role") if isinstance(item, dict) else None,
            "available": False,
            "digest_matches": False,
            "observed_at": None,
            "age_sec": None,
        }
        if not isinstance(item, dict) or not isinstance(item.get("ref"), str):
            problems.append(f"authoring evidence ref {index} is malformed")
            result.append(entry)
            continue
        pure = pathlib.PurePosixPath(item["ref"])
        if pure.is_absolute() or ".." in pure.parts:
            problems.append(f"authoring evidence ref {index} is outside the workspace")
            result.append(entry)
            continue
        path = workspace.joinpath(*pure.parts).resolve()
        try:
            path.relative_to(workspace)
            raw = path.read_bytes()
            value = json.loads(raw)
            entry["available"] = True
            entry["digest_matches"] = item.get("digest") == f"sha256:{hashlib.sha256(raw).hexdigest()}"
            entry["observed_at"] = value.get("observed_at") if isinstance(value, dict) else None
            if isinstance(entry["observed_at"], str):
                observed = datetime.fromisoformat(entry["observed_at"].replace("Z", "+00:00"))
                entry["age_sec"] = max(0, int((datetime.now(timezone.utc) - observed).total_seconds()))
        except (OSError, ValueError, json.JSONDecodeError, TypeError):
            pass
        if not entry["available"]:
            problems.append(f"authoring evidence missing: {item['ref']}")
        elif not entry["digest_matches"]:
            problems.append(f"authoring evidence digest mismatch: {item['ref']}")
        result.append(entry)
    return result, problems


def status(backlog: pathlib.Path, spec: pathlib.Path) -> dict[str, Any]:
    fm = frontmatter(spec.read_text(encoding="utf-8"))
    view = build_graph(backlog)
    task_id = str(fm.get("id"))
    node = next((item for item in view["nodes"] if item["task_id"] == task_id), None)
    if not node:
        raise DataError(f"{task_id} is absent from TaskGraphView/v1")
    rev = revision(spec)
    signature = str(fm.get("signed_off_sig", ""))
    scheme = signature.split(":", 1)[0] if ":" in signature else "none"
    verification = "unsigned"
    stale = False
    if scheme == "hmac-sha256-v3":
        key = signing_key(spec)
        if key:
            payload = (
                f"contract=TaskAuthorization/v3\ntask_revision_digest={rev['task_revision_digest']}\n"
                f"signed_off=true\nsigned_off_by={fm.get('signed_off_by')}\nsigned_off_at={fm.get('signed_off_at')}"
            ).encode("utf-8")
            expected = f"hmac-sha256-v3:{hashlib.sha256(key.encode()).hexdigest()[:8]}:{hmac.new(key.encode(), payload, hashlib.sha256).hexdigest()}"
            if hmac.compare_digest(expected, signature):
                tier, verification = 1, "verified"
            else:
                tier, verification, stale = 3, "mismatch", True
        else:
            tier, verification = 2, "key-unavailable"
    elif scheme in {"hmac-sha256-v1", "hmac-sha256-v2"}:
        tier, verification, stale = 2, "authentic-but-narrow", True
    else:
        tier, verification = 3, "unsigned-or-malformed"
    accepted = fm.get("accepted") is True
    acceptance: dict[str, Any] = {"accepted": accepted, "record": None, "record_matches": False, "record_error": None}
    attempt = fm.get("accepted_attempt_id")
    if accepted and attempt:
        record = acceptance_record_path(backlog, task_id, str(attempt))
        acceptance["record"] = str(record)
        try:
            verify_acceptance_record(spec, backlog, record)
            acceptance["record_matches"] = True
        except (OSError, DataError, ValueError) as exc:
            acceptance["record_error"] = str(exc)
    blockers = view["blocked_reasons"].get(task_id, [])
    state = backlog / "_state.yaml"
    projected_graph = None
    if state.is_file():
        for line in state.read_text(encoding="utf-8").splitlines():
            if line.startswith("graph_revision_digest:"):
                projected_graph = line.split(":", 1)[1].strip()
                break
    graph_stale = projected_graph != view["graph_revision_digest"]
    missing_evidence: list[str] = []
    authoring_refs, authoring_problems = authoring_evidence(backlog, fm)
    missing_evidence.extend(authoring_problems)
    policy = fm.get("evaluation_policy") if isinstance(fm.get("evaluation_policy"), dict) else {}
    if not accepted:
        for name in ("holdout", "graded", "human"):
            if isinstance(policy.get(name), dict) and policy[name].get("required") is True:
                missing_evidence.append(f"{name} receipt not yet bound to an accepted attempt")
        environment = fm.get("environment_contract")
        if isinstance(environment, dict) and environment.get("required") is True:
            missing_evidence.append("environment receipt not yet bound to an accepted attempt")
    elif not acceptance["record_matches"]:
        missing_evidence.append("acceptance record missing or digest mismatch")
    if fm.get("signed_off") is not True:
        next_command = f"taskspec gate --stamp {spec}"
    elif tier != 1:
        next_command = f"taskspec gate --stamp {spec}"
    elif graph_stale:
        next_command = "taskspec rebuild-state"
    elif node["effort"] in {"XL", "XXL"}:
        next_command = f"taskspec graph --task {task_id}"
    elif blockers and not (len(blockers) == 1 and blockers[0].startswith("status:")):
        next_command = f"taskspec graph --task {task_id}"
    elif not accepted:
        next_command = f"taskspec handoff {spec} --backend {fm.get('execution_backend', 'any')}"
    elif node["status"] != "done":
        next_command = f"taskspec transition {task_id} done"
    else:
        next_command = f"taskspec status {task_id}"
    return {
        "contract": "TaskStatus/v1",
        "task_id": task_id,
        "path": str(spec),
        "lifecycle": node["status"],
        "authorization": {"scheme": scheme, "tier": tier, "verification": verification, "stale": stale, "task_revision_digest": rev["task_revision_digest"]},
        "graph": {"revision_digest": view["graph_revision_digest"], "projection_digest": projected_graph, "stale": graph_stale, "issues": view["issues"], "blockers": blockers},
        "evidence": {"missing_or_mismatched": missing_evidence, "authoring_refs": authoring_refs},
        "acceptance": acceptance,
        "next_command": next_command,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?")
    parser.add_argument("--backlog", default=os.environ.get("TASKSPEC_BACKLOG_DIR", "tasks"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.target:
        parser.print_usage(sys.stderr)
        return 2
    try:
        backlog = pathlib.Path(args.backlog).resolve()
        result = status(backlog, resolve(backlog, args.target))
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
        else:
            print(f"TASK={result['task_id']} status={result['lifecycle']} authorization=Tier-{result['authorization']['tier']} accepted={str(result['acceptance']['accepted']).lower()}")
            if result["graph"]["blockers"]:
                print("BLOCKED=" + ",".join(result["graph"]["blockers"]))
            print(f"NEXT={result['next_command']}")
        return 0
    except (OSError, DataError, ValueError) as exc:
        print(f"STATUS=INVALID error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
