#!/usr/bin/env python3
"""Validate, preview, and materialize a deterministic TaskPlan v1 manifest."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from collections import defaultdict

LIB = pathlib.Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(LIB))
from taskspec_data import DataError, canonical_digest, load_document, sensitive_key_paths, yaml_scalar  # noqa: E402

ID_RE = re.compile(r"^T-[0-9]{8}-[a-z0-9]+(?:-[a-z0-9]+)*$")
LEAVES = {"XS": 1, "S": 2, "M": 3, "L": 5}
NODES = {"XL": 2, "XXL": 3}
PROFILES = {"lite", "standard", "full"}
SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_./#:+@-]+$")
REQUIRED = (
    "id", "title", "effort", "profile", "agent", "execution_backend",
    "depends_on", "touches_paths", "creates_paths", "source_note", "why",
    "goal", "evals",
)


def validate_plan(plan: object) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(plan, dict):
        return ["document must be a mapping"], warnings
    if plan.get("api_version") != "taskspec.dev/v1":
        errors.append("api_version must be taskspec.dev/v1")
    if plan.get("kind") != "TaskPlan":
        errors.append("kind must be TaskPlan")
    unknown_root = set(plan) - {"api_version", "kind", "metadata", "approved", "units"}
    if unknown_root:
        errors.append(f"unknown top-level fields: {sorted(unknown_root)}")
    credential_paths = sensitive_key_paths(plan)
    if credential_paths:
        errors.append(f"credential-bearing keys are forbidden in TaskPlan: {credential_paths}")
    if not isinstance(plan.get("metadata"), dict) or not plan["metadata"].get("name"):
        errors.append("metadata.name is required")
    units = plan.get("units")
    if not isinstance(units, list) or not units:
        errors.append("units must be a non-empty list; the CLI never invents missing units")
        return errors, warnings

    ids: list[str] = []
    creates: defaultdict[str, list[str]] = defaultdict(list)
    writes: defaultdict[str, list[str]] = defaultdict(list)
    graph: dict[str, list[str]] = {}
    long_backends = set(os.environ.get("TASKSPEC_LONG_HORIZON_BACKENDS", "glm claude codex kimi").split())

    for index, unit in enumerate(units, 1):
        where = f"units[{index}]"
        if not isinstance(unit, dict):
            errors.append(f"{where} must be a mapping")
            continue
        for key in REQUIRED:
            if key not in unit:
                errors.append(f"{where}: missing {key}; TaskPlan preview never fills authoring gaps")
        task_id = unit.get("id")
        if not isinstance(task_id, str) or not ID_RE.fullmatch(task_id):
            errors.append(f"{where}.id must match T-YYYYMMDD-kebab-slug")
            continue
        if task_id in ids:
            errors.append(f"duplicate task id: {task_id}")
        ids.append(task_id)
        effort = unit.get("effort")
        if effort not in LEAVES and effort not in NODES:
            errors.append(f"{task_id}: effort must be XS, S, M, L, XL, or XXL")
        if unit.get("profile") not in PROFILES:
            errors.append(f"{task_id}: profile must be lite, standard, or full")
        for field in ("depends_on", "touches_paths", "creates_paths", "evals", "children"):
            if field in unit and not isinstance(unit[field], list):
                errors.append(f"{task_id}: {field} must be a list")
        for field in ("title", "source_note", "why", "goal"):
            value = unit.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{task_id}: {field} must be a non-empty string")
        for field in ("agent", "execution_backend"):
            value = unit.get(field)
            if not isinstance(value, str) or not SAFE_TOKEN.fullmatch(value):
                errors.append(f"{task_id}: {field} must be a safe non-empty token")
        parent = unit.get("parent", "(none)")
        if not isinstance(parent, str) or (parent != "(none)" and not SAFE_TOKEN.fullmatch(parent)):
            errors.append(f"{task_id}: parent must be (none) or a safe repository-relative reference")
        for field in ("tags", "produces"):
            values = unit.get(field, [])
            if not isinstance(values, list) or any(not isinstance(value, str) or not SAFE_TOKEN.fullmatch(value) for value in values):
                errors.append(f"{task_id}: {field} must be a list of safe tokens")
        priority = unit.get("priority", "P2")
        if not isinstance(priority, str) or priority not in {"P0", "P1", "P2", "P3", "P4", "(none)"}:
            errors.append(f"{task_id}: priority must be P0-P4 or (none)")
        severity = unit.get("severity", "feature")
        if not isinstance(severity, str) or severity not in {"cosmetic", "refactor", "feature", "bugfix", "security", "financial-critical", "(none)"}:
            errors.append(f"{task_id}: unsupported severity")
        budget = unit.get("budget_iterations", 15)
        if not isinstance(budget, int) or isinstance(budget, bool) or budget < 1:
            errors.append(f"{task_id}: budget_iterations must be a positive integer")
        dependencies = unit.get("depends_on", []) if isinstance(unit.get("depends_on", []), list) else []
        graph[task_id] = dependencies
        for dep in dependencies:
            if not isinstance(dep, str) or not ID_RE.fullmatch(dep):
                errors.append(f"{task_id}: invalid dependency id {dep!r}")
        touches = unit.get("touches_paths", []) if isinstance(unit.get("touches_paths", []), list) else []
        new_paths = unit.get("creates_paths", []) if isinstance(unit.get("creates_paths", []), list) else []
        unique_paths = set(path for path in touches + new_paths if isinstance(path, str))
        for path in touches + new_paths:
            if not isinstance(path, str) or not path or path.startswith("/") or ".." in pathlib.PurePosixPath(path).parts or not SAFE_TOKEN.fullmatch(path):
                errors.append(f"{task_id}: write paths must be non-empty workspace-relative paths")
        for path in unique_paths:
            writes[path].append(task_id)
        for path in new_paths:
            if isinstance(path, str):
                creates[path].append(task_id)

        children = unit.get("children", [])
        if isinstance(children, list):
            for child in children:
                if not isinstance(child, str) or not ID_RE.fullmatch(child):
                    errors.append(f"{task_id}: invalid child id {child!r}")
        if effort in LEAVES:
            if children:
                errors.append(f"{task_id}: runnable leaves cannot declare children")
            count = len(unique_paths)
            if count > LEAVES.get(effort, 10**6):
                warnings.append(f"{task_id}: {effort} write surface is {count}, above the advisory budget {LEAVES[effort]}")
            if effort == "L" and unit.get("execution_backend") not in long_backends:
                errors.append(f"{task_id}: L requires a backend in TASKSPEC_LONG_HORIZON_BACKENDS ({' '.join(sorted(long_backends))})")
        elif effort in NODES:
            if not isinstance(children, list) or len(children) < NODES[effort]:
                errors.append(f"{task_id}: {effort} requires at least {NODES[effort]} children")
            if touches or new_paths:
                errors.append(f"{task_id}: decomposition nodes own no write surface")

        behaviors = unit.get("behaviors", [])
        if unit.get("profile") != "lite" and not behaviors:
            errors.append(f"{task_id}: profile {unit.get('profile')} requires behaviors")
        behavior_ids: set[str] = set()
        if behaviors and not isinstance(behaviors, list):
            errors.append(f"{task_id}: behaviors must be a list")
            behaviors = []
        for behavior in behaviors:
            if not isinstance(behavior, dict) or not all(behavior.get(key) for key in ("id", "given", "when", "then")):
                errors.append(f"{task_id}: each behavior requires id, given, when, and then")
                continue
            behavior_id = str(behavior["id"])
            if not re.fullmatch(r"B-[0-9]+", behavior_id):
                errors.append(f"{task_id}: behavior id {behavior_id!r} must match B-N")
            if behavior_id in behavior_ids:
                errors.append(f"{task_id}: duplicate behavior id {behavior_id}")
            behavior_ids.add(behavior_id)
        eval_ids: set[str] = set()
        for check in unit.get("evals", []) if isinstance(unit.get("evals", []), list) else []:
            if not isinstance(check, dict) or not all(check.get(key) for key in ("id", "description", "command")):
                errors.append(f"{task_id}: each eval requires id, description, and command")
                continue
            eval_id = str(check["id"])
            if not re.fullmatch(r"eval_[0-9]+", eval_id):
                errors.append(f"{task_id}: eval id {eval_id!r} must match eval_N")
            if eval_id in eval_ids:
                errors.append(f"{task_id}: duplicate eval id {eval_id}")
            eval_ids.add(eval_id)
            verifies = check.get("verifies", [])
            if not isinstance(verifies, list) or any(not isinstance(item, str) for item in verifies):
                errors.append(f"{task_id}: {eval_id} verifies must be a list of behavior ids")
                verifies = []
            verified = set(verifies)
            expected_duration = check.get("expected_duration_sec", 10)
            if not isinstance(expected_duration, int) or isinstance(expected_duration, bool) or expected_duration < 1:
                errors.append(f"{task_id}: {eval_id} expected_duration_sec must be a positive integer")
            if behavior_ids and not verified:
                errors.append(f"{task_id}: {eval_id} must declare verifies")
            unknown = verified - behavior_ids
            if unknown:
                errors.append(f"{task_id}: {eval_id} verifies unknown behaviors {sorted(unknown)}")
        if behavior_ids:
            covered = {
                item
                for check in unit.get("evals", [])
                if isinstance(check, dict) and isinstance(check.get("verifies", []), list)
                for item in check.get("verifies", [])
                if isinstance(item, str)
            }
            if behavior_ids - covered:
                errors.append(f"{task_id}: uncovered behaviors {sorted(behavior_ids - covered)}")

    known = set(ids)
    for task_id, dependencies in graph.items():
        for dependency in dependencies:
            if isinstance(dependency, str) and ID_RE.fullmatch(dependency) and dependency not in known:
                errors.append(f"{task_id}: dependency {dependency} is not declared in this TaskPlan")
    for task_id, unit in ((u.get("id"), u) for u in units if isinstance(u, dict)):
        if not task_id:
            continue
        for child in unit.get("children", []) if isinstance(unit.get("children", []), list) else []:
            if child not in known:
                errors.append(f"{task_id}: child {child} is not declared in this TaskPlan")
    for path, owners in creates.items():
        if len(set(owners)) > 1:
            errors.append(f"dual-creation collision: {path} is created by {', '.join(sorted(set(owners)))}")

    def depends_transitively(task_id: str, dependency: str) -> bool:
        pending = list(graph.get(task_id, []))
        seen: set[str] = set()
        while pending:
            current = pending.pop()
            if current == dependency:
                return True
            if current in seen:
                continue
            seen.add(current)
            pending.extend(item for item in graph.get(current, []) if isinstance(item, str))
        return False

    for path, owners in sorted(writes.items()):
        unique_owners = sorted(set(owners))
        unordered_pairs = [
            f"{left}<->{right}"
            for position, left in enumerate(unique_owners)
            for right in unique_owners[position + 1:]
            if not depends_transitively(left, right) and not depends_transitively(right, left)
        ]
        if unordered_pairs:
            warnings.append(f"write conflict: {path} has unordered writers {', '.join(unordered_pairs)}")

    state: dict[str, int] = {}
    def visit(node: str, stack: list[str]) -> None:
        if state.get(node) == 1:
            errors.append("dependency cycle: " + " -> ".join(stack + [node]))
            return
        if state.get(node) == 2:
            return
        state[node] = 1
        for dep in graph.get(node, []):
            if dep in graph:
                visit(dep, stack + [node])
        state[node] = 2
    for node in graph:
        visit(node, [])
    return errors, warnings


def _tokens(values: list) -> str:
    # Every caller is validated as a list of delimiter-free safe tokens before
    # rendering, so the shell engine and the constrained Python reader see the
    # same portable inline-YAML representation.
    return "[" + ", ".join(values) + "]"


def _frontmatter(unit: dict) -> list[str]:
    rows = [
        "---", f"id: {unit['id']}", f"title: {yaml_scalar(unit['title'])}",
        "status: ready", "format_version: 3", f"profile: {unit['profile']}",
        f"effort: {unit['effort']}", f"budget_iterations: {int(unit.get('budget_iterations', 15))}",
        f"agent: {unit['agent']}", f"parent: {unit.get('parent', '(none)')}",
        f"depends_on: {_tokens(unit['depends_on'])}",
    ]
    if unit.get("children"):
        rows.append(f"children: {_tokens(unit['children'])}")
    rows.extend([
        f"touches_paths: {_tokens(unit['touches_paths'])}",
        f"creates_paths: {_tokens(unit['creates_paths'])}",
        f"source_note: {yaml_scalar(unit['source_note'])}",
        f"created: {yaml_scalar(unit.get('created', unit['id'][2:10][:4] + '-' + unit['id'][6:8] + '-' + unit['id'][8:10] + 'T00:00:00Z'))}",
        f"tags: {_tokens(unit.get('tags', []))}", "owner: (none)",
        f"priority: {unit.get('priority', 'P2')}", f"severity: {unit.get('severity', 'feature')}",
        "due_date: (none)", "precondition: (none)", "blocked_reason: (none)",
        "security_class: (none)", "source_action_item: (none)", "tracker_ref: (none)",
        f"execution_backend: {unit['execution_backend']}", "signed_off: false",
        "signed_off_by: (none)", "signed_off_at: (none)", "accepted: false",
        "accepted_by: (none)", "accepted_at: (none)", "---",
    ])
    return rows


def render_spec(unit: dict) -> str:
    lines = _frontmatter(unit)
    lines += ["", f"# {unit['title']}", "", f"> **Why:** {unit['why']}", "", "## Goal", "", str(unit["goal"])]
    context = unit.get("context", "(none — the manifest contains all execution context)")
    lines += ["", "## Context", "", str(context)]
    behaviors = unit.get("behaviors", [])
    if behaviors:
        lines += ["", "## Behavior", ""]
        for behavior in behaviors:
            lines.append(f"- **{behavior['id']}** — GIVEN {behavior['given']} WHEN {behavior['when']} THEN {behavior['then']}")
    lines += ["", "## Success Criteria", "", "```bash"]
    for check in unit["evals"]:
        description_lines = str(check["description"]).splitlines() or [""]
        lines.extend(f"# {check['id']}: {line}" if index == 0 else f"# {line}" for index, line in enumerate(description_lines))
        lines.append(f"{check['id']}() {{")
        for command_line in str(check["command"]).splitlines():
            lines.append(f"  {command_line}")
        lines.append("}")
        lines.append("")
    lines += ["```", "", "## Validation Card", "", "```yaml", "success_criteria:"]
    for check in unit["evals"]:
        lines += [
            f"  - id: {check['id']}", f"    description: {yaml_scalar(check['description'])}",
            "    runnable: bash", "    check_type: deterministic",
            f"    verifies: {_tokens(check.get('verifies', []))}",
            f"    terminal: {str(check.get('terminal', True)).lower()}",
            f"    expected_duration_sec: {int(check.get('expected_duration_sec', 10))}",
        ]
    lines += [
        "retry_policy:", f"  max_iterations: {int(unit.get('budget_iterations', 15))}",
        "  circuit_breaker_no_progress: 3", "  on_terminal_failure: park_with_context",
        "agent_contract:", "  version: 2", "  read: [intent, behavior, contract, guardrails]",
        f"  produce: {_tokens(unit.get('produces', ['code', 'tests']))}",
        "  required_tools: [git, bash]", "  timeout_minutes: 30", "  sandbox_type: host",
        "  output_artifacts: []", "  mcp_dependencies: []", "  emit: [pass, fail, retry_with_reason, parked_with_context]",
        "  backend_metadata: {}", "```", "", "## Exit Check", "", "```bash",
        " && ".join(str(check["id"]) for check in unit["evals"]), "```",
        "", "## Rollback Plan", "", str(unit.get("rollback", "Revert only the declared write surface and park the task with context.")),
        "", "## Observability Hooks", "", str(unit.get("observability", "(none — no runtime observability required)")),
        "", "## Anti-Patterns", "",
    ]
    anti = unit.get("anti_patterns", ["Do not weaken or edit the eval contract after sign-off."])
    lines.extend(f"- {item}" for item in anti)
    lines += ["", "## Do-Not-Touch", ""]
    lines.extend(f"- `{item}`" for item in unit.get("do_not_touch", ["(none)"]))
    lines += ["", "## Open Questions", "", str(unit.get("open_questions", "(none — this task is fully specified)")), ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preview", "generate"))
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out-dir", default=os.environ.get("TASKSPEC_BACKLOG_DIR", "tasks"))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        plan = load_document(args.manifest)
    except DataError as exc:
        print(f"TASK_PLAN=INVALID\nerror: {exc}", file=sys.stderr)
        return 1
    errors, warnings = validate_plan(plan)
    units = plan.get("units", []) if isinstance(plan, dict) else []
    result = {
        "contract": "TaskPlan/v1", "manifest": str(pathlib.Path(args.manifest).resolve()),
        "digest": canonical_digest(plan), "approved": bool(plan.get("approved")) if isinstance(plan, dict) else False,
        "valid": not errors, "errors": errors, "warnings": warnings,
        "units": [{key: unit.get(key) for key in ("id", "title", "effort", "profile", "execution_backend", "depends_on", "children") if key in unit} for unit in units if isinstance(unit, dict)],
    }
    if args.action == "generate" and not result["approved"]:
        errors.append("TaskPlan must set approved: true before generation")
        result["valid"] = False
    if errors:
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("TaskPlan v1 — INVALID", file=sys.stderr)
            for error in errors:
                print(f"  ERROR  {error}", file=sys.stderr)
            for warning in warnings:
                print(f"  WARN   {warning}", file=sys.stderr)
            print("TASK_PLAN=INVALID")
        return 1

    if args.action == "generate":
        out_dir = pathlib.Path(args.out_dir)
        targets = [out_dir / f"{unit['id']}.md" for unit in units]
        existing = [str(path) for path in targets if path.exists()]
        if existing:
            result["valid"] = False
            result["errors"] = [f"refusing to clobber existing file: {path}" for path in existing]
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                for error in result["errors"]:
                    print(f"ERROR: {error}", file=sys.stderr)
                print("TASK_BATCH=REFUSED")
            return 1
        if not args.dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)
            for unit, target in zip(units, targets):
                target.write_text(render_spec(unit), encoding="utf-8")
        result["dry_run"] = args.dry_run
        result["created"] = [str(path) for path in targets]
        token = "TASK_BATCH=DRY_RUN" if args.dry_run else "TASK_BATCH=OK"
    else:
        token = "TASK_PLAN=OK"

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"TaskPlan v1 · {'approved' if result['approved'] else 'review required'} · digest {result['digest'][:12]}")
        print(f"{'ID':<38} {'KIND':<6} {'SIZE':<4} {'BACKEND':<12} TITLE")
        for unit in units:
            kind = "node" if unit["effort"] in NODES else "leaf"
            print(f"{unit['id']:<38} {kind:<6} {unit['effort']:<4} {unit['execution_backend']:<12} {unit['title']}")
        for warning in warnings:
            print(f"WARN: {warning}")
        if args.action == "generate":
            verb = "would create" if args.dry_run else "created"
            print(f"{verb}: {len(result['created'])} Task-Spec scaffold(s) in {args.out_dir}/")
        print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
