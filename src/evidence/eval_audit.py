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
    if not isinstance(value, dict) or value.get("contract") != "MutationMatrix/v1" or not isinstance(value.get("mutations"), list):
        raise ValueError("mutation matrix must be MutationMatrix/v1 with a mutations list")
    unknown = set(value) - {"contract", "stack", "experimental", "mutations"}
    if unknown:
        raise ValueError(f"mutation matrix has unknown fields: {sorted(unknown)}")
    if value.get("stack") not in {"python", "javascript", "go", "bash", "generic"}:
        raise ValueError("mutation matrix stack must be python, javascript, go, bash, or generic")
    if value.get("experimental") is not True:
        raise ValueError("MutationMatrix/v1 must be explicitly experimental")
    seen: set[str] = set()
    for index, mutation in enumerate(value["mutations"]):
        if not isinstance(mutation, dict) or set(mutation) != {"id", "patch"}:
            raise ValueError(f"mutations[{index}] must contain only id and patch")
        mutation_id, raw_patch = mutation.get("id"), mutation.get("patch")
        if not isinstance(mutation_id, str) or not mutation_id or mutation_id in seen:
            raise ValueError(f"mutations[{index}].id must be non-empty and unique")
        seen.add(mutation_id)
        if not isinstance(raw_patch, str) or not raw_patch:
            raise ValueError(f"mutations[{index}].patch must be a non-empty string")
        pure = pathlib.PurePosixPath(raw_patch)
        if pure.is_absolute() or ".." in pure.parts:
            raise ValueError(f"mutations[{index}].patch must remain inside the matrix directory")
    return value["mutations"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--mutations")
    parser.add_argument("--report")
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()
    spec = pathlib.Path(args.spec).resolve()
    try:
        root = repo_root(spec)
        rel = spec.relative_to(root)
        if not 1 <= args.repeat <= 20: raise ValueError("--repeat must be 1..20")
        current_runs = [run_spec(spec, root) for _ in range(args.repeat)]
        current = {"passed": all(run["passed"] for run in current_runs), "exit_code": current_runs[-1]["exit_code"], "runs": current_runs, "pass_rate": sum(run["passed"] for run in current_runs) / args.repeat}
        cases: list[dict[str, Any]] = [{"id": "current", "expected": "pass", **current}]

        baseline_tree = worktree(root, args.baseline)
        try:
            target_spec = baseline_tree / rel
            target_spec.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(spec, target_spec)
            baseline_runs = [run_spec(target_spec, baseline_tree) for _ in range(args.repeat)]
            observed = {"passed": all(run["passed"] for run in baseline_runs), "exit_code": baseline_runs[-1]["exit_code"], "runs": baseline_runs, "pass_rate": sum(run["passed"] for run in baseline_runs) / args.repeat}
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
                mutation_runs = [run_spec(target_spec, tree) for _ in range(args.repeat)]
                observed = {
                    "passed": all(run["passed"] for run in mutation_runs),
                    "exit_code": mutation_runs[-1]["exit_code"],
                    "runs": mutation_runs,
                    "pass_rate": sum(run["passed"] for run in mutation_runs) / args.repeat,
                }
                cases.append({"id": mutation_id, "patch": str(patch), "expected": "fail", **observed})
            finally:
                remove_worktree(root, tree)

        flaky = any(0 < case.get("pass_rate", int(case.get("passed", False))) < 1 for case in cases)
        discriminating = not flaky and current["passed"] and all(
            not case["passed"] and case.get("exit_code") != 125 for case in cases[1:]
        )
        report = {
            "contract": "EvalAuditReceipt/v1", "spec": str(spec), "baseline_ref": args.baseline,
            "audited_at": now(), "repeat": args.repeat, "flake_detected": flaky,
            "result": "pass" if discriminating else "fail", "cases": cases,
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
