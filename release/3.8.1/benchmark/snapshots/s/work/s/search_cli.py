#!/usr/bin/env python3
"""Intentionally defective local search CLI for the frozen benchmark."""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    matches = [{"path": "docs/task-spec.md", "score": 1}] if args.query == "task" else []
    if args.json:
        print(str({"query": args.query, "results": matches}))
    elif matches:
        print("PATH\tSCORE")
        for match in matches:
            print("{}\t{}".format(match["path"], match["score"]))
    else:
        print("Nothing found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
