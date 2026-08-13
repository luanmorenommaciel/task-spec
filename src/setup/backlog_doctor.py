#!/usr/bin/env python3
"""Audit backlog graph, narrow seals, recovery artifacts, and acceptance projections."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
sys.path.insert(0, str(ROOT / "src" / "graph"))
sys.path.insert(0, str(ROOT / "src" / "accept"))
from taskspec_data import DataError, frontmatter  # noqa: E402
from task_graph import build as build_graph, task_files  # noqa: E402
from record import acceptance_root as configured_acceptance_root, verify as verify_acceptance_record  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backlog", default="tasks")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        backlog = pathlib.Path(args.backlog).resolve()
        view = build_graph(backlog)
        warnings: list[dict[str, str]] = []
        errors: list[dict[str, str]] = []
        tasks: dict[str, pathlib.Path] = {}
        accepted_attempts: set[tuple[str, str]] = set()
        for path in task_files(backlog):
            fm = frontmatter(path.read_text(encoding="utf-8"))
            task_id = str(fm.get("id"))
            tasks[task_id] = path
            signature = str(fm.get("signed_off_sig", ""))
            if signature.startswith(("hmac-sha256-v1:", "hmac-sha256-v2:")):
                warnings.append({
                    "code": "AUTHENTIC_BUT_NARROW", "task_id": task_id,
                    "message": f"restamp exactly: taskspec gate --stamp {path}",
                })
            if fm.get("accepted") is True and fm.get("accepted_attempt_id"):
                accepted_attempts.add((task_id, str(fm["accepted_attempt_id"])))
                try:
                    verify_acceptance_record(path, backlog)
                except (OSError, DataError, ValueError) as exc:
                    errors.append({"code": "ACCEPTANCE_RECORD_MISMATCH", "task_id": task_id, "message": str(exc)})
        for issue in view["issues"]:
            target = errors if issue.get("severity") == "error" else warnings
            target.append({"code": str(issue.get("code")), "task_id": str(issue.get("task_id", "")), "message": json.dumps(issue, sort_keys=True)})
        for temporary in sorted(backlog.rglob(".*.tmp.*")):
            warnings.append({"code": "STALE_TEMPORARY", "task_id": "", "message": str(temporary)})
        acceptance_root = configured_acceptance_root(backlog)
        for temporary in sorted(acceptance_root.rglob(".*.tmp.*")) if acceptance_root.is_dir() else []:
            warnings.append({"code": "STALE_TEMPORARY", "task_id": "", "message": str(temporary)})
        for record in sorted(acceptance_root.glob("T-*/*.json")) if acceptance_root.is_dir() else []:
            try:
                value = json.loads(record.read_text(encoding="utf-8"))
                subject = value.get("subject", {})
                task_id, attempt = subject.get("task_id"), subject.get("attempt_id")
                if task_id not in tasks or (str(task_id), str(attempt)) not in accepted_attempts:
                    warnings.append({"code": "ORPHAN_ACCEPTANCE_RECORD", "task_id": str(task_id), "message": str(record)})
            except (OSError, json.JSONDecodeError):
                errors.append({"code": "INVALID_ACCEPTANCE_RECORD", "task_id": "", "message": str(record)})
        metric_attempts: set[str] = set()
        metrics = backlog / "_metrics.jsonl"
        if metrics.is_file():
            for line in metrics.read_text(encoding="utf-8").splitlines():
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("event") == "accepted" and event.get("attempt_id"):
                    metric_attempts.add(str(event["attempt_id"]))
        accepted_attempt_ids = {attempt for _, attempt in accepted_attempts}
        for attempt in sorted(accepted_attempt_ids - metric_attempts):
            warnings.append({"code": "METRICS_PROJECTION_MISSING", "task_id": "", "message": f"attempt {attempt}"})
        result = {
            "contract": "BacklogDoctor/v1", "ok": not errors,
            "graph_revision_digest": view["graph_revision_digest"],
            "errors": errors, "warnings": warnings,
        }
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
        else:
            for item in errors: print(f"FAIL {item['code']} {item['message']}")
            for item in warnings: print(f"WARN {item['code']} {item['message']}")
            print(f"BACKLOG_DOCTOR={'READY' if not errors else 'BLOCKED'} errors={len(errors)} warnings={len(warnings)}")
        return 0 if not errors else 1
    except (OSError, DataError, ValueError) as exc:
        print(f"BACKLOG_DOCTOR=BLOCKED error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
