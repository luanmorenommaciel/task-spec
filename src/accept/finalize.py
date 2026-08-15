#!/usr/bin/env python3
"""Atomically persist AcceptanceRecord/v1 and the complete task acceptance envelope."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import pathlib
import sys
import uuid
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
from taskspec_data import DataError, frontmatter, sha256_file  # noqa: E402
from file_lock import DirectoryLock  # noqa: E402
from update_frontmatter import update as update_frontmatter  # noqa: E402
from workspace import WorkspaceError, resolve_acceptance_root, resolve_backlog, resolve_workspace  # noqa: E402


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def atomic_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def append_metric(path: pathlib.Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                current = json.loads(line)
            except json.JSONDecodeError:
                continue
            if current.get("event") == "accepted" and current.get("attempt_id") == event["attempt_id"]:
                return
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--handoff")
    parser.add_argument("--preflight", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--accepted-by", required=True)
    parser.add_argument("--tier", type=int, choices=[1, 2], required=True)
    parser.add_argument("--supervised-by")
    parser.add_argument("--reason")
    parser.add_argument("--verifier-signature")
    parser.add_argument("--receipt", action="append", default=[])
    parser.add_argument("--acceptance-dir")
    args = parser.parse_args()
    try:
        spec = pathlib.Path(args.spec).resolve()
        fm = frontmatter(spec.read_text(encoding="utf-8"))
        preflight, policy = load(pathlib.Path(args.preflight)), load(pathlib.Path(args.policy))
        if not preflight.get("ok") or not policy.get("ok"):
            raise ValueError("cannot finalize a failed acceptance gate")
        handoff = load(pathlib.Path(args.handoff)) if args.handoff else None
        if handoff and handoff.get("contract") == "TaskHandoff/v3":
            attempt_id = str(handoff["attempt"]["id"])
            base_commit = str(handoff["source"]["base_commit"])
        else:
            attempt_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"taskspec:{fm.get('id')}:{fm.get('signed_off_sig')}"))
            base_commit = str(preflight.get("base_commit", "HEAD"))
        workspace = resolve_workspace(spec)
        backlog = resolve_backlog(spec, workspace)
        acceptance_root = resolve_acceptance_root(workspace, args.acceptance_dir)
        record_path = acceptance_root / str(fm.get("id")) / f"{attempt_id}.json"
        accepted_at = now()
        subject = {
            "task_id": str(fm.get("id")),
            "task_revision_digest": str(preflight.get("task_revision_digest")),
            "authorization_ref": str(fm.get("signed_off_sig")),
            "attempt_id": attempt_id,
            "base_commit": base_commit,
        }
        receipts = []
        for raw in args.receipt:
            receipt_path = pathlib.Path(raw).resolve()
            receipts.append({"path": str(receipt_path), "digest": f"sha256:{sha256_file(receipt_path)}"})
        record = {
            "contract": "AcceptanceRecord/v1",
            "subject": subject,
            "outcome": {"status": "accepted", "code": f"ACCEPTED_TIER_{args.tier}"},
            "gate_outcomes": {
                "authorization": {"status": "pass", "code": "AUTHORIZATION_VALID"},
                "evaluation": {"status": "pass", "code": "EVAL_PASSED"},
                "preflight": {"status": "pass", "code": "PREFLIGHT_PASSED", "warnings": preflight.get("warnings", [])},
                "evidence": {"status": "pass", "code": "EVIDENCE_SATISFIED", "proof": policy.get("proof", [])},
            },
            "receipts": receipts,
            "acceptance_tier": args.tier,
            "accepted_by": args.accepted_by,
            "accepted_at": accepted_at,
        }
        if args.tier == 2:
            record["supervision"] = {"supervised_by": args.supervised_by, "reason": args.reason}
        if args.verifier_signature:
            record["verifier_signature"] = args.verifier_signature

        lock_dir = backlog / ".state.lock.d"
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_lock = record_path.parent / f".{attempt_id}.lock.d"
        with DirectoryLock(record_lock):
            if record_path.exists():
                existing = load(record_path)
                immutable_keys = (
                    "subject", "receipts", "acceptance_tier", "accepted_by",
                    "supervision", "verifier_signature", "outcome",
                )
                conflicts = [key for key in immutable_keys if existing.get(key) != record.get(key)]
                if conflicts:
                    raise ValueError(
                        "existing AcceptanceRecord conflicts with this attempt: " + ", ".join(conflicts)
                    )
                record = existing
                accepted_at = str(existing["accepted_at"])
            else:
                atomic_json(record_path, record)
            record_digest = f"sha256:{sha256_file(record_path)}"
        if os.environ.get("TASKSPEC_TEST_CRASH_AFTER_RECORD") == "1":
            raise RuntimeError("injected crash after AcceptanceRecord write")
        with DirectoryLock(lock_dir):
            update_frontmatter(
                spec,
                {
                    "accepted": True,
                    "accepted_by": record["accepted_by"],
                    "accepted_at": accepted_at,
                    "accepted_tier": record["acceptance_tier"],
                    "accepted_attempt_id": attempt_id,
                    "accepted_authorization_ref": record["subject"]["authorization_ref"],
                    "acceptance_record_digest": record_digest,
                },
            )
        try:
            if os.environ.get("TASKSPEC_TEST_FAIL_METRICS") == "1":
                raise OSError("injected metrics projection failure")
            append_metric(
                backlog / "_metrics.jsonl",
                {
                    "schema_version": 1, "ts": accepted_at, "task": fm.get("id"),
                    "event": "accepted", "author": record["accepted_by"],
                    "attempt_id": attempt_id, "acceptance_tier": record["acceptance_tier"],
                    "acceptance_record_digest": record_digest,
                },
            )
        except OSError as exc:
            print(f"WARN metrics projection missing: {exc}", file=sys.stderr)
        print(json.dumps({
            "contract": "AcceptanceFinalized/v1", "accepted": True,
            "task_id": fm.get("id"), "attempt_id": attempt_id,
            "tier": record["acceptance_tier"], "acceptance_record": str(record_path),
            "acceptance_record_digest": record_digest,
        }, sort_keys=True))
        return 0
    except (OSError, ValueError, DataError, WorkspaceError, KeyError, RuntimeError) as exc:
        print(f"ACCEPTANCE_FINALIZE=FAILED error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
