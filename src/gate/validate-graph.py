#!/usr/bin/env python3
"""Report derived-graph errors that invalidate one Task-Spec."""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
sys.path.insert(0, str(ROOT / "src" / "graph"))

from taskspec_data import DataError, frontmatter  # noqa: E402
from task_graph import build  # noqa: E402


def relevant(issue: dict, task_id: str, relative_path: str) -> bool:
    if issue.get("task_id") == task_id or task_id in issue.get("tasks", []):
        return True
    if task_id in issue.get("cycle", []):
        return True
    if relative_path in issue.get("paths", []) or issue.get("path") == relative_path:
        return True
    return False


def main() -> int:
    if len(sys.argv) not in {3, 4} or (len(sys.argv) == 4 and sys.argv[3] != "--skip-references"):
        print("usage: validate-graph.py <spec> <backlog> [--skip-references]", file=sys.stderr)
        return 2
    spec = pathlib.Path(sys.argv[1]).resolve()
    backlog = pathlib.Path(sys.argv[2]).resolve()
    try:
        task_id = str(frontmatter(spec.read_text(encoding="utf-8")).get("id", ""))
        relative = str(spec.relative_to(backlog))
        view = build(backlog)
        skip_references = len(sys.argv) == 4
        reference_codes = {"DANGLING_DEPENDENCY", "DANGLING_CHILD", "DANGLING_SUPERSEDES", "ASYMMETRIC_COMPOSITION"}
        errors = [
            issue for issue in view["issues"]
            if issue.get("severity") == "error"
            and relevant(issue, task_id, relative)
            and not (skip_references and issue.get("code") in reference_codes)
        ]
    except (OSError, UnicodeError, ValueError, DataError) as exc:
        print(exc)
        return 1
    for issue in errors:
        print(f"{issue['code']}: {issue}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
