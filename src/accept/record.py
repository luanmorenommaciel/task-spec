#!/usr/bin/env python3
"""Validate an AcceptanceRecord/v1 against a task's complete acceptance envelope."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
sys.path.insert(0, str(ROOT / "src" / "security"))
from taskspec_data import DataError, frontmatter, sha256_file  # noqa: E402
from task_revision import revision  # noqa: E402
from workspace import WorkspaceError, resolve_acceptance_root, resolve_workspace  # noqa: E402


def acceptance_root(backlog: pathlib.Path) -> pathlib.Path:
    """Return the configured projection root without changing canonical task state."""
    workspace = resolve_workspace(backlog.resolve())
    return resolve_acceptance_root(workspace)


def record_path(backlog: pathlib.Path, task_id: str, attempt_id: str) -> pathlib.Path:
    return acceptance_root(backlog) / task_id / f"{attempt_id}.json"


def _object(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataError(f"cannot read AcceptanceRecord: {exc}") from exc
    if not isinstance(value, dict):
        raise DataError("AcceptanceRecord must be a JSON object")
    return value


def verify(spec: pathlib.Path, backlog: pathlib.Path, path: pathlib.Path | None = None) -> dict[str, Any]:
    """Fail closed unless the record and frontmatter describe one identical acceptance."""
    spec = spec.resolve()
    fm = frontmatter(spec.read_text(encoding="utf-8"))
    task_id = str(fm.get("id", ""))
    attempt_id = str(fm.get("accepted_attempt_id", ""))
    if fm.get("accepted") is not True or not task_id or not attempt_id:
        raise DataError("task does not contain a complete accepted subject")
    path = path.resolve() if path else record_path(backlog.resolve(), task_id, attempt_id)
    value = _object(path)
    if value.get("contract") != "AcceptanceRecord/v1":
        raise DataError("record contract must be AcceptanceRecord/v1")
    subject = value.get("subject")
    if not isinstance(subject, dict):
        raise DataError("record subject must be an object")
    expected = {
        "task_id": task_id,
        "task_revision_digest": revision(spec)["task_revision_digest"],
        "authorization_ref": fm.get("accepted_authorization_ref"),
        "attempt_id": attempt_id,
    }
    for key, wanted in expected.items():
        if subject.get(key) != wanted:
            raise DataError(f"record subject {key} does not match accepted task envelope")
    if subject.get("authorization_ref") != fm.get("signed_off_sig"):
        raise DataError("accepted authorization no longer matches the task authorization")
    if value.get("acceptance_tier") != fm.get("accepted_tier"):
        raise DataError("record acceptance tier does not match task envelope")
    if value.get("accepted_by") != fm.get("accepted_by"):
        raise DataError("record acceptor does not match task envelope")
    if value.get("accepted_at") != fm.get("accepted_at"):
        raise DataError("record timestamp does not match task envelope")
    outcome = value.get("outcome")
    expected_code = f"ACCEPTED_TIER_{fm.get('accepted_tier')}"
    if outcome != {"status": "accepted", "code": expected_code}:
        raise DataError("record outcome is missing or inconsistent")
    digest = f"sha256:{sha256_file(path)}"
    if fm.get("acceptance_record_digest") != digest:
        raise DataError("record digest does not match task envelope")
    return {"record": value, "path": str(path), "digest": digest}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--backlog", default="tasks")
    parser.add_argument("--record")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(
            pathlib.Path(args.spec), pathlib.Path(args.backlog),
            pathlib.Path(args.record) if args.record else None,
        )
        if args.json:
            print(json.dumps({"contract": "AcceptanceRecordVerification/v1", "ok": True, **result}, indent=2, sort_keys=True))
        else:
            print(f"ACCEPTANCE_RECORD=VALID path={result['path']}")
        return 0
    except (OSError, DataError, WorkspaceError, ValueError) as exc:
        if args.json:
            print(json.dumps({"contract": "AcceptanceRecordVerification/v1", "ok": False, "error": str(exc)}, sort_keys=True))
        else:
            print(f"ACCEPTANCE_RECORD=INVALID error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
