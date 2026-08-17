#!/usr/bin/env python3
"""Generate Converge's non-editable Task-Spec mirror and UPSTREAM.lock.

Converge keeps its methodology/runtime wrappers. Files listed in UPSTREAM.lock
are generated from this repository and must only change by running this export.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_TARGET = pathlib.Path("/Users/luanmorenomaciel/GitHub/converge/skills/task-spec")

MAPPINGS = {
    "src/lib/_lib.sh": "scripts/_lib.sh",
    "src/author/generate-task-spec.sh": "scripts/generate-task-spec.sh",
    "src/author/batch-generate.sh": "scripts/batch-generate.sh",
    "src/author/migrate-legacy-task.sh": "scripts/migrate-legacy-task.sh",
    "src/gate/validate-task-spec.sh": "scripts/validate-task-spec.sh",
    "src/gate/safe-to-delegate.sh": "scripts/safe-to-delegate.sh",
    "src/gate/run-task-spec.sh": "scripts/run-task-spec.sh",
    "src/gate/definition-of-done.sh": "scripts/definition-of-done.sh",
    "src/accept/accept-task.sh": "scripts/accept-task.sh",
    "src/backlog/archive.sh": "scripts/archive.sh",
    "src/backlog/backup-backlog.sh": "scripts/backup-backlog.sh",
    "src/backlog/install-hooks.sh": "scripts/install-hooks.sh",
    "src/backlog/lint-backlog.sh": "scripts/lint-backlog.sh",
    "src/backlog/list-ready.sh": "scripts/list-ready.sh",
    "src/backlog/query-metrics.sh": "scripts/query-metrics.sh",
    "src/backlog/rebuild-state.sh": "scripts/rebuild-state.sh",
    "src/backlog/transition-status.sh": "scripts/transition-status.sh",
    "src/dispatch/conformance-check.sh": "scripts/conformance-check.sh",
    "src/dispatch/ref-executor.sh": "scripts/ref-executor.sh",
    "src/templates/task-spec.md.tpl": "templates/task-spec.md.tpl",
    "spec/schemas/task-spec-frontmatter.schema.json": "references/schemas/task-spec-frontmatter.schema.json",
    "spec/schemas/agent-contract.schema.json": "references/schemas/agent-contract.schema.json",
    "spec/schemas/task-plan.schema.json": "references/schemas/task-plan.schema.json",
    "spec/schemas/task-handoff.schema.json": "references/schemas/task-handoff.schema.json",
    "spec/schemas/authoring-evidence.schema.json": "references/schemas/authoring-evidence.schema.json",
    "docs/concepts/effort-gate.md": "references/concepts/effort-gate.md",
    "docs/concepts/signed-off.md": "references/concepts/signed-off.md",
    "tests/test-effort-sizing.sh": "tests/test-effort-sizing.sh",
    "tests/test-hmac-envelope.sh": "tests/test-hmac-envelope.sh",
}


def transform(source: str, destination: str, data: bytes) -> bytes:
    if not destination.endswith((".sh", ".md", ".tpl")):
        return data
    text = data.decode("utf-8")
    if destination.startswith("scripts/"):
        text = text.replace('__lib_dir/../..', '__lib_dir/..')
        text = text.replace('"$SCRIPT_DIR/../lib/_lib.sh"', '"$SCRIPT_DIR/_lib.sh"')
        text = text.replace('$(dirname "${BASH_SOURCE[0]}")/../lib', '$(dirname "${BASH_SOURCE[0]}")')
        text = text.replace('$(dirname "${BASH_SOURCE[0]}")/../..', '$(dirname "${BASH_SOURCE[0]}")/..')
        text = text.replace('"$SCRIPT_DIR/../gate/run-task-spec.sh"', '"$SCRIPT_DIR/run-task-spec.sh"')
        text = text.replace('"$SCRIPT_DIR/../accept/accept-task.sh"', '"$SCRIPT_DIR/accept-task.sh"')
        text = text.replace('"$SKILL_DIR/src/backlog/rebuild-state.sh"', '"$SKILL_DIR/scripts/rebuild-state.sh"')
        text = text.replace('"$SKILL_DIR/src/gate/validate-task-spec.sh"', '"$SKILL_DIR/scripts/validate-task-spec.sh"')
        text = text.replace('"$SKILL_DIR/src/gate/safe-to-delegate.sh"', '"$SKILL_DIR/scripts/safe-to-delegate.sh"')
        text = text.replace('"$TASKSPEC_SKILL_DIR/src/backlog/rebuild-state.sh"', '"$TASKSPEC_SKILL_DIR/scripts/rebuild-state.sh"')
        text = text.replace('spec/schemas/', 'references/schemas/')
        text = text.replace('docs/concepts/', 'references/concepts/')
    if destination.startswith("tests/"):
        text = text.replace('$SKILL_DIR/src/lib/_lib.sh', '$SKILL_DIR/scripts/_lib.sh')
        text = text.replace('"$SKILL_DIR/src/lib/_lib.sh"', '"$SKILL_DIR/scripts/_lib.sh"')
        text = text.replace('"$SKILL_DIR/src/gate/safe-to-delegate.sh"', '"$SKILL_DIR/scripts/safe-to-delegate.sh"')
        text = text.replace('"$SKILL_DIR/src/gate/validate-task-spec.sh"', '"$SKILL_DIR/scripts/validate-task-spec.sh"')
        text = text.replace('"$ROOT/src/gate/validate-task-spec.sh"', '"$ROOT/scripts/validate-task-spec.sh"')
    text = text.replace('docs/concepts/', 'references/concepts/') if destination.startswith(("templates/", "references/")) else text
    return text.encode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_head() -> str | None:
    try:
        clean = not subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        if clean:
            return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    return None


def build() -> tuple[dict[str, bytes], dict]:
    rendered: dict[str, bytes] = {}
    source_rows = []
    for source, destination in sorted(MAPPINGS.items()):
        raw = (ROOT / source).read_bytes()
        source_rows.append(f"{source}\0{sha(raw)}")
        rendered[destination] = transform(source, destination, raw)
    mapped_hashes = {path: sha(data) for path, data in sorted(rendered.items())}
    lock = {
        "contract": "TaskSpecUpstreamLock/v1",
        "upstream": "https://github.com/luanmorenommaciel/task-spec",
        "release": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "release_tag": "v" + (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "source_commit": git_head(),
        "source_state": "clean_commit" if git_head() else "unpublished_worktree",
        "donor_baseline": {"repository": "converge", "commit": "f78f077"},
        "source_tree_digest": sha("\n".join(source_rows).encode()),
        "mapped_files": mapped_hashes,
        "policy": "Files in mapped_files are generated; Converge-specific wrappers remain editable.",
    }
    marker = (
        "# Generated Task-Spec mirror\n\n"
        "Files listed in `UPSTREAM.lock` come from the standalone Task-Spec "
        f"{lock['release']} export and are not edited here. Converge wrappers "
        "remain local. Run the upstream `tools/export-converge.py` to update or check the mirror.\n"
    ).encode()
    rendered["GENERATED-UPSTREAM.md"] = marker
    lock["mapped_files"]["GENERATED-UPSTREAM.md"] = sha(marker)
    return rendered, lock


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=pathlib.Path, default=DEFAULT_TARGET)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = args.target.resolve()
    rendered, lock = build()
    lock_bytes = (json.dumps(lock, indent=2, sort_keys=True) + "\n").encode()
    problems = []
    for relative, expected in rendered.items():
        path = target / relative
        if not path.is_file() or path.read_bytes() != expected:
            problems.append(relative)
    lock_path = target / "UPSTREAM.lock"
    if not lock_path.is_file() or lock_path.read_bytes() != lock_bytes:
        problems.append("UPSTREAM.lock")
    if args.check:
        if problems:
            print("UPSTREAM_MIRROR=STALE")
            for problem in problems:
                print(f"  {problem}")
            return 1
        print(f"UPSTREAM_MIRROR=OK files={len(rendered)} release={lock['release']}")
        return 0
    for relative, content in rendered.items():
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        if relative.endswith(".sh"):
            path.chmod(0o755)
    lock_path.write_bytes(lock_bytes)
    print(f"UPSTREAM_MIRROR=WRITTEN files={len(rendered)} release={lock['release']} target={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
