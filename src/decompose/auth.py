"""Domain-separated native plan review authentication."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import subprocess


def key_for(root: Path) -> bytes:
    value = os.environ.get("TASKSPEC_SIGNING_KEY", "").strip()
    if not value:
        result = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=root, text=True, capture_output=True, check=False)
        if result.returncode:
            raise ValueError("native review requires a Git workspace; run taskspec init and setup signing")
        directory = Path(result.stdout.strip())
        if not directory.is_absolute():
            directory = root / directory
        path = directory / "info/taskspec-signing-key"
        if not path.is_file():
            raise ValueError("native review requires a signing key; run taskspec setup signing")
        value = path.read_text().strip()
    if not value:
        raise ValueError("native review signing key is empty")
    return value.encode()


def sign(root: Path, record: dict) -> str:
    key = key_for(root)
    payload = {k: v for k, v in record.items() if k != "signature"}
    message = b"TaskPlanReview/v1\n" + json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "hmac-taskplan-v1:" + hashlib.sha256(key).hexdigest()[:8] + ":" + hmac.new(key, message, hashlib.sha256).hexdigest()


def verify(root: Path, record: dict) -> bool:
    try:
        return hmac.compare_digest(str(record.get("signature", "")), sign(root, record))
    except (OSError, ValueError):
        return False


def reviewed_inputs(folder: Path) -> dict[str, str]:
    """Bind the whole reviewed input inventory, including optional original intake.

    The delivery plan and review are bound separately to avoid a signature cycle.
    Generated TaskPlan projections, event logs, and old snapshots are excluded.
    """
    names = ["source-recipe.yaml", "intent.md", "system-map.md", "evidence.jsonl",
             "seam-map.yaml", "steel-thread.md", "proposed-graph.json"]
    if (folder / "intake.md").exists():
        names.append("intake.md")
    for directory in ("decisions", "seams", "swimlanes", "legs"):
        names.extend(str(p.relative_to(folder)) for p in sorted((folder / directory).glob("*.md")))
    result = {}
    for name in sorted(names):
        path = folder / name
        if path.is_symlink() or not path.resolve().is_relative_to(folder.resolve()):
            raise ValueError("reviewed input traverses a symlink: " + name)
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result
