#!/usr/bin/env python3
"""Prove an eval set discriminates current work from baselines and mutations."""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUNNER = ROOT / "src" / "gate" / "run-task-spec.sh"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def command(argv: list[str], cwd: pathlib.Path, *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, input=input_text, text=True, capture_output=True, check=False)


def repo_root(spec: pathlib.Path) -> pathlib.Path:
    result = command(["git", "rev-parse", "--show-toplevel"], spec.parent)
    if result.returncode:
        raise ValueError("eval-audit requires a git repository")
    return pathlib.Path(result.stdout.strip()).resolve()


def run_spec(spec: pathlib.Path, cwd: pathlib.Path) -> dict[str, Any]:
    result = command(["bash", str(RUNNER), str(spec)], cwd)
    return {"exit_code": result.returncode, "passed": result.returncode == 0}


def worktree(root: pathlib.Path, ref: str) -> pathlib.Path:
    target = pathlib.Path(tempfile.mkdtemp(prefix="taskspec-audit-"))
    result = command(["git", "worktree", "add", "-q", "--detach", str(target), ref], root)
    if result.returncode:
        shutil.rmtree(target, ignore_errors=True)
        raise ValueError(f"cannot reconstruct ref {ref!r}: {result.stderr.strip()}")
    return target


def remove_worktree(root: pathlib.Path, target: pathlib.Path) -> None:
    result = command(["git", "worktree", "remove", "--force", str(target)], root)
    if result.returncode:
        shutil.rmtree(target, ignore_errors=True)


def load_matrix(path: pathlib.Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("contract") != "MutationMatrix/v1" or not isinstance(value.get("mutations"), list):
        raise ValueError("mutation matrix must be MutationMatrix/v1 with a mutations list")
    return value["mutations"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--mutations")
    parser.add_argument("--report")
    args = parser.parse_args()
    spec = pathlib.Path(args.spec).resolve()
    try:
        root = repo_root(spec)
        rel = spec.relative_to(root)
        current = run_spec(spec, root)
        cases: list[dict[str, Any]] = [{"id": "current", "expected": "pass", **current}]

        baseline_tree = worktree(root, args.baseline)
        try:
            target_spec = baseline_tree / rel
            target_spec.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(spec, target_spec)
            observed = run_spec(target_spec, baseline_tree)
            cases.append({"id": "baseline", "ref": args.baseline, "expected": "fail", **observed})
        finally:
            remove_worktree(root, baseline_tree)

        for mutation in load_matrix(pathlib.Path(args.mutations).resolve() if args.mutations else None):
            mutation_id = mutation.get("id")
            patch = pathlib.Path(str(mutation.get("patch", "")))
            if not patch.is_absolute() and args.mutations:
                patch = pathlib.Path(args.mutations).resolve().parent / patch
            tree = worktree(root, "HEAD")
            try:
                applied = command(["git", "apply", str(patch)], tree)
                if applied.returncode:
                    cases.append({"id": mutation_id, "expected": "fail", "passed": False, "exit_code": 125, "error": "patch did not apply"})
                    continue
                target_spec = tree / rel
                target_spec.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(spec, target_spec)
                observed = run_spec(target_spec, tree)
                cases.append({"id": mutation_id, "patch": str(patch), "expected": "fail", **observed})
            finally:
                remove_worktree(root, tree)

        discriminating = current["passed"] and all(
            not case["passed"] and case.get("exit_code") != 125 for case in cases[1:]
        )
        report = {
            "contract": "EvalAuditReceipt/v1", "spec": str(spec), "baseline_ref": args.baseline,
            "audited_at": now(), "result": "pass" if discriminating else "fail", "cases": cases,
        }
        if args.report:
            out = pathlib.Path(args.report); out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0 if discriminating else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"EVAL_AUDIT=INVALID error={exc}", file=sys.stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())
