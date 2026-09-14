"""Stdlib-only verification of native planning provenance at the atomic boundary."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src/lib"))
from decompose.auth import verify, reviewed_inputs  # noqa: E402
from taskspec_data import DataError, load_document, canonical_digest  # noqa: E402


def owned(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise DataError("native provenance path escapes workspace")
    current = root
    for part in path.parts:
        current /= part
        if current.is_symlink(): raise DataError("native provenance may not traverse symlinks")
    return current


def initiative_folder(root: Path, initiative: str) -> Path:
    if not isinstance(initiative, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", initiative):
        raise DataError("invalid native initiative identifier")
    return owned(root, "tasks/.plans/" + initiative)


def verify_bundle(root: Path, manifest: Path) -> dict:
    plan = load_document(manifest)
    initiative = plan.get("metadata", {}).get("native_initiative")
    folder = initiative_folder(root, initiative)
    if manifest.resolve() != (folder / "task-plan.json").resolve():
        raise DataError("native TaskPlan must be materialized from its owned initiative bundle")
    bundle = load_document(folder / "bundle.json")
    if bundle.get("contract") != "TaskPlanBundle/v1" or not verify(root, bundle):
        raise DataError("native plan bundle authentication failed")
    review = load_document(folder / "reviews/delivery-plan-review.json")
    if not verify(root, review): raise DataError("native review authentication failed")
    if review.get("artifacts_sha256") != reviewed_inputs(folder):
        raise DataError("native reviewed input content or inventory changed")
    for name, field in (("delivery-plan.yaml", "plan_sha256"), ("proposed-graph.json", "topology_sha256"), ("source-recipe.yaml", "recipe_sha256")):
        if hashlib.sha256((folder / name).read_bytes()).hexdigest() != review.get(field):
            raise DataError("native reviewed snapshot changed: " + name)
    lineage = load_document(folder / "task-plan-lineage.json")
    if bundle.get("plan_digest") != canonical_digest(plan) or bundle.get("lineage_digest") != canonical_digest(lineage):
        raise DataError("native plan or lineage changed after review")
    ids = {u["id"] for u in plan["units"]}
    if ids != set(lineage.get("units", {})) or ids != set(bundle.get("units", {})):
        raise DataError("native lineage must map every unit exactly once")
    for unit in plan["units"]:
        verify_task(root, unit["id"], unit.get("provenance"))
    return plan


def verify_task(root: Path, task_id: str, provenance: object) -> dict:
    if not isinstance(provenance, dict) or provenance.get("contract") != "TaskPlanProvenance/v1":
        raise DataError("native task requires TaskPlanProvenance/v1")
    folder = initiative_folder(root, provenance.get("initiative"))
    snapshot_path = owned(root, provenance.get("snapshot", ""))
    if snapshot_path.parent != folder / "snapshots": raise DataError("snapshot is outside its initiative")
    snapshot = load_document(snapshot_path)
    if canonical_digest(snapshot) != provenance.get("snapshot_digest") or not verify(root, snapshot):
        raise DataError("native snapshot authentication failed")
    row = snapshot.get("units", {}).get(task_id)
    if not row or row.get("projection_digest") != provenance.get("projection_digest") or canonical_digest(row["projection"]) != row["projection_digest"]:
        raise DataError("native unit projection does not match its signed snapshot")
    current = load_document(folder / "bundle.json")
    if not verify(root, current): raise DataError("current native plan bundle authentication failed")
    if current.get("units", {}).get(task_id) != row["projection_digest"]:
        raise DataError("native task scope changed or was removed; review a successor and reauthorize")
    # Recheck only sources applicable to this leaf. Unrelated siblings do not revoke it.
    projection = row["projection"]
    references = [projection.get("intent", {}).get("source", {})] + [e.get("source", {}) for e in projection.get("evidence", [])]
    for reference in references:
        uri = reference.get("uri", "")
        if uri and "://" not in uri:
            source = owned(root, uri)
            if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != reference.get("sha256"):
                raise DataError("applicable source evidence changed or is missing: " + uri)
    return projection
