#!/usr/bin/env python3
"""Resolve one task by ID or path using the shared recursive graph universe."""

from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
sys.path.insert(0, str(ROOT / "src" / "graph"))
from taskspec_data import DataError  # noqa: E402
from task_graph import resolve_task  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target")
    parser.add_argument("--backlog", default="tasks")
    args = parser.parse_args()
    try:
        print(resolve_task(pathlib.Path(args.backlog).resolve(), args.target))
        return 0
    except (OSError, DataError, ValueError) as exc:
        print(f"TASK_RESOLUTION=INVALID error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
