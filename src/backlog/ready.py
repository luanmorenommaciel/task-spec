#!/usr/bin/env python3
"""List the dependency-aware TaskGraphView/v1 pickup frontier."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "graph"))
from task_graph import build  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backlog", default=os.environ.get("TASKSPEC_BACKLOG_DIR", "tasks"))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--effort")
    parser.add_argument("--agent")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    view = build(pathlib.Path(args.backlog))
    frontier = set(view["ready_frontier"])
    rows = []
    for node in view["nodes"]:
        if node["status"] != "ready" or node["effort"] in {"XL", "XXL"}:
            continue
        if not args.all and node["task_id"] not in frontier:
            continue
        path = pathlib.Path(args.backlog) / node["path"]
        sys.path.insert(0, str(ROOT / "src" / "lib"))
        from taskspec_data import frontmatter  # noqa: PLC0415
        fm = frontmatter(path.read_text(encoding="utf-8"))
        if args.effort and node["effort"] != args.effort: continue
        if args.agent and fm.get("agent") != args.agent: continue
        rows.append({"task_id": node["task_id"], "effort": node["effort"], "agent": fm.get("agent"), "title": fm.get("title"), "blockers": view["blocked_reasons"].get(node["task_id"], [])})
    if args.json:
        print(json.dumps({"contract": "ReadyFrontier/v1", "tasks": rows}, indent=2, sort_keys=True))
    else:
        print(f"{'ID':32} {'EFFORT':7} {'AGENT':12} TITLE")
        print(f"{'=' * 32} {'=' * 7} {'=' * 12} {'=' * 30}")
        for row in rows: print(f"{row['task_id']:32} {row['effort']:7} {str(row['agent']):12} {row['title']}")
        hidden = sum(1 for node in view["nodes"] if node["status"] == "ready" and node["effort"] not in {"XL", "XXL"} and node["task_id"] not in frontier)
        if hidden and not args.all: print(f"\n({hidden} ready spec(s) hidden — blocked; --all shows them)")
        nodes = sum(1 for node in view["nodes"] if node["status"] == "ready" and node["effort"] in {"XL", "XXL"})
        if nodes: print(f"({nodes} composition node(s) hidden — dispatch their child leaves)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
