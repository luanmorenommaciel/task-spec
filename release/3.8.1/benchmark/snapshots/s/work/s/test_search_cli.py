#!/usr/bin/env python3
"""Frozen discriminating tests for the S benchmark."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys


CLI = pathlib.Path(__file__).with_name("search_cli.py")


def run(*args: str) -> str:
    return subprocess.check_output([sys.executable, str(CLI), *args], text=True)


assert json.loads(run("task", "--json")) == {
    "query": "task",
    "results": [{"path": "docs/task-spec.md", "score": 1}],
}
assert run("task") == "PATH\tSCORE\ndocs/task-spec.md\t1\n"
assert run("missing") == "No results for: missing\n"
print("SEARCH_CLI=READY")
