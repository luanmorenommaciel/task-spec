#!/usr/bin/env python3
"""Resolve one Git workspace, backlog, and contained acceptance store."""

from __future__ import annotations

import os
import pathlib
import subprocess
from typing import Mapping


class WorkspaceError(ValueError):
    """Raised when repository authority is ambiguous or escapes its workspace."""


def _inside(path: pathlib.Path, root: pathlib.Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _git_toplevel(path: pathlib.Path) -> pathlib.Path:
    probe = path if path.is_dir() else path.parent
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=probe,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode or not result.stdout.strip():
        raise WorkspaceError("Task-Spec lifecycle requires a Git workspace")
    return pathlib.Path(result.stdout.strip()).resolve()


def resolve_workspace(path: pathlib.Path, environ: Mapping[str, str] | None = None) -> pathlib.Path:
    """Return the repository root and validate any explicit workspace claim."""
    environ = os.environ if environ is None else environ
    candidate = path.resolve()
    git_root = _git_toplevel(candidate)
    configured = environ.get("TASKSPEC_WORKSPACE_ROOT")
    if configured:
        explicit = pathlib.Path(configured)
        if not explicit.is_absolute():
            explicit = pathlib.Path.cwd() / explicit
        try:
            explicit = explicit.resolve(strict=True)
        except OSError as exc:
            raise WorkspaceError(f"TASKSPEC_WORKSPACE_ROOT is unavailable: {configured}") from exc
        if not explicit.is_dir():
            raise WorkspaceError("TASKSPEC_WORKSPACE_ROOT must be a directory")
        if not _inside(candidate, explicit):
            raise WorkspaceError("Task-Spec is outside TASKSPEC_WORKSPACE_ROOT")
        if explicit != git_root:
            raise WorkspaceError("TASKSPEC_WORKSPACE_ROOT must equal the Git repository root")
    if not _inside(candidate, git_root):
        raise WorkspaceError("Task-Spec resolves outside the Git repository root")
    return git_root


def resolve_backlog(
    spec: pathlib.Path,
    workspace: pathlib.Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> pathlib.Path:
    """Return the one backlog containing ``spec``, contained by ``workspace``."""
    environ = os.environ if environ is None else environ
    spec = spec.resolve()
    workspace = (workspace or resolve_workspace(spec, environ)).resolve()
    configured = environ.get("TASKSPEC_BACKLOG_DIR")
    if configured:
        backlog = pathlib.Path(configured)
        if not backlog.is_absolute():
            backlog = workspace / backlog
        try:
            backlog = backlog.resolve(strict=True)
        except OSError as exc:
            raise WorkspaceError(f"TASKSPEC_BACKLOG_DIR is unavailable: {configured}") from exc
        if not backlog.is_dir():
            raise WorkspaceError("TASKSPEC_BACKLOG_DIR must be a directory")
        if not _inside(backlog, workspace):
            raise WorkspaceError("TASKSPEC_BACKLOG_DIR escapes the Git workspace")
        if not _inside(spec, backlog):
            raise WorkspaceError("Task-Spec is outside TASKSPEC_BACKLOG_DIR")
        return backlog
    for parent in spec.parents:
        if parent == workspace.parent:
            break
        if parent.name == "tasks":
            if not _inside(parent, workspace):
                break
            return parent
    raise WorkspaceError("spec is not inside a tasks backlog")


def resolve_acceptance_root(
    workspace: pathlib.Path,
    configured: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> pathlib.Path:
    """Resolve CLI > environment > default acceptance storage inside the workspace."""
    environ = os.environ if environ is None else environ
    workspace = workspace.resolve()
    raw = configured if configured is not None else environ.get("TASKSPEC_ACCEPTANCE_DIR")
    if raw is None or not raw.strip():
        raw = ".taskspec/acceptance"
    declared = pathlib.PurePath(raw)
    if ".." in declared.parts:
        raise WorkspaceError("acceptance directory traversal is forbidden")
    if ".git" in declared.parts:
        raise WorkspaceError("acceptance directory cannot target .git")
    candidate = pathlib.Path(raw)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    candidate = candidate.absolute()
    if candidate.is_symlink():
        resolved_candidate = candidate.resolve()
        if not _inside(resolved_candidate, workspace):
            raise WorkspaceError("acceptance directory escapes through a symlink")
    probe = candidate
    while not probe.exists() and probe != workspace.parent:
        probe = probe.parent
    if not probe.exists():
        raise WorkspaceError("acceptance directory has no existing parent")
    resolved_probe = probe.resolve()
    if not _inside(resolved_probe, workspace):
        if _inside(probe.absolute(), workspace):
            raise WorkspaceError("acceptance directory escapes through a symlink parent")
        raise WorkspaceError("acceptance directory escapes the Git workspace")
    if candidate.exists() or candidate.is_symlink():
        resolved_candidate = candidate.resolve()
        if not _inside(resolved_candidate, workspace):
            raise WorkspaceError("acceptance directory escapes through a symlink")
        candidate = resolved_candidate
    else:
        relative_tail = candidate.relative_to(probe)
        candidate = resolved_probe.joinpath(relative_tail)
    if candidate == workspace:
        raise WorkspaceError("repository root is too broad for acceptance storage")
    return candidate
