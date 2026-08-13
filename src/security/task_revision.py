#!/usr/bin/env python3
"""Canonical TaskRevision/v1 identity for Task-Spec authorization.

The revision digest seals the complete frontmatter by default and excludes only
the explicitly mutable lifecycle/projection fields below.  This is deliberately
the inverse of an allow-list: a future authority-bearing field is protected
without requiring another envelope revision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
from taskspec_data import DataError, canonical_digest, frontmatter  # noqa: E402


CONTRACT = "TaskRevision/v1"
MUTABLE_FIELDS = frozenset(
    {
        "status",
        "blocked_reason",
        "owner",
        "priority",
        "due_date",
        "tags",
        "tracker_ref",
        "linear_ref",
        "projection",
        "signed_off",
        "signed_off_by",
        "signed_off_at",
        "signed_off_sig",
        "accepted",
        "accepted_by",
        "accepted_at",
        "accepted_tier",
        "accepted_attempt_id",
        "accepted_authorization_ref",
        "acceptance_record_digest",
    }
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def spec_body(text: str) -> str:
    """Return the same body bytes as the Bash ts_spec_body helper."""
    if not text.startswith("---\n"):
        raise DataError("Task-Spec has no leading frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise DataError("Task-Spec frontmatter is not closed")
    remainder = text[end + 4 :]
    if remainder.startswith("\n"):
        remainder = remainder[1:]
    # awk `print` in ts_spec_body always terminates every body line.
    return remainder if not remainder or remainder.endswith("\n") else remainder + "\n"


def authority_manifest(fm: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in fm.items() if key not in MUTABLE_FIELDS}


def revision(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    fm = frontmatter(text)
    task_id = fm.get("id")
    if not isinstance(task_id, str) or not task_id:
        raise DataError("Task-Spec frontmatter requires a non-empty id")
    body_digest = hashlib.sha256(spec_body(text).encode("utf-8")).hexdigest()
    manifest = authority_manifest(fm)
    manifest_digest = canonical_digest(manifest)
    payload = f"{CONTRACT}\n{task_id}\n{body_digest}\n{manifest_digest}"
    return {
        "contract": CONTRACT,
        "task_id": task_id,
        "body_digest": f"sha256:{body_digest}",
        "authority_manifest": manifest,
        "authority_manifest_digest": f"sha256:{manifest_digest}",
        "task_revision_digest": f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument(
        "--field",
        choices=("task_revision_digest", "authority_manifest_digest", "body_digest", "task_id"),
    )
    parser.add_argument("--manifest", action="store_true")
    args = parser.parse_args()
    try:
        value = revision(pathlib.Path(args.spec))
        if args.field:
            print(value[args.field])
        elif args.manifest:
            print(canonical_json(value["authority_manifest"]))
        else:
            print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, DataError, UnicodeError) as exc:
        print(f"TASK_REVISION=INVALID error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
