#!/usr/bin/env python3
"""Atomically write a complete TaskAuthorization/v3 frontmatter envelope."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
sys.path.insert(0, str(ROOT / "src" / "security"))
from taskspec_data import frontmatter  # noqa: E402
from task_revision import revision  # noqa: E402
from update_frontmatter import update  # noqa: E402
from file_lock import DirectoryLock  # noqa: E402


def signing_key(spec: pathlib.Path) -> str | None:
    configured = os.environ.get("TASKSPEC_SIGNING_KEY")
    if configured:
        candidate = pathlib.Path(configured)
        raw = candidate.read_text(encoding="utf-8") if candidate.is_file() else configured
        return raw.strip() or None
    for flag in ("--git-common-dir", "--git-dir"):
        result = subprocess.run(["git", "rev-parse", flag], cwd=spec.parent, text=True, capture_output=True, check=False)
        if result.returncode: continue
        directory = pathlib.Path(result.stdout.strip())
        if not directory.is_absolute(): directory = (spec.parent / directory).resolve()
        candidate = directory / "info" / "taskspec-signing-key"
        if candidate.is_file(): return candidate.read_text(encoding="utf-8").strip() or None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec"); parser.add_argument("--by", required=True); parser.add_argument("--at", required=True); parser.add_argument("--backlog", required=True)
    args = parser.parse_args()
    spec, backlog = pathlib.Path(args.spec).resolve(), pathlib.Path(args.backlog).resolve()
    try:
        current = frontmatter(spec.read_text(encoding="utf-8"))
        task_rev = revision(spec)["task_revision_digest"]
        payload = (
            f"contract=TaskAuthorization/v3\ntask_revision_digest={task_rev}\n"
            f"signed_off=true\nsigned_off_by={args.by}\nsigned_off_at={args.at}"
        ).encode("utf-8")
        key = signing_key(spec)
        fields = {"signed_off": True, "signed_off_by": args.by, "signed_off_at": args.at}
        signature = None
        if key:
            digest = hmac.new(key.encode("utf-8"), payload, hashlib.sha256).hexdigest()
            key_id = hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]
            signature = f"hmac-sha256-v3:{key_id}:{digest}"
            fields["signed_off_sig"] = signature
        lock = backlog / ".state.lock.d"
        backlog.mkdir(parents=True, exist_ok=True)
        with DirectoryLock(lock):
            # Retire an older signature in the same replacement when the new
            # authorization is structural-only.
            update(spec, fields, {"signed_off_sig"} if not key and "signed_off_sig" in current else set())
        print(json.dumps({"contract": "TaskAuthorization/v3", "tier": 1 if signature else 2, "signature": signature}))
        return 0
    except (OSError, ValueError) as exc:
        print(f"STAMP=FAILED error={exc}", file=sys.stderr); return 1


if __name__ == "__main__": raise SystemExit(main())
