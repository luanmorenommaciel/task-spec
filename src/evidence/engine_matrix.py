#!/usr/bin/env python3
"""Validate, preview, and run reproducible multi-engine Task-Spec evidence matrices."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from typing import Any

FAMILIES = {"openai", "anthropic", "google", "xai", "deepseek", "kimi", "minimax", "qwen", "glm"}
ROOT = pathlib.Path(__file__).resolve().parents[2]
V2_FAMILIES = {"openai", "anthropic"}
BENCHMARK_RUNTIME_ROOT = pathlib.Path("/tmp/taskspec-3.8.1-engine-matrix").resolve()


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


def validate_v2(value: dict[str, Any], matrix_path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    if value.get("contract") != "EngineMatrix/v2":
        return ["contract must be EngineMatrix/v2"]
    tasks = value.get("tasks")
    engines = value.get("engines")
    if not isinstance(tasks, list) or len(tasks) != 3:
        errors.append("tasks must contain the frozen XS, S, and M cases")
    else:
        efforts = []
        task_ids: set[str] = set()
        for index, task in enumerate(tasks):
            if not isinstance(task, dict):
                errors.append(f"tasks[{index}] must be an object")
                continue
            efforts.append(task.get("effort"))
            task_id = task.get("task_id")
            if not isinstance(task_id, str) or task_id in task_ids:
                errors.append(f"tasks[{index}] has an invalid or duplicate task_id")
            else:
                task_ids.add(task_id)
            raw = task.get("handoff")
            if not isinstance(raw, str):
                errors.append(f"tasks[{index}].handoff must be a path")
                continue
            try:
                handoff = (matrix_path.parent / raw).resolve(strict=True)
                handoff.relative_to(matrix_path.parent.resolve())
                expected = task.get("handoff_digest")
                if expected != f"sha256:{digest(handoff)}":
                    errors.append(f"tasks[{index}] handoff digest does not match")
                data = load(handoff)
                if data.get("contract") != "TaskHandoff/v3" or data.get("task_id") != task_id:
                    errors.append(f"tasks[{index}] does not reference its TaskHandoff/v3")
                if data.get("signoff_tier") != 1 or data.get("authorization", {}).get("tier") != 1:
                    errors.append(f"tasks[{index}] handoff is not Tier 1")
            except (OSError, ValueError) as exc:
                errors.append(f"tasks[{index}] handoff is unavailable: {exc}")
        if efforts != ["XS", "S", "M"]:
            errors.append("tasks must be ordered XS, S, M")
    if not isinstance(engines, list) or len(engines) != 2:
        errors.append("engines must contain exactly OpenAI and Anthropic")
    else:
        seen: set[str] = set()
        for index, engine in enumerate(engines):
            if not isinstance(engine, dict):
                errors.append(f"engines[{index}] must be an object")
                continue
            family = engine.get("family")
            if family not in V2_FAMILIES or family in seen:
                errors.append(f"engines[{index}] has an invalid or duplicate family")
            else:
                seen.add(family)
            if engine.get("adapter") not in {"codex", "claude"}:
                errors.append(f"engines[{index}] has an unsupported adapter")
            if engine.get("max_attempts") != 1:
                errors.append(f"engines[{index}].max_attempts must equal 1")
            budget = engine.get("budget")
            if not isinstance(budget, dict) or not isinstance(budget.get("timeout_sec"), int):
                errors.append(f"engines[{index}] has an invalid budget")
        if seen != V2_FAMILIES:
            errors.append("the OpenAI and Anthropic families are both required")
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
        if copy_handoff.get("contract") == "TaskHandoff/v3":
            copy_handoff["source"]["workspace"] = str(isolated)
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


def run_checked(argv: list[str], cwd: pathlib.Path, env: dict[str, str] | None = None) -> None:
    completed = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False, env=env)
    if completed.returncode:
        raise ValueError(f"{' '.join(argv)} failed: {completed.stderr.strip()}")


def benchmark_snapshot(matrix_path: pathlib.Path, effort: str) -> pathlib.Path:
    path = matrix_path.parent / "benchmark" / "snapshots" / effort.lower()
    if not path.is_dir():
        raise ValueError(f"missing frozen {effort} snapshot")
    return path


def unseal_for_first_commit(text: str) -> str:
    replacements = {
        "signed_off": "false", "signed_off_by": "(none)",
        "signed_off_at": "(none)", "signed_off_sig": "(none)",
    }
    for field, value in replacements.items():
        text = re.sub(rf"^{field}:.*$", f"{field}: {value}", text, flags=re.M)
    return text


def recreate_benchmark_worktree(
    matrix_path: pathlib.Path, task: dict[str, Any], handoff: dict[str, Any]
) -> tuple[pathlib.Path, pathlib.Path]:
    workspace = pathlib.Path(handoff["source"]["workspace"]).resolve()
    try:
        relative = workspace.relative_to(BENCHMARK_RUNTIME_ROOT)
    except ValueError as exc:
        raise ValueError("frozen handoff workspace is outside the benchmark runtime root") from exc
    if len(relative.parts) != 2 or relative.parts[1] != "worktree":
        raise ValueError("frozen handoff workspace has an invalid layout")
    case_root = workspace.parent
    if case_root.exists():
        shutil.rmtree(case_root)
    seed = case_root / "seed"
    bare = case_root / "repo.git"
    snapshot = benchmark_snapshot(matrix_path, task["effort"])
    shutil.copytree(snapshot, seed)
    specs = list((seed / "tasks").glob("*.md"))
    if len(specs) != 1:
        raise ValueError("benchmark snapshot must contain exactly one Task-Spec")
    signed_bytes = specs[0].read_bytes()
    specs[0].write_text(unseal_for_first_commit(signed_bytes.decode("utf-8")), encoding="utf-8")
    run_checked(["git", "init", "-q"], seed)
    run_checked(["git", "config", "user.name", "Task-Spec Benchmark"], seed)
    run_checked(["git", "config", "user.email", "benchmark@taskspec.invalid"], seed)
    run_checked(["git", "add", "."], seed)
    fixed = os.environ.copy()
    fixed.update({"GIT_AUTHOR_DATE": "2026-08-15T00:00:00Z", "GIT_COMMITTER_DATE": "2026-08-15T00:00:00Z"})
    run_checked(["git", "commit", "-q", "-m", "frozen benchmark snapshot"], seed, fixed)
    specs[0].write_bytes(signed_bytes)
    run_checked(["git", "add", "tasks"], seed)
    fixed.update({"GIT_AUTHOR_DATE": "2026-08-15T00:01:00Z", "GIT_COMMITTER_DATE": "2026-08-15T00:01:00Z"})
    run_checked(["git", "commit", "-q", "-m", "seal benchmark task"], seed, fixed)
    run_checked(["git", "clone", "-q", "--bare", str(seed), str(bare)], case_root)
    shutil.rmtree(seed)
    run_checked(["git", f"--git-dir={bare}", "worktree", "add", "-q", "--detach", str(workspace), "HEAD"], case_root)
    if (bare / "info" / "taskspec-signing-key").exists():
        raise ValueError("sanitized benchmark repository unexpectedly contains a signing key")
    head = git(workspace, "rev-parse", "HEAD").stdout.strip()
    if head != handoff["source"]["base_commit"]:
        raise ValueError(f"frozen benchmark base commit drifted: {head}")
    spec = pathlib.Path(handoff["spec"]).resolve()
    if spec.parent.parent != workspace or not spec.is_file():
        raise ValueError("frozen Task-Spec path is not present in the detached worktree")
    if f"sha256:{digest(spec)}" != handoff["spec_digest"]:
        raise ValueError("frozen Task-Spec digest drifted")
    return workspace, spec


def redact(value: str) -> str:
    patterns = [
        r"sk-[A-Za-z0-9_-]{16,}", r"sk-ant-[A-Za-z0-9_-]{16,}",
        r"(?i)(api[_-]?key|token|secret|password)\s*[=:]\s*[^\s\"']+",
    ]
    for pattern in patterns:
        value = re.sub(pattern, "[REDACTED]", value)
    return value


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def version_of(command: str) -> str:
    completed = subprocess.run([command, "--version"], text=True, capture_output=True, check=False)
    return (completed.stdout or completed.stderr).strip().splitlines()[0] if completed.returncode == 0 else "unavailable"


def engine_environment() -> tuple[dict[str, str], dict[str, Any]]:
    env = os.environ.copy()
    removed = []
    for key in list(env):
        upper = key.upper()
        if (
            key.startswith("TASKSPEC_")
            or key in {"SSH_AUTH_SOCK", "GPG_AGENT_INFO"}
            or any(token in upper for token in ("API_KEY", "SIGNING_KEY", "EVALUATOR_KEY"))
        ):
            removed.append(key)
            env.pop(key, None)
    manifest = {
        "contract": "SanitizedEngineEnvironment/v1",
        "credential_values_retained": False,
        "removed_variable_names": sorted(removed),
        "inherited_variable_names": sorted(env),
    }
    return env, manifest


def adapter_command(engine: dict[str, Any], workspace: pathlib.Path) -> tuple[list[str], str]:
    model = engine["model"]
    if engine["adapter"] == "codex":
        return [
            "codex", "exec", "--cd", str(workspace), "--model", model,
            "--sandbox", "workspace-write", "--ephemeral", "--ignore-user-config",
            "--ignore-rules", "--skip-git-repo-check", "--json", "-",
        ], version_of("codex")
    command = [
        "claude", "-p", "--model", model, "--effort", "high", "--safe-mode",
        "--no-session-persistence", "--output-format", "stream-json", "--verbose",
        "--permission-mode", "dontAsk", "--tools", "Read,Edit,Write,Bash",
        "--allowedTools", "Read,Edit,Write,Bash",
    ]
    maximum = engine["budget"].get("max_cost_usd")
    if maximum is not None:
        command.extend(["--max-budget-usd", str(maximum)])
    return command, version_of("claude")


def observed_stream_data(adapter: str, transcript: str, configured_model: str) -> tuple[str | None, dict[str, Any]]:
    observed: str | None = None
    usage: dict[str, Any] = {}
    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if adapter == "claude" and event.get("type") == "system" and isinstance(event.get("model"), str):
            observed = event["model"]
        if adapter == "claude" and event.get("type") == "result":
            usage = {key: event.get(key) for key in ("total_cost_usd", "duration_ms", "usage") if key in event}
        if adapter == "codex" and event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usage = event["usage"]
        model = event.get("model")
        if adapter == "codex" and isinstance(model, str):
            observed = model
    if adapter == "codex" and observed is None:
        observed = configured_model
    return observed, usage


def combined_patch(workspace: pathlib.Path) -> bytes:
    parts = [git(workspace, "diff", "--binary", "HEAD").stdout]
    untracked = git(workspace, "ls-files", "--others", "--exclude-standard").stdout.splitlines()
    for name in sorted(untracked):
        completed = subprocess.run(
            ["git", "diff", "--no-index", "--binary", "/dev/null", name],
            cwd=workspace, text=True, capture_output=True, check=False,
        )
        parts.append(completed.stdout)
    return "".join(parts).encode("utf-8")


def overlaps(changed: str, declared: str) -> bool:
    return changed == declared or changed.startswith(declared.rstrip("/") + "/")


def scope_violation(manifest: list[dict[str, Any]], handoff: dict[str, Any]) -> bool:
    scope = handoff["write_scope"]
    allowed = list(scope.get("touches_paths", [])) + list(scope.get("creates_paths", []))
    forbidden = list(scope.get("do_not_touch", []))
    return any(
        any(overlaps(row["path"], item) for item in forbidden)
        or not any(overlaps(row["path"], item) for item in allowed)
        for row in manifest
    )


def signing_key_path() -> pathlib.Path:
    configured = os.environ.get("TASKSPEC_EVIDENCE_SIGNING_KEY")
    if configured:
        key = pathlib.Path(configured).expanduser().resolve()
        if not key.is_file():
            raise ValueError("TASKSPEC_EVIDENCE_SIGNING_KEY is unavailable")
        return key
    common = git(ROOT, "rev-parse", "--git-common-dir")
    if common.returncode:
        raise ValueError("cannot resolve the host-side Task-Spec signing key")
    path = pathlib.Path(common.stdout.strip())
    if not path.is_absolute():
        path = ROOT / path
    key = path.resolve() / "info" / "taskspec-signing-key"
    if not key.is_file():
        raise ValueError("host-side Task-Spec signing key is unavailable")
    return key


def execute_v2_attempt(
    matrix_path: pathlib.Path, task: dict[str, Any], engine: dict[str, Any], out_dir: pathlib.Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    handoff_path = (matrix_path.parent / task["handoff"]).resolve()
    handoff = load(handoff_path)
    attempt_id = handoff["attempt"]["id"]
    if engine.get("enabled") is not True:
        empty = hashlib.sha256(b"").hexdigest()
        attempt = {
            "task_id": task["task_id"], "attempt_id": attempt_id, "status": "unavailable",
            "handoff_digest": task["handoff_digest"], "command_digest": f"sha256:{empty}",
            "patch_digest": None, "transcript_digest": f"sha256:{empty}", "duration_sec": 0,
            "scope_violation": False, "failure_code": "ENGINE_DISABLED",
        }
        return attempt, {"state": "unavailable", "observed_model": None, "adapter_version": "disabled"}
    if shutil.which(engine["adapter"]) is None:
        empty = hashlib.sha256(b"").hexdigest()
        attempt = {
            "task_id": task["task_id"], "attempt_id": attempt_id, "status": "unavailable",
            "handoff_digest": task["handoff_digest"], "command_digest": f"sha256:{empty}",
            "patch_digest": None, "transcript_digest": f"sha256:{empty}", "duration_sec": 0,
            "scope_violation": False, "failure_code": "ADAPTER_UNAVAILABLE",
        }
        return attempt, {"state": "unavailable", "observed_model": None, "adapter_version": "unavailable"}

    workspace, spec = recreate_benchmark_worktree(matrix_path, task, handoff)
    command, adapter_version = adapter_command(engine, workspace)
    environment, environment_manifest = engine_environment()
    prompt = (
        "Execute exactly one frozen TaskHandoff/v3. Work only in the declared workspace and write scope. "
        "Do not edit or commit the Task-Spec, do not inspect parent directories, do not create sessions or subagents, "
        "and run the declared Exit Check before reporting. The independent host gate decides acceptance.\n\n"
        + json.dumps(handoff, indent=2, ensure_ascii=False)
    )
    command_manifest = {
        "contract": "SanitizedEngineCommand/v1", "argv": command,
        "cwd": str(workspace), "handoff_digest": task["handoff_digest"],
        "stdin": "<TaskHandoff/v3 prompt>",
    }
    started = time.monotonic()
    timed_out = False
    try:
        completed = subprocess.run(
            command, cwd=workspace, input=prompt, text=True, capture_output=True,
            check=False, env=environment, timeout=engine["budget"]["timeout_sec"],
        )
        exit_code = completed.returncode
        combined = completed.stdout + ("\n[stderr]\n" + completed.stderr if completed.stderr else "")
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        combined = stdout + ("\n[stderr]\n" + stderr if stderr else "")
    duration = int(math.ceil(time.monotonic() - started))
    sanitized = redact(combined)
    raw_dir = out_dir / "raw" / engine["family"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = raw_dir / f"{task['effort'].lower()}.jsonl"
    transcript_path.write_text(sanitized, encoding="utf-8")

    manifest = changed_file_manifest(workspace)
    violated = scope_violation(manifest, handoff)
    patch = combined_patch(workspace)
    patch_path = raw_dir / f"{task['effort'].lower()}.patch"
    patch_path.write_bytes(patch)
    files_path = raw_dir / f"{task['effort'].lower()}-files.json"
    files_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    accept_env = os.environ.copy()
    accept_env.update({
        "TASKSPEC_SIGNING_KEY": str(signing_key_path()),
        "TASKSPEC_WORKSPACE_ROOT": str(workspace),
    })
    accepted = subprocess.run(
        [str(ROOT / "bin" / "taskspec"), "accept", "--stamp", "--handoff", str(handoff_path), str(spec)],
        cwd=workspace, text=True, capture_output=True, check=False, env=accept_env,
    )
    acceptance_text = accepted.stdout + accepted.stderr
    acceptance_path = raw_dir / f"{task['effort'].lower()}-acceptance.txt"
    acceptance_path.write_text(redact(acceptance_text), encoding="utf-8")
    observed_model, usage = observed_stream_data(engine["adapter"], sanitized, engine["model"])
    if violated:
        status, failure_code = "rejected", "SCOPE_VIOLATION"
    elif accepted.returncode == 0:
        status, failure_code = "accepted", None
    elif timed_out:
        status, failure_code = "failed", "TIMEOUT"
    else:
        failure = re.search(r"ACCEPTANCE_FAILURE=([A-Z_]+)", acceptance_text)
        status, failure_code = "rejected", failure.group(1) if failure else "ACCEPTANCE_REJECTED"
    attempt = {
        "task_id": task["task_id"], "attempt_id": attempt_id, "status": status,
        "handoff_digest": task["handoff_digest"], "command_digest": canonical_digest(command_manifest),
        "patch_digest": "sha256:" + hashlib.sha256(patch).hexdigest() if patch else None,
        "transcript_digest": "sha256:" + hashlib.sha256(sanitized.encode("utf-8")).hexdigest(),
        "duration_sec": duration, "scope_violation": violated, "failure_code": failure_code,
    }
    detail = {
        "task_id": task["task_id"], "effort": task["effort"], "attempt_id": attempt_id,
        "adapter_exit_code": exit_code, "adapter_version": adapter_version,
        "configured_model": engine["model"], "observed_model": observed_model,
        "usage": usage, "command": command_manifest, "environment": environment_manifest,
        "changed_files": manifest, "acceptance_exit_code": accepted.returncode,
        "acceptance_digest": "sha256:" + hashlib.sha256(acceptance_text.encode("utf-8")).hexdigest(),
        "artifacts": {
            "transcript": str(transcript_path), "patch": str(patch_path),
            "changed_files": str(files_path), "acceptance": str(acceptance_path),
        },
    }
    return attempt, detail


def run_v2(matrix_path: pathlib.Path, matrix: dict[str, Any], out_dir: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    detail_rows = []
    scope_violations = 0
    for engine in matrix["engines"]:
        attempts = []
        observed_model = None
        adapter_version = "unavailable"
        for task in matrix["tasks"]:
            attempt, detail = execute_v2_attempt(matrix_path, task, engine, out_dir)
            attempts.append(attempt)
            detail_rows.append({"family": engine["family"], **detail})
            observed_model = detail.get("observed_model") or observed_model
            adapter_version = detail.get("adapter_version", adapter_version)
            scope_violations += int(attempt["scope_violation"])
        accepted_count = sum(item["status"] == "accepted" for item in attempts)
        if engine.get("enabled") is not True:
            state = "disabled"
        elif all(item["status"] == "unavailable" for item in attempts):
            state = "unavailable"
        else:
            state = "pass" if accepted_count >= 2 and not any(item["scope_violation"] for item in attempts) else "fail"
        results.append({
            "family": engine["family"], "adapter_version": adapter_version,
            "observed_model": observed_model, "state": state,
            "attempts": attempts, "accepted_count": accepted_count,
        })
    families_passing = sum(item["state"] == "pass" for item in results)
    summary = {
        "required_families": 2, "families_passing": families_passing,
        "scope_violations": scope_violations,
        "passed": families_passing == 2 and scope_violations == 0,
    }
    result = {
        "contract": "EngineMatrixResult/v2", "matrix_digest": f"sha256:{digest(matrix_path)}",
        "generated_at": now(), "results": results, "summary": summary,
    }
    detail = {
        "contract": "EngineMatrixArtifacts/v1", "matrix_digest": result["matrix_digest"],
        "generated_at": result["generated_at"], "raw_artifacts_committed": False,
        "attempts": detail_rows,
        "limits": [
            "Synthetic evidence is not production reliability.",
            "A supervised host worktree is not a security sandbox.",
            "Only one attempt per engine and task was executed; no retries were removed.",
        ],
    }
    return result, detail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "plan", "run"):
        command = sub.add_parser(name)
        command.add_argument("matrix")
        if name in {"plan", "run"}:
            command.add_argument("--handoff")
            command.add_argument("--out-dir", required=True)
        if name == "run":
            command.add_argument("--result")
            command.add_argument("--artifacts")
    args = parser.parse_args()
    try:
        matrix_path = pathlib.Path(args.matrix).resolve()
        matrix = load(matrix_path)
        if matrix.get("contract") == "EngineMatrix/v2":
            errors = validate_v2(matrix, matrix_path)
            if errors:
                raise ValueError("; ".join(errors))
            if args.command == "validate":
                print("ENGINE_MATRIX=VALID contract=EngineMatrix/v2 tasks=3 families=2")
                return 0
            out_dir = pathlib.Path(args.out_dir).resolve()
            if args.command == "plan":
                runs = [
                    {
                        "family": engine["family"], "adapter": engine["adapter"],
                        "model": engine["model"], "enabled": engine["enabled"],
                        "tasks": [task["task_id"] for task in matrix["tasks"]],
                        "max_attempts_per_task": 1,
                    }
                    for engine in matrix["engines"]
                ]
                print(json.dumps({
                    "contract": "EngineMatrixPlan/v2", "matrix_digest": f"sha256:{digest(matrix_path)}",
                    "runs": runs, "raw_output": str(out_dir),
                }, indent=2))
                return 0
            result, artifacts = run_v2(matrix_path, matrix, out_dir)
            result_path = pathlib.Path(args.result).resolve() if args.result else out_dir / "results.json"
            artifact_path = pathlib.Path(args.artifacts).resolve() if args.artifacts else out_dir / "artifacts.json"
            result_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            artifact_path.write_text(json.dumps(artifacts, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(result, indent=2))
            return 0 if result["summary"]["passed"] else 1

        errors = validate(matrix)
        if errors:
            raise ValueError("; ".join(errors))
        if args.command == "validate":
            print("ENGINE_MATRIX=VALID families=9")
            return 0

        if not args.handoff:
            raise ValueError("EngineMatrix/v1 plan and run require --handoff")
        handoff = pathlib.Path(args.handoff).resolve()
        handoff_data = load(handoff)
        out_dir = pathlib.Path(args.out_dir).resolve()
        if handoff_data.get("contract") not in {"TaskHandoff/v1", "TaskHandoff/v2", "TaskHandoff/v3"}:
            raise ValueError("--handoff must be TaskHandoff/v1, v2, or v3")
        source_workspace = pathlib.Path(str(
            handoff_data.get("source", {}).get("workspace") or handoff_data.get("workspace", "")
        )).resolve()
        current_spec = pathlib.Path(str(handoff_data.get("spec", ""))).resolve()
        expected_spec_digest = str(handoff_data.get("spec_digest", ""))
        if expected_spec_digest.startswith("sha256:"):
            expected_spec_digest = expected_spec_digest[len("sha256:"):]
        if any(engine.get("enabled") is True for engine in matrix["engines"]) and (
            not current_spec.is_file() or digest(current_spec) != expected_spec_digest
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
                "contract": "EngineRunReceipt/v2" if handoff_data.get("contract") == "TaskHandoff/v3" else "EngineRunReceipt/v1",
                "run_id": str(uuid.uuid4()),
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
            if handoff_data.get("contract") == "TaskHandoff/v3":
                receipt.update({
                    "subject": {
                        "task_id": handoff_data["task_id"],
                        "task_revision_digest": handoff_data["task_revision_digest"],
                        "authorization_ref": handoff_data["authorization"]["ref"],
                        "attempt_id": handoff_data["attempt"]["id"],
                        "base_commit": handoff_data["source"]["base_commit"],
                    },
                    "observed_at": now(),
                })
            else:
                receipt.update({
                    "task_id": handoff_data.get("task_id"),
                    "task_digest": handoff_data.get("spec_digest"),
                })
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
