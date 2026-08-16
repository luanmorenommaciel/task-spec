#!/usr/bin/env python3
"""Materialize canonical examples from an installed Task-Spec package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[2]
EXAMPLES = {"task-plan": ROOT / "docs" / "examples" / "task-plan.yaml"}


def result(example: str, target: pathlib.Path, source: pathlib.Path, content: bytes, dry_run: bool, overwritten: bool) -> dict:
    return {
        "contract": "TaskSpecExampleResult/v1",
        "example": example,
        "source": source.relative_to(ROOT).as_posix(),
        "path": str(target),
        "digest": "sha256:" + hashlib.sha256(content).hexdigest(),
        "dry_run": dry_run,
        "written": not dry_run,
        "created": not dry_run and not overwritten,
        "overwritten": overwritten and not dry_run,
    }


def write_atomic(target: pathlib.Path, content: bytes, force: bool) -> bool:
    target.parent.mkdir(parents=True, exist_ok=True)
    existed = target.exists()
    if existed and not force:
        raise FileExistsError("{} already exists; pass --force to replace it".format(target))
    if not force:
        descriptor = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        return False
    descriptor, temporary = tempfile.mkstemp(prefix=".{}.".format(target.name), dir=str(target.parent))
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return existed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example", choices=sorted(EXAMPLES))
    parser.add_argument("--out", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    source = EXAMPLES[args.example]
    target = pathlib.Path(args.out).expanduser().resolve()
    json_mode = os.environ.get("TASKSPEC_JSON_MODE") == "1"
    dry_run = os.environ.get("TASKSPEC_DRY_RUN") == "1"
    try:
        content = source.read_bytes()
        overwritten = target.exists()
        if not dry_run:
            overwritten = write_atomic(target, content, args.force)
        payload = result(args.example, target, source, content, dry_run, overwritten)
        if json_mode:
            print(json.dumps(payload, sort_keys=True))
        elif dry_run:
            print("EXAMPLE=DRY_RUN example={} path={} digest={}".format(args.example, target, payload["digest"]))
        else:
            action = "replaced" if overwritten else "created"
            print("EXAMPLE=WRITTEN example={} path={} action={} digest={}".format(args.example, target, action, payload["digest"]))
        return 0
    except (OSError, ValueError) as exc:
        print("EXAMPLE=REFUSED error={}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
