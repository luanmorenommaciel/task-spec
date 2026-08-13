#!/usr/bin/env python3
"""Atomically replace several top-level frontmatter scalars in one operation."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from typing import Any


def scalar(value: Any) -> str:
    if isinstance(value, bool): return "true" if value else "false"
    if value is None: return "null"
    if isinstance(value, (int, float)): return str(value)
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=isinstance(value, dict), separators=(",", ":"))
    text = str(value)
    if text and text.strip() == text and not re.search(r'[\n\r\t]', text) and not re.search(r'(^[-?:,\[\]{}#&*!|>\'"%@`]|: | #)', text) and text.lower() not in {"true", "false", "null", "yes", "no"}:
        return text
    return json.dumps(text, ensure_ascii=False)


def update(path: pathlib.Path, assignments: dict[str, Any], removals: set[str] | None = None) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("no valid YAML frontmatter")
    end = text.index("\n---\n", 4)
    lines = text[4:end].splitlines()
    remaining = dict(assignments)
    removals = removals or set()
    output: list[str] = []
    for line in lines:
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):", line)
        if match and match.group(1) in removals:
            continue
        if match and match.group(1) in remaining:
            key = match.group(1); output.append(f"{key}: {scalar(remaining.pop(key))}")
        else:
            output.append(line)
    output.extend(f"{key}: {scalar(value)}" for key, value in remaining.items())
    rendered = "---\n" + "\n".join(output) + text[end:]
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        temporary.write_text(rendered, encoding="utf-8")
        if os.environ.get("TASKSPEC_TEST_CRASH_BEFORE_FRONTMATTER_REPLACE") == "1":
            raise RuntimeError("injected crash before frontmatter replacement")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file")
    parser.add_argument("--set-json", required=True)
    parser.add_argument("--remove", action="append", default=[])
    args = parser.parse_args()
    try:
        assignments = json.loads(args.set_json)
        if not isinstance(assignments, dict) or not assignments:
            raise ValueError("--set-json must be a non-empty JSON object")
        update(pathlib.Path(args.file), assignments, set(args.remove))
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"FRONTMATTER_UPDATE=FAILED error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
