#!/usr/bin/env python3
"""Deterministic, read-only TaskGraphView/v1 projection."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from collections import defaultdict, deque
from typing import Any, Iterable

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
sys.path.insert(0, str(ROOT / "src" / "security"))
from taskspec_data import DataError, canonical_digest, frontmatter  # noqa: E402
from task_revision import revision  # noqa: E402


CONTRACT = "TaskGraphView/v1"
def _strings(value: Any) -> list[str]:
    if value is None or value == {}:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    return []


def _path_overlap(left: str, right: str) -> bool:
    left, right = left.rstrip("/"), right.rstrip("/")
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def task_files(backlog: pathlib.Path) -> list[pathlib.Path]:
    """Resolve every task recursively so all lifecycle views share one universe."""
    if not backlog.is_dir():
        return []
    return sorted(
        {path for path in backlog.rglob("T-*.md") if path.is_file()},
        key=lambda item: str(item.relative_to(backlog)),
    )


def resolve_task(backlog: pathlib.Path, target: str) -> pathlib.Path:
    direct = pathlib.Path(target)
    if direct.is_file():
        return direct.resolve()
    matches: list[pathlib.Path] = []
    for path in task_files(backlog):
        if path.stem == target or path.stem.startswith(target + "-"):
            matches.append(path)
    if len(matches) != 1:
        raise DataError(f"expected exactly one task for {target!r}, found {len(matches)}")
    return matches[0].resolve()


def _cycles(ids: Iterable[str], dependencies: dict[str, list[str]]) -> list[list[str]]:
    color: dict[str, int] = {task_id: 0 for task_id in ids}
    stack: list[str] = []
    cycles: list[list[str]] = []

    def visit(task_id: str) -> None:
        color[task_id] = 1
        stack.append(task_id)
        for dep in sorted(dependencies.get(task_id, [])):
            if dep not in color:
                continue
            if color[dep] == 0:
                visit(dep)
            elif color[dep] == 1:
                start = stack.index(dep)
                cycle = stack[start:] + [dep]
                if cycle not in cycles:
                    cycles.append(cycle)
        stack.pop()
        color[task_id] = 2

    for task_id in sorted(color):
        if color[task_id] == 0:
            visit(task_id)
    return cycles


def build(backlog: pathlib.Path) -> dict[str, Any]:
    backlog = backlog.resolve()
    nodes: dict[str, dict[str, Any]] = {}
    issues: list[dict[str, Any]] = []
    duplicates: dict[str, list[str]] = defaultdict(list)

    for path in task_files(backlog):
        rel = str(path.relative_to(backlog))
        try:
            text = path.read_text(encoding="utf-8")
            fm = frontmatter(text)
            rev = revision(path)
        except (OSError, UnicodeError, DataError) as exc:
            issues.append({"code": "INVALID_TASK", "severity": "error", "path": rel, "message": str(exc)})
            continue
        task_id = str(fm.get("id", ""))
        duplicates[task_id].append(rel)
        if task_id in nodes:
            continue
        touches = sorted(set(_strings(fm.get("touches_paths"))))
        creates = sorted(set(_strings(fm.get("creates_paths"))))
        nodes[task_id] = {
            "task_id": task_id,
            "path": rel,
            "status": str(fm.get("status", "unknown")),
            "effort": str(fm.get("effort", "unknown")),
            "task_revision_digest": rev["task_revision_digest"],
            "depends_on": sorted(set(_strings(fm.get("depends_on")))),
            "blocks": sorted(set(_strings(fm.get("blocks")))),
            "children": sorted(set(_strings(fm.get("children")))),
            "supersedes": str(fm.get("supersedes")) if fm.get("supersedes") not in {None, "", "(none)"} else None,
            "write_surface": {"touches_paths": touches, "creates_paths": creates},
        }

    for task_id, paths in sorted(duplicates.items()):
        if not task_id:
            issues.append({"code": "MISSING_ID", "severity": "error", "paths": paths})
        elif len(paths) > 1:
            issues.append({"code": "DUPLICATE_ID", "severity": "error", "task_id": task_id, "paths": paths})

    dependencies = {task_id: node["depends_on"] for task_id, node in nodes.items()}
    edges: list[dict[str, str]] = []
    composition_parents: dict[str, list[str]] = defaultdict(list)
    for task_id, node in sorted(nodes.items()):
        for dep in node["depends_on"]:
            edges.append({"type": "depends_on", "from": task_id, "to": dep})
            if dep not in nodes:
                issues.append({"code": "DANGLING_DEPENDENCY", "severity": "error", "task_id": task_id, "target": dep})
        for child in node["children"]:
            edges.append({"type": "contains", "from": task_id, "to": child})
            composition_parents[child].append(task_id)
            if child not in nodes:
                issues.append({"code": "DANGLING_CHILD", "severity": "error", "task_id": task_id, "target": child})
        if node["supersedes"]:
            edges.append({"type": "supersedes", "from": task_id, "to": node["supersedes"]})
            if node["supersedes"] not in nodes:
                issues.append({"code": "DANGLING_SUPERSEDES", "severity": "error", "task_id": task_id, "target": node["supersedes"]})
            elif nodes[node["supersedes"]]["status"] not in {"parked", "done"}:
                issues.append({"code": "LIVE_SUPERSEDED_TASK", "severity": "error", "task_id": task_id, "target": node["supersedes"]})

    for child, parents in sorted(composition_parents.items()):
        if len(parents) > 1:
            issues.append({"code": "ASYMMETRIC_COMPOSITION", "severity": "error", "task_id": child, "parents": sorted(parents)})

    declared_reverse: dict[str, list[str]] = defaultdict(list)
    for task_id, node in nodes.items():
        for dependency in node["depends_on"]:
            declared_reverse[dependency].append(task_id)
    for task_id, node in sorted(nodes.items()):
        if node["blocks"] and sorted(node["blocks"]) != sorted(declared_reverse.get(task_id, [])):
            issues.append({
                "code": "ADVISORY_BLOCKS_MISMATCH", "severity": "warning", "task_id": task_id,
                "blocks": node["blocks"], "derived_from_depends_on": sorted(declared_reverse.get(task_id, [])),
            })

    for cycle in _cycles(nodes, dependencies):
        issues.append({"code": "DEPENDENCY_CYCLE", "severity": "error", "cycle": cycle})
    compositions = {task_id: node["children"] for task_id, node in nodes.items()}
    for cycle in _cycles(nodes, compositions):
        issues.append({"code": "COMPOSITION_CYCLE", "severity": "error", "cycle": cycle})

    conflict_edges: list[dict[str, Any]] = []
    task_ids = sorted(nodes)
    for index, left_id in enumerate(task_ids):
        left = nodes[left_id]["write_surface"]
        for right_id in task_ids[index + 1 :]:
            right = nodes[right_id]["write_surface"]
            overlaps: list[dict[str, str]] = []
            dual_create = False
            for left_kind, left_paths in left.items():
                for right_kind, right_paths in right.items():
                    for left_path in left_paths:
                        for right_path in right_paths:
                            if _path_overlap(left_path, right_path):
                                overlaps.append({"left": left_path, "right": right_path})
                                dual_create = dual_create or (left_kind == "creates_paths" and right_kind == "creates_paths")
            if overlaps:
                conflict_edges.append(
                    {"type": "write_conflict", "from": left_id, "to": right_id, "dual_create": dual_create, "overlaps": overlaps}
                )
                if dual_create:
                    issues.append({"code": "DUAL_CREATE_COLLISION", "severity": "error", "tasks": [left_id, right_id], "overlaps": overlaps})

    cycles_present = any(issue["code"] == "DEPENDENCY_CYCLE" for issue in issues)
    blocked_reasons: dict[str, list[str]] = {}
    superseded = {node["supersedes"] for node in nodes.values() if node.get("supersedes")}
    ready: list[str] = []
    for task_id, node in sorted(nodes.items()):
        reasons: list[str] = []
        if node["status"] != "ready":
            reasons.append(f"status:{node['status']}")
        if node["effort"] in {"XL", "XXL"}:
            reasons.append("composition-node")
        for dep in node["depends_on"]:
            if dep not in nodes:
                reasons.append(f"missing:{dep}")
            elif nodes[dep]["status"] != "done":
                reasons.append(f"unmet:{dep}:{nodes[dep]['status']}")
            if dep in superseded:
                reasons.append(f"stale-superseded:{dep}")
        for edge in conflict_edges:
            if task_id not in {edge["from"], edge["to"]}:
                continue
            other = edge["to"] if edge["from"] == task_id else edge["from"]
            if nodes.get(other, {}).get("status") == "in-progress":
                reasons.append(f"write-conflict:{other}:in-progress")
        if cycles_present and any(task_id in issue.get("cycle", []) for issue in issues if issue["code"] == "DEPENDENCY_CYCLE"):
            reasons.append("dependency-cycle")
        if reasons:
            blocked_reasons[task_id] = reasons
        else:
            ready.append(task_id)

    # Greedy deterministic write-disjoint grouping for runnable ready leaves.
    conflict_pairs = {frozenset((edge["from"], edge["to"])) for edge in conflict_edges}
    concurrency_groups: list[list[str]] = []
    for task_id in ready:
        placed = False
        for group in concurrency_groups:
            if all(frozenset((task_id, member)) not in conflict_pairs for member in group):
                group.append(task_id)
                placed = True
                break
        if not placed:
            concurrency_groups.append([task_id])

    immutable_graph = {
        "nodes": [
            {
                "task_id": task_id,
                "task_revision_digest": nodes[task_id]["task_revision_digest"],
                "depends_on": nodes[task_id]["depends_on"],
                "children": nodes[task_id]["children"],
                "supersedes": nodes[task_id]["supersedes"],
            }
            for task_id in sorted(nodes)
        ],
        "edges": sorted(edges, key=lambda item: (item["type"], item["from"], item["to"])),
    }
    return {
        "contract": CONTRACT,
        "backlog": str(backlog),
        "graph_revision_digest": f"sha256:{canonical_digest(immutable_graph)}",
        "nodes": [nodes[task_id] for task_id in sorted(nodes)],
        "edges": immutable_graph["edges"],
        "write_conflicts": conflict_edges,
        "issues": issues,
        "ready_frontier": ready,
        "blocked_reasons": blocked_reasons,
        "concurrency_groups": concurrency_groups,
        "composition_parents": {key: sorted(value) for key, value in sorted(composition_parents.items())},
    }


def dependency_closure(view: dict[str, Any], task_id: str) -> dict[str, Any]:
    nodes = {node["task_id"]: node for node in view["nodes"]}
    if task_id not in nodes:
        raise DataError(f"task {task_id!r} is not in the backlog graph")
    parents = view.get("composition_parents", {})
    dependency_members: set[str] = set()
    queue = deque([task_id])
    while queue:
        current = queue.popleft()
        if current in dependency_members:
            continue
        dependency_members.add(current)
        node = nodes.get(current)
        if node:
            queue.extend(node["depends_on"])
    composition_ancestors: set[str] = set()
    queue = deque(parents.get(task_id, []))
    while queue:
        current = queue.popleft()
        if current in composition_ancestors:
            continue
        composition_ancestors.add(current)
        queue.extend(parents.get(current, []))
    wanted = dependency_members | composition_ancestors
    members = [
        {"task_id": item, "task_revision_digest": nodes[item]["task_revision_digest"]}
        for item in sorted(wanted)
        if item in nodes
    ]
    return {
        "contract": "DependencyClosure/v1",
        "task_id": task_id,
        "digest": f"sha256:{canonical_digest(members)}",
        "members": members,
    }


def active_write_conflicts(view: dict[str, Any], task_id: str) -> list[dict[str, Any]]:
    """Return conflicts with another task that is currently executing."""
    nodes = {node["task_id"]: node for node in view["nodes"]}
    conflicts: list[dict[str, Any]] = []
    for edge in view.get("write_conflicts", []):
        if task_id not in {edge.get("from"), edge.get("to")}:
            continue
        other = edge["to"] if edge.get("from") == task_id else edge["from"]
        if nodes.get(other, {}).get("status") == "in-progress":
            conflicts.append(edge)
    return conflicts


def mermaid(view: dict[str, Any]) -> str:
    lines = ["flowchart LR"]
    for node in view["nodes"]:
        safe_id = "n_" + hashlib.sha256(node["task_id"].encode()).hexdigest()[:10]
        label = f"{node['task_id']}\\n{node['status']} · {node['effort']}".replace('"', "'")
        lines.append(f'    {safe_id}["{label}"]')
    aliases = {node["task_id"]: "n_" + hashlib.sha256(node["task_id"].encode()).hexdigest()[:10] for node in view["nodes"]}
    for edge in view["edges"]:
        if edge["from"] in aliases and edge["to"] in aliases:
            lines.append(f'    {aliases[edge["from"]]} -->|"{edge["type"]}"| {aliases[edge["to"]]}')
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backlog", default="tasks")
    parser.add_argument("--task")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--mermaid", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        view = build(pathlib.Path(args.backlog))
        if args.task:
            view["selected_closure"] = dependency_closure(view, args.task)
        if args.mermaid:
            print(mermaid(view))
        elif args.json:
            print(json.dumps(view, indent=2, ensure_ascii=False, sort_keys=True))
        else:
            print(f"GRAPH={view['graph_revision_digest']} tasks={len(view['nodes'])} ready={len(view['ready_frontier'])} issues={len(view['issues'])}")
            for issue in view["issues"]:
                print(f"{issue['severity'].upper()} {issue['code']} {json.dumps(issue, sort_keys=True)}")
            print("CONCURRENCY_GROUPS=" + json.dumps(view["concurrency_groups"], separators=(",", ":")))
            if args.task:
                selected = view["selected_closure"]
                print(f"CLOSURE={selected['digest']} members={len(selected['members'])}")
        if args.check and any(issue.get("severity") == "error" for issue in view["issues"]):
            return 1
        return 0
    except (OSError, DataError, UnicodeError) as exc:
        print(f"GRAPH=INVALID error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
