#!/usr/bin/env python3
"""Validate, preview, and run reproducible multi-engine Task-Spec evidence matrices."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any

FAMILIES = {"openai", "anthropic", "google", "xai", "deepseek", "kimi", "minimax", "qwen", "glm"}
ROOT = pathlib.Path(__file__).resolve().parents[2]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def git(workspace: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=workspace, text=True, capture_output=True, check=False)


def validate(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if value.get("contract") != "EngineMatrix/v1":
        errors.append("contract must be EngineMatrix/v1")
    engines = value.get("engines")
    if not isinstance(engines, list):
        return errors + ["engines must be a list"]
    seen: set[str] = set()
    for index, engine in enumerate(engines):
        if not isinstance(engine, dict):
            errors.append(f"engines[{index}] must be an object")
            continue
        family = engine.get("family")
        if family not in FAMILIES:
            errors.append(f"engines[{index}].family is unsupported")
        elif family in seen:
            errors.append(f"engine family {family} is duplicated")
        else:
            seen.add(family)
        for field in ("provider", "model_id", "adapter_version", "enabled"):
            if field not in engine:
                errors.append(f"engines[{index}] missing {field}")
        if engine.get("enabled") is True:
            if engine.get("model_id") == "TO_RECORD":
                errors.append(f"engines[{index}].model_id must be exact before the engine is enabled")
            argv = engine.get("argv")
            if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
                errors.append(f"engines[{index}].argv must be a non-empty string list when enabled")
    missing = FAMILIES - seen
    if missing:
        errors.append(f"matrix is missing families: {', '.join(sorted(missing))}")
    return errors


def expand(
    argv: list[str], *, handoff: pathlib.Path, output: pathlib.Path,
    workspace: pathlib.Path | None = None, spec: pathlib.Path | None = None,
) -> list[str]:
    values = {
        "handoff": str(handoff), "output": str(output),
        "workspace": str(workspace or "<isolated-workspace>"),
        "spec": str(spec or "<isolated-spec>"),
    }
    try:
        return [item.format(**values) for item in argv]
    except KeyError as exc:
        raise ValueError(f"unsupported argv placeholder: {exc}") from exc


def isolated_handoff(
    original: dict[str, Any], out_dir: pathlib.Path,
    family: str, source_workspace: pathlib.Path, source_commit: str,
) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    isolated = pathlib.Path(tempfile.mkdtemp(prefix=f"taskspec-{family}-"))
    added = git(source_workspace, "worktree", "add", "-q", "--detach", str(isolated), source_commit)
    if added.returncode:
        shutil.rmtree(isolated, ignore_errors=True)
        raise ValueError(f"cannot create isolated worktree for {family}: {added.stderr.strip()}")
    try:
        original_spec = pathlib.Path(str(original["spec"])).resolve()
        relative_spec = original_spec.relative_to(source_workspace)
        isolated_spec = isolated / relative_spec
        isolated_spec.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original_spec, isolated_spec)  # the sealed handoff spec may be newer than the baseline commit
        staged = git(isolated, "add", str(relative_spec))
        if staged.returncode:
            raise ValueError(f"cannot stage sealed spec overlay for {family}: {staged.stderr.strip()}")
        if git(isolated, "diff", "--cached", "--quiet").returncode != 0:
            committed = git(
                isolated, "-c", "user.name=Task-Spec Evidence", "-c",
                "user.email=evidence@taskspec.invalid", "commit", "-q", "-m", "sealed Task-Spec handoff",
            )
            if committed.returncode:
                raise ValueError(f"cannot commit sealed spec overlay for {family}: {committed.stderr.strip()}")
        copy_handoff = copy.deepcopy(original)
        copy_handoff["workspace"] = str(isolated)
        copy_handoff["spec"] = str(isolated_spec)
        for key in ("eval_command", "acceptance_command"):
            copy_handoff[key] = [str(isolated_spec) if item == str(original_spec) else item for item in copy_handoff.get(key, [])]
        handoff_dir = out_dir / "handoffs"
        handoff_dir.mkdir(parents=True, exist_ok=True)
        handoff_path = handoff_dir / f"{family}.json"
        handoff_path.write_text(json.dumps(copy_handoff, indent=2) + "\n", encoding="utf-8")
        return isolated, isolated_spec, handoff_path
    except Exception:
        git(source_workspace, "worktree", "remove", "--force", str(isolated))
        shutil.rmtree(isolated, ignore_errors=True)
        raise


def remove_worktree(source_workspace: pathlib.Path, isolated: pathlib.Path) -> None:
    removed = git(source_workspace, "worktree", "remove", "--force", str(isolated))
    if removed.returncode:
        shutil.rmtree(isolated, ignore_errors=True)


def changed_file_manifest(workspace: pathlib.Path) -> list[dict[str, Any]]:
    names: set[str] = set()
    for result in (
        git(workspace, "diff", "--name-only", "HEAD"),
        git(workspace, "ls-files", "--others", "--exclude-standard"),
    ):
        if result.returncode == 0:
            names.update(item for item in result.stdout.splitlines() if item)
    manifest: list[dict[str, Any]] = []
    for name in sorted(names):
        path = (workspace / name).resolve()
        try:
            path.relative_to(workspace.resolve())
        except ValueError:
            continue
        if path.is_file():
            manifest.append({"path": name, "bytes": path.stat().st_size, "sha256": digest(path)})
        else:
            manifest.append({"path": name, "state": "deleted-or-non-file"})
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "plan", "run"):
        command = sub.add_parser(name)
        command.add_argument("matrix")
        if name in {"plan", "run"}:
            command.add_argument("--handoff", required=True)
            command.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    try:
        matrix_path = pathlib.Path(args.matrix).resolve()
        matrix = load(matrix_path)
        errors = validate(matrix)
        if errors:
            raise ValueError("; ".join(errors))
        if args.command == "validate":
            print("ENGINE_MATRIX=VALID families=9")
            return 0

        handoff = pathlib.Path(args.handoff).resolve()
        handoff_data = load(handoff)
        out_dir = pathlib.Path(args.out_dir).resolve()
        if handoff_data.get("contract") not in {"TaskHandoff/v1", "TaskHandoff/v2"}:
            raise ValueError("--handoff must be TaskHandoff/v1 or TaskHandoff/v2")
        source_workspace = pathlib.Path(str(handoff_data.get("workspace", ""))).resolve()
        current_spec = pathlib.Path(str(handoff_data.get("spec", ""))).resolve()
        if any(engine.get("enabled") is True for engine in matrix["engines"]) and (
            not current_spec.is_file() or digest(current_spec) != handoff_data.get("spec_digest")
        ):
            raise ValueError("handoff spec digest no longer matches the source workspace; regenerate the frozen handoff")
        source_commit_result = git(source_workspace, "rev-parse", "HEAD")
        if source_commit_result.returncode:
            raise ValueError("handoff workspace must be a git repository for isolated evidence runs")
        source_commit = source_commit_result.stdout.strip()

        plan: list[dict[str, Any]] = []
        for engine in matrix["engines"]:
            target = out_dir / "raw" / f"{engine['family']}.txt"
            plan.append({
                "family": engine["family"], "provider": engine["provider"], "model_id": engine["model_id"],
                "enabled": engine["enabled"], "isolation": "detached-git-worktree" if engine["enabled"] else "not-run",
                "argv": expand(engine.get("argv", []), handoff=handoff, output=target),
            })
        if args.command == "plan":
            print(json.dumps({"contract": "EngineMatrixPlan/v1", "source_commit": source_commit, "runs": plan}, indent=2))
            return 0

        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "raw").mkdir(exist_ok=True)
        (out_dir / "receipts").mkdir(exist_ok=True)
        results: list[dict[str, Any]] = []
        for entry, engine in zip(plan, matrix["engines"]):
            started = now()
            target = out_dir / "raw" / f"{entry['family']}.txt"
            artifacts: list[str] = []
            acceptance = "not_run"
            if not entry["enabled"]:
                terminal, code, stderr = "unavailable", None, "engine disabled; no external claim made"
            else:
                isolated, isolated_spec, run_handoff = isolated_handoff(
                    handoff_data, out_dir, entry["family"], source_workspace, source_commit,
                )
                try:
                    argv = expand(engine["argv"], handoff=run_handoff, output=target, workspace=isolated, spec=isolated_spec)
                    completed = subprocess.run(argv, cwd=isolated, text=True, capture_output=True, check=False, env=os.environ.copy())
                    target.write_text(completed.stdout, encoding="utf-8")
                    terminal, code, stderr = ("pass" if completed.returncode == 0 else "fail"), completed.returncode, completed.stderr[-4000:]
                    status_path = out_dir / "raw" / f"{entry['family']}-status.txt"
                    status_path.write_text(git(isolated, "status", "--short").stdout, encoding="utf-8")
                    patch_path = out_dir / "raw" / f"{entry['family']}.patch"
                    patch_path.write_text(git(isolated, "diff", "--binary", "HEAD").stdout, encoding="utf-8")
                    files_path = out_dir / "raw" / f"{entry['family']}-files.json"
                    files_path.write_text(json.dumps(changed_file_manifest(isolated), indent=2) + "\n", encoding="utf-8")
                    artifacts.extend([str(target), str(status_path), str(patch_path), str(files_path), str(run_handoff)])
                    if terminal == "pass" and engine.get("acceptance_argv"):
                        accept_argv = expand(engine["acceptance_argv"], handoff=run_handoff, output=target, workspace=isolated, spec=isolated_spec)
                        accepted = subprocess.run(accept_argv, cwd=isolated, text=True, capture_output=True, check=False, env=os.environ.copy())
                        acceptance = "accepted" if accepted.returncode == 0 else "rejected"
                        accept_path = out_dir / "raw" / f"{entry['family']}-acceptance.txt"
                        accept_path.write_text(accepted.stdout + accepted.stderr, encoding="utf-8")
                        artifacts.append(str(accept_path))
                finally:
                    remove_worktree(source_workspace, isolated)
            receipt = {
                "contract": "EngineRunReceipt/v1", "run_id": str(uuid.uuid4()),
                "task_id": handoff_data.get("task_id"), "task_digest": handoff_data.get("spec_digest"),
                "handoff_digest": digest(handoff), "source_commit": source_commit,
                "provider": entry["provider"], "model_id": entry["model_id"], "adapter_version": engine["adapter_version"],
                "engine_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
                "environment_digest": matrix.get("environment_digest", "unreported"),
                "started_at": started, "finished_at": now(), "attempts": 0 if terminal == "unavailable" else 1,
                "terminal_outcome": terminal, "acceptance_verdict": acceptance, "artifacts": artifacts,
                "deviations": [
                    f"family={entry['family']}", f"isolation={entry['isolation']}",
                    f"matrix=sha256:{digest(matrix_path)}", f"exit_code={code}",
                    f"stderr=sha256:{hashlib.sha256(stderr.encode()).hexdigest()}",
                ],
            }
            receipt_path = out_dir / "receipts" / f"{entry['family']}.json"
            receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
            results.append(receipt)
        summary = {"contract": "EngineMatrixResult/v1", "matrix_digest": f"sha256:{digest(matrix_path)}", "results": results}
        (out_dir / "results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 0 if all(item["terminal_outcome"] in {"pass", "unavailable"} for item in results) else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ENGINE_MATRIX=INVALID error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
