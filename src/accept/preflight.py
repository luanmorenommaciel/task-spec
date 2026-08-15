#!/usr/bin/env python3
"""Validate a TaskHandoff/v3, graph closure, Git base, and declared write scope."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import pathlib
import re
import subprocess
import sys
import uuid
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
sys.path.insert(0, str(ROOT / "src" / "security"))
sys.path.insert(0, str(ROOT / "src" / "graph"))
from taskspec_data import DataError, frontmatter, parse_yaml_subset, sha256_file  # noqa: E402
from workspace import WorkspaceError, resolve_backlog, resolve_workspace  # noqa: E402
from task_revision import revision  # noqa: E402
from task_graph import active_write_conflicts, build as build_graph, dependency_closure  # noqa: E402


def _git(workspace: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=workspace, text=True, capture_output=True, check=False)


def _inside(path: pathlib.Path, root: pathlib.Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _validate_declared_path(raw: Any, workspace: pathlib.Path, *, allow_git: bool = False) -> tuple[str | None, str | None]:
    if not isinstance(raw, str) or not raw.strip():
        return None, "path declaration must be a non-empty string"
    path = pathlib.PurePosixPath(raw)
    if path.is_absolute() or raw.startswith("/"):
        return None, f"absolute path is forbidden: {raw}"
    if ".." in path.parts:
        return None, f"path traversal is forbidden: {raw}"
    if ".git" in path.parts and not allow_git:
        return None, f".git is outside task authority: {raw}"
    normalized = pathlib.PurePosixPath(*[part for part in path.parts if part not in {"", "."}])
    if not normalized.parts:
        return None, f"repository root is too broad a write scope: {raw}"
    candidate = workspace.joinpath(*normalized.parts)
    probe = candidate if candidate.exists() or candidate.is_symlink() else candidate.parent
    while not probe.exists() and probe != workspace:
        probe = probe.parent
    resolved = probe.resolve()
    if not _inside(resolved, workspace):
        return None, f"path escapes the repository through a symlink: {raw}"
    if candidate.exists() or candidate.is_symlink():
        resolved_candidate = candidate.resolve()
        if not _inside(resolved_candidate, workspace):
            return None, f"existing path escapes the repository through a symlink: {raw}"
    return normalized.as_posix(), None


def _overlap(changed: str, declared: str) -> bool:
    return changed == declared or changed.startswith(declared.rstrip("/") + "/")


def _validation_card(text: str) -> dict[str, Any]:
    section = re.search(r"^##\s+Validation Card\s*$\n(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    fenced = re.search(r"```ya?ml\s*\n(.*?)```", section.group(1) if section else "", re.S | re.I)
    if not fenced:
        raise DataError("Validation Card has no YAML fence")
    value = parse_yaml_subset(fenced.group(1))
    if not isinstance(value, dict):
        raise DataError("Validation Card must be a mapping")
    return value


def _receipt_requirements(fm: dict[str, Any]) -> list[str]:
    requirements = ["deterministic"]
    if int(str(fm.get("format_version", 0)).split(".")[0]) >= 4:
        policy = fm.get("evaluation_policy", {})
        for name, contract in (
            ("holdout", "EvaluationReceipt/v2"),
            ("graded", "GradedEvaluationReceipt/v2"),
            ("human", "HumanAcceptanceReceipt/v2"),
        ):
            if isinstance(policy, dict) and isinstance(policy.get(name), dict) and policy[name].get("required") is True:
                requirements.append(contract)
        if isinstance(fm.get("environment_contract"), dict) and fm["environment_contract"].get("required") is True:
            requirements.append("EnvironmentReceipt/v2")
        if isinstance(fm.get("identity_policy"), dict) and fm["identity_policy"].get("required") is True:
            requirements.append("AuthorizationReceipt/v1")
    return requirements


def _changed(workspace: pathlib.Path, base: str) -> tuple[list[str], str | None]:
    exists = _git(workspace, "cat-file", "-e", f"{base}^{{commit}}")
    if exists.returncode:
        return [], "base commit does not exist"
    ancestor = _git(workspace, "merge-base", "--is-ancestor", base, "HEAD")
    if ancestor.returncode:
        return [], "base commit is not an ancestor of HEAD"
    commands = (
        ("diff", "--name-only", f"{base}..HEAD"),
        ("diff", "--name-only", "--cached"),
        ("diff", "--name-only"),
        ("ls-files", "--others", "--exclude-standard"),
    )
    paths: set[str] = set()
    for command in commands:
        result = _git(workspace, *command)
        if result.returncode:
            return [], f"git {' '.join(command)} failed: {result.stderr.strip()}"
        paths.update(line for line in result.stdout.splitlines() if line)
    return sorted(paths), None


def evaluate(spec: pathlib.Path, handoff_path: pathlib.Path | None, check_blast: bool, bookkeeping: list[pathlib.Path] | None = None) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[str] = []
    tier2_reasons: list[str] = []
    spec = spec.resolve()
    text = spec.read_text(encoding="utf-8")
    fm = frontmatter(text)
    task_rev = revision(spec)
    try:
        workspace = resolve_workspace(spec)
        backlog = resolve_backlog(spec, workspace)
    except WorkspaceError as exc:
        raise DataError(str(exc)) from exc

    handoff: dict[str, Any] | None = None
    if handoff_path:
        try:
            handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append({"code": "HANDOFF_STALE", "message": f"cannot read handoff: {exc}"})
    if not isinstance(handoff, dict) or handoff.get("contract") != "TaskHandoff/v3":
        tier2_reasons.append("HANDOFF_MISSING_OR_LEGACY")
        handoff = None

    base = "HEAD"
    expected_closure: dict[str, Any] | None = None
    if handoff:
        try:
            base = str(handoff["source"]["base_commit"])
            attempt_id = handoff["attempt"]["id"]
            if not isinstance(attempt_id, str) or str(uuid.UUID(attempt_id)) != attempt_id.lower():
                errors.append({"code": "HANDOFF_STALE", "message": "handoff attempt ID is not a canonical UUID"})
            issued_at = handoff["attempt"]["issued_at"]
            if not isinstance(issued_at, str) or not issued_at.endswith("Z"):
                errors.append({"code": "HANDOFF_STALE", "message": "handoff issued_at must be a UTC timestamp ending in Z"})
            else:
                issued = datetime.fromisoformat(issued_at[:-1] + "+00:00")
                if issued.utcoffset() != timezone.utc.utcoffset(issued):
                    errors.append({"code": "HANDOFF_STALE", "message": "handoff issued_at must be UTC"})
            if handoff.get("task_id") != fm.get("id"):
                errors.append({"code": "HANDOFF_STALE", "message": "handoff task_id does not match spec"})
            if handoff.get("task_revision_digest") != task_rev["task_revision_digest"]:
                errors.append({"code": "HANDOFF_STALE", "message": "handoff task revision no longer matches spec"})
            if handoff.get("authorization", {}).get("ref") != fm.get("signed_off_sig"):
                errors.append({"code": "HANDOFF_STALE", "message": "handoff authorization no longer matches spec"})
            expected_authorization = {
                "scheme": str(fm.get("signed_off_sig", "")).split(":", 1)[0],
                "ref": fm.get("signed_off_sig"),
                "tier": handoff.get("signoff_tier"),
                "signed_by": fm.get("signed_off_by"),
                "signed_at": fm.get("signed_off_at"),
            }
            if handoff.get("signoff_tier") not in {1, 2}:
                errors.append({"code": "HANDOFF_STALE", "message": "handoff signoff tier must be 1 or 2"})
            if handoff.get("authorization") != expected_authorization:
                errors.append({"code": "HANDOFF_STALE", "message": "handoff authorization metadata differs from the sealed spec"})
            handoff_workspace = pathlib.Path(str(handoff["source"]["workspace"])).resolve()
            if handoff_workspace != workspace:
                errors.append({"code": "HANDOFF_STALE", "message": "handoff workspace does not match current repository"})
            if pathlib.Path(str(handoff.get("workspace", ""))).resolve() != workspace:
                errors.append({"code": "HANDOFF_STALE", "message": "handoff legacy workspace alias differs from source.workspace"})
            if pathlib.Path(str(handoff.get("spec", ""))).resolve() != spec:
                errors.append({"code": "HANDOFF_STALE", "message": "handoff spec path does not match the accepted task"})
            expected_format = int(str(fm.get("format_version", 0)).split(".")[0])
            if handoff.get("format_version") != expected_format:
                errors.append({"code": "HANDOFF_STALE", "message": "handoff format version differs from the sealed spec"})
            body_do_not_touch = re.findall(r"`([^`]+)`", text.split("## Do-Not-Touch", 1)[-1].split("\n## ", 1)[0])
            expected_scope = {
                "touches_paths": fm.get("touches_paths", []),
                "creates_paths": fm.get("creates_paths", []),
                "do_not_touch": body_do_not_touch,
            }
            if handoff.get("write_scope") != expected_scope:
                errors.append({"code": "HANDOFF_STALE", "message": "handoff write scope differs from the sealed spec"})
            expected_budgets = {
                "iterations": fm.get("budget_iterations"),
                "tokens": fm.get("budget_tokens"),
                "effort": fm.get("effort"),
            }
            if handoff.get("budgets") != expected_budgets:
                errors.append({"code": "HANDOFF_STALE", "message": "handoff budgets differ from the sealed spec"})
            declared_backend = str(fm.get("execution_backend", "any"))
            if declared_backend != "any" and handoff.get("backend") != declared_backend:
                errors.append({"code": "HANDOFF_STALE", "message": "handoff backend differs from sealed execution_backend"})
            card = _validation_card(text)
            if handoff.get("agent_contract") != card.get("agent_contract", {}):
                errors.append({"code": "HANDOFF_STALE", "message": "handoff agent_contract differs from the sealed Validation Card"})
            expected_policy = fm.get("evaluation_policy", {}) if expected_format >= 4 else {}
            expected_environment = fm.get("environment_contract", {}) if expected_format >= 4 else {}
            expected_identity = fm.get("identity_policy", {}) if expected_format >= 4 else {}
            if handoff.get("evaluation_policy") != expected_policy or handoff.get("environment_contract") != expected_environment or handoff.get("identity_policy") != expected_identity:
                errors.append({"code": "HANDOFF_STALE", "message": "handoff evidence or environment policy differs from the sealed spec"})
            if handoff.get("receipt_requirements") != _receipt_requirements(fm):
                errors.append({"code": "HANDOFF_STALE", "message": "handoff receipt requirements differ from sealed policy"})
            current_spec_digest = f"sha256:{sha256_file(spec)}"
            if handoff.get("spec_digest") != current_spec_digest:
                warnings.append("spec digest changed while TaskRevision/v1 remained stable; mutable lifecycle fields may have changed")
        except (KeyError, TypeError, OSError, ValueError) as exc:
            errors.append({"code": "HANDOFF_STALE", "message": f"handoff is incomplete: {exc}"})

    view = build_graph(backlog)
    graph_errors = [issue for issue in view["issues"] if issue.get("severity") == "error"]
    if graph_errors:
        errors.append({"code": "GRAPH_INVALID", "message": f"{graph_errors[0]['code']}: backlog graph is invalid"})
    active_conflicts = active_write_conflicts(view, str(fm.get("id")))
    if active_conflicts:
        edge = active_conflicts[0]
        other = edge["to"] if edge["from"] == fm.get("id") else edge["from"]
        errors.append({"code": "GRAPH_INVALID", "message": f"write scope conflicts with in-progress task {other}"})
    try:
        expected_closure = dependency_closure(view, str(fm.get("id")))
        if handoff and handoff.get("dependency_closure") != expected_closure:
            errors.append({"code": "CLOSURE_DRIFT", "message": "dependency closure changed after handoff"})
    except DataError as exc:
        errors.append({"code": "GRAPH_INVALID", "message": str(exc)})

    allowed: list[str] = []
    forbidden: list[str] = []
    scope = handoff.get("write_scope", {}) if handoff else {
        "touches_paths": fm.get("touches_paths", []),
        "creates_paths": fm.get("creates_paths", []),
        "do_not_touch": re.findall(r"`([^`]+)`", text.split("## Do-Not-Touch", 1)[-1].split("\n## ", 1)[0]),
    }
    for raw in list(scope.get("touches_paths", [])) + list(scope.get("creates_paths", [])):
        value, path_error = _validate_declared_path(raw, workspace)
        if path_error:
            errors.append({"code": "BLAST_RADIUS", "message": path_error})
        elif value:
            allowed.append(value)
    for raw in scope.get("do_not_touch", []):
        value, path_error = _validate_declared_path(raw, workspace, allow_git=True)
        if path_error:
            errors.append({"code": "BLAST_RADIUS", "message": path_error})
        elif value:
            forbidden.append(value)

    changed: list[str] = []
    if check_blast:
        changed, git_error = _changed(workspace, base)
        if git_error:
            code = "BASE_DIVERGED" if "ancestor" in git_error or "does not exist" in git_error else "BLAST_RADIUS"
            errors.append({"code": code, "message": git_error})
        else:
            spec_rel = spec.relative_to(workspace).as_posix()
            exact_bookkeeping = {
                spec_rel,
                f"{backlog.relative_to(workspace).as_posix()}/_state.yaml",
                f"{backlog.relative_to(workspace).as_posix()}/_metrics.jsonl",
            }
            if handoff_path:
                try:
                    exact_bookkeeping.add(handoff_path.resolve().relative_to(workspace).as_posix())
                except ValueError:
                    pass
            if handoff:
                try:
                    exact_bookkeeping.add(
                        f".taskspec/acceptance/{fm.get('id')}/{handoff['attempt']['id']}.json"
                    )
                except (KeyError, TypeError):
                    pass
            for item in bookkeeping or []:
                try:
                    exact_bookkeeping.add(item.resolve().relative_to(workspace).as_posix())
                except ValueError:
                    pass
            for changed_path in changed:
                if changed_path in exact_bookkeeping:
                    continue
                if any(_overlap(changed_path, denied) for denied in forbidden):
                    errors.append({"code": "BLAST_RADIUS", "message": f"changed do-not-touch path: {changed_path}"})
                elif not any(_overlap(changed_path, declared) for declared in allowed):
                    errors.append({"code": "BLAST_RADIUS", "message": f"changed path is outside declared scope: {changed_path}"})
    else:
        tier2_reasons.append("BLAST_RADIUS_SKIPPED")

    return {
        "contract": "AcceptancePreflight/v1",
        "ok": not errors,
        "task_id": fm.get("id"),
        "task_revision_digest": task_rev["task_revision_digest"],
        "authorization_ref": fm.get("signed_off_sig"),
        "attempt_id": handoff.get("attempt", {}).get("id") if handoff else None,
        "base_commit": base,
        "dependency_closure": expected_closure,
        "changed_paths": changed,
        "tier2_reasons": sorted(set(tier2_reasons)),
        "warnings": warnings,
        "errors": errors,
        "failure_codes": sorted({error["code"] for error in errors}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--handoff")
    parser.add_argument("--no-blast-radius", action="store_true")
    parser.add_argument("--bookkeeping", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = evaluate(
            pathlib.Path(args.spec), pathlib.Path(args.handoff) if args.handoff else None,
            not args.no_blast_radius, [pathlib.Path(item) for item in args.bookkeeping],
        )
    except (OSError, DataError, ValueError) as exc:
        result = {
            "contract": "AcceptancePreflight/v1", "ok": False,
            "tier2_reasons": [], "warnings": [],
            "errors": [{"code": "HANDOFF_STALE", "message": str(exc)}],
            "failure_codes": ["HANDOFF_STALE"],
        }
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    elif result["ok"]:
        print(f"PREFLIGHT=PASS attempt={result.get('attempt_id') or 'legacy'}")
    else:
        for error in result["errors"]:
            print(f"BLOCK {error['code']} — {error['message']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
