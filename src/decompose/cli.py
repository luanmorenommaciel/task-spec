#!/usr/bin/env python3
"""Compile evidence-backed initiatives without delegating authority to a model."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src/lib"))


def workspace() -> Path:
    if os.environ.get("TASKSPEC_WORKSPACE_ROOT"):
        return Path(os.environ["TASKSPEC_WORKSPACE_ROOT"]).resolve()
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
    return Path(result.stdout.strip()).resolve() if result.returncode == 0 else Path.cwd().resolve()


def digest(data: object) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def require_result(result, allow_review: bool = False) -> dict:
    if not result.ok and not (allow_review and result.token == "DELIVERY_PLAN=NEEDS_REVIEW"):
        raise ValueError("; ".join(f"{d.code}: {d.message}" for d in result.diagnostics) or result.token)
    return result.as_dict()


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="action", required=True)
    for action in ("init", "prepare", "review", "compile", "status", "impact", "import", "graph", "bundle-check"):
        cmd = sub.add_parser(action)
        cmd.add_argument("initiative")
        if action == "init": cmd.add_argument("--intent-file", required=True)
        if action == "prepare":
            cmd.add_argument("--recipe", required=True); cmd.add_argument("--replace", action="store_true")
        if action == "review":
            cmd.add_argument("--accept", action="store_true", required=True)
            cmd.add_argument("--reviewer", required=True); cmd.add_argument("--reason", required=True)
        if action == "import": cmd.add_argument("--source", required=True)
        if action == "impact": cmd.add_argument("--against", required=True)
        if action == "graph": cmd.add_argument("--view", choices=("tasks", "capabilities"), default="tasks")
    return p


def prepare(root: Path, initiative: str, source: Path, replace: bool, dry: bool) -> dict:
    from decompose.engine import map_recipe, build_plan
    from decompose.workspace import init_workspace
    from decompose.io import strict_yaml_load
    from decompose.safety import path_boundary_diagnostics
    from decompose.paths import PLAN_DIR
    raw = source.read_bytes()
    recipe = strict_yaml_load(raw.decode())
    if not isinstance(recipe, dict): raise ValueError("recipe must be a mapping")
    target = root / PLAN_DIR
    if path_boundary_diagnostics(root, [target]): raise ValueError("unsafe initiative path")
    if (target / "seam-map.yaml").exists() and not replace:
        raise ValueError("initiative already prepared; use impact and explicit prepare --replace after reviewing the revision")
    # Build a private projection using only the declared local source/write inputs.
    # Failed validation leaves the live initiative untouched.
    with tempfile.TemporaryDirectory(prefix="taskspec-prepare-") as directory:
        staged = Path(directory).resolve()
        def seed(value):
            if isinstance(value, dict):
                uri = value.get("uri")
                if isinstance(uri, str) and "://" in uri:
                    raise ValueError("native source evidence requires a workspace-relative immutable snapshot: " + uri)
                if isinstance(uri, str):
                    relative = Path(uri)
                    if relative.is_absolute() or ".." in relative.parts: raise ValueError("source escapes workspace")
                    origin = root / relative
                    if origin.is_symlink() or not origin.resolve().is_relative_to(root): raise ValueError("source traverses a symlink or escapes workspace")
                    if origin.is_file():
                        dest = staged / relative; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(origin, dest)
                for field in ("touches_paths",):
                    for item in value.get(field, []):
                        relative = Path(item)
                        if relative.is_absolute() or ".." in relative.parts: raise ValueError("write path escapes workspace")
                        origin = root / relative; dest = staged / relative
                        if origin.is_symlink() or not origin.resolve().is_relative_to(root): raise ValueError("write input traverses a symlink or escapes workspace")
                        if origin.is_file(): dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(origin, dest)
                        elif origin.is_dir(): dest.mkdir(parents=True, exist_ok=True)
                for child in value.values(): seed(child)
            elif isinstance(value, list):
                for child in value: seed(child)
        seed(recipe)
        # Existing creates are valid only for the same authenticated prior unit.
        prior_creates = {}
        if (target / "bundle.json").is_file():
            from decompose.auth import verify
            previous_plan = json.loads((target / "task-plan.json").read_text())
            previous_bundle = json.loads((target / "bundle.json").read_text())
            if verify(root, previous_bundle) and digest(previous_plan) == previous_bundle.get("plan_digest"):
                prior_creates = {u["id"]: set(u.get("creates_paths", [])) for u in previous_plan["units"]}
        def check_creates(value):
            if isinstance(value, dict):
                for item in value.get("creates_paths", []):
                    if (root / item).exists() and item not in prior_creates.get(value.get("id"), set()): raise ValueError(f"declared creation already exists: {item}")
                for child in value.values(): check_creates(child)
            elif isinstance(value, list):
                for child in value: check_creates(child)
        check_creates(recipe)
        require_result(init_workspace(staged))
        staged_source = staged / PLAN_DIR / "source-recipe.yaml"
        staged_source.write_bytes(raw)
        require_result(map_recipe(staged, staged_source))
        data = require_result(build_plan(staged), allow_review=True)
        from decompose.engine.planning import verify_plan
        from decompose.engine.compilation import derive_task_bundle
        proposed, errors = verify_plan(staged, require_review=False)
        if proposed is None: raise ValueError("; ".join(d.message for d in errors))
        _, graph, errors = derive_task_bundle(staged, proposed)
        if errors: raise ValueError("; ".join(d.message for d in errors))
        (staged / PLAN_DIR / "proposed-graph.json").write_text(json.dumps(graph, indent=2) + "\n")
        if not dry:
            target.parent.mkdir(parents=True, exist_ok=True)
            incoming = Path(tempfile.mkdtemp(prefix=f".{initiative}-incoming-", dir=target.parent))
            shutil.copytree(staged / PLAN_DIR, incoming, dirs_exist_ok=True)
            if target.exists():
                # Preserve old immutable review and bundle snapshots on replacement.
                for name in ("snapshots", "migration", "intake.md"):
                    old = target / name
                    if old.is_dir(): shutil.copytree(old, incoming / name, dirs_exist_ok=True)
                    elif old.is_file(): shutil.copyfile(old, incoming / name)
            backup = target.with_name("." + initiative + ".previous")
            if backup.exists(): raise ValueError(f"interrupted replacement requires recovery: {backup}")
            if target.exists(): target.rename(backup)
            try: incoming.rename(target)
            except BaseException:
                if backup.exists(): backup.rename(target)
                raise
            if backup.exists(): shutil.rmtree(backup)
        return {"contract": "TaskDecompositionResult/v1", "initiative": initiative, "state": "needs_review", "dry_run": dry, "next": [f"taskspec decompose review {initiative} --accept --reviewer <name> --reason <reason>"], "diagnostics": data.get("diagnostics", [])}


def compile_bundle(root: Path, initiative: str, dry: bool) -> dict:
    from decompose.engine import compile_graph
    from decompose.io import load_json, load_yaml
    from decompose.auth import sign
    from decompose.paths import PLAN_DIR
    folder = root / PLAN_DIR
    source = folder / "source-recipe.yaml"
    seam_map = load_yaml(folder / "seam-map.yaml")
    if hashlib.sha256(source.read_bytes()).hexdigest() != seam_map["source_recipe"]["sha256"]:
        raise ValueError("authored recipe changed after prepare; prepare --replace and review the new snapshot")
    from decompose.engine.recipe import _verify_local_recipe_sources
    source_errors = _verify_local_recipe_sources(root, source, load_yaml(source))
    if source_errors: raise ValueError("; ".join(d.message for d in source_errors))
    if dry:
        return require_result(compile_graph(root, dry_run=True))
    require_result(compile_graph(root))
    plan = load_json(folder / "task-plan.json")
    lineage = load_json(folder / "task-plan-lineage.json")
    recipe = load_yaml(folder / "source-recipe.yaml")
    units = {}
    for seam in recipe["seams"]:
        lane = seam["swimlane"]
        for leg in lane["legs"]:
            for task in leg["tasks"]:
                unit = next(item for item in plan["units"] if item["id"] == task["id"])
                projection = {
                    "unit": json.loads(json.dumps(unit)), "intent": recipe["intent"],
                    "original_intake": (folder / "intake.md").read_text() if (folder / "intake.md").exists() else None,
                    "decisions": [d for d in recipe["decisions"] if d["id"] in seam.get("decision_ids", [])],
                    "seam": {k: v for k, v in seam.items() if k != "swimlane"},
                    "lane": {k: v for k, v in lane.items() if k != "legs"},
                    "leg": {k: v for k, v in leg.items() if k != "tasks"},
                    "evidence": [e for e in recipe["evidence"] if e["id"] in seam.get("evidence", [])],
                }
                units[task["id"]] = {"projection_digest": digest(projection), "projection": projection}
    reviewed_artifacts = {}
    from decompose.auth import reviewed_inputs
    names = list(reviewed_inputs(folder)) + ["delivery-plan.yaml", "reviews/delivery-plan-review.json"]
    for name in names:
        raw = (folder / name).read_bytes()
        reviewed_artifacts[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "content": raw.decode()}
    snapshot = {"contract": "TaskPlanSnapshot/v1", "initiative": initiative, "review": load_json(folder / "reviews/delivery-plan-review.json"), "reviewed_artifacts": reviewed_artifacts, "units": units}
    snapshot["signature"] = sign(root, snapshot)
    snapshot_digest = digest(snapshot)
    snapshots = folder / "snapshots"; snapshots.mkdir(exist_ok=True)
    snapshot_path = snapshots / (snapshot_digest + ".json")
    if snapshot_path.exists() and digest(load_json(snapshot_path)) != snapshot_digest: raise ValueError("immutable snapshot collision or tampering")
    if not snapshot_path.exists(): snapshot_path.write_text(json.dumps(snapshot, indent=2) + "\n")
    for unit in plan["units"]:
        relevant = units[unit["id"]]["projection"]
        unit["context"] += "\n\nApplicable intent, capability, and evidence: " + json.dumps({k: v for k, v in relevant.items() if k != "unit"}, sort_keys=True)
        unit["provenance"] = {"contract": "TaskPlanProvenance/v1", "initiative": initiative, "snapshot": str(snapshot_path.relative_to(root)), "snapshot_digest": snapshot_digest, "projection_digest": units[unit["id"]]["projection_digest"]}
    plan["metadata"]["native_initiative"] = initiative
    lineage["task_plan"]["digest"] = digest(plan)
    bundle = {"contract": "TaskPlanBundle/v1", "initiative": initiative, "plan_digest": digest(plan), "lineage_digest": digest(lineage), "snapshot_digest": snapshot_digest, "units": {key: value["projection_digest"] for key, value in units.items()}}
    bundle["signature"] = sign(root, bundle)
    from decompose.io import TransactionWriter, workspace_lock
    with workspace_lock(root):
        writer = TransactionWriter()
        writer.json(folder / "task-plan.json", plan); writer.json(folder / "task-plan-lineage.json", lineage); writer.json(folder / "bundle.json", bundle); writer.commit()
    return {"contract": "TaskDecompositionResult/v1", "initiative": initiative, "state": "compiled", "plan": str(folder / "task-plan.json"), "snapshot": str(snapshot_path), "dispatch_authorized": False, "next": [f"taskspec plan --manifest {PLAN_DIR}/task-plan.json", f"taskspec batch --plan {PLAN_DIR}/task-plan.json"]}


def main() -> int:
    args = parser().parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", args.initiative):
        print("DECOMPOSE=INVALID initiative must be a lowercase identifier", file=sys.stderr); return 2
    os.environ["TASKSPEC_INITIATIVE"] = args.initiative
    lock = contextlib.ExitStack()
    try:
        import yaml  # noqa: F401
        from decompose.paths import PLAN_DIR
        from decompose.io import load_json, load_yaml, workspace_lock
        from decompose.engine import accept_plan, verify_plan
        from decompose.safety import workspace_boundary_diagnostics
        root = workspace(); folder = root / PLAN_DIR
        dry = os.environ.get("TASKSPEC_DRY_RUN") == "1"
        lock.enter_context(workspace_lock(root, dry_run=dry or args.action in {"status", "impact", "graph", "bundle-check"}))
        if workspace_boundary_diagnostics(root): raise ValueError("unsafe initiative workspace (symlink or invalid managed path)")
        if args.action == "init":
            raw = sys.stdin.read() if args.intent_file == "-" else Path(args.intent_file).read_text()
            if not raw.strip(): raise ValueError("intent must be nonblank")
            if folder.exists(): raise ValueError("initiative already exists")
            if not dry: folder.mkdir(parents=True); (folder / "intake.md").write_text(raw)
            data = {"contract": "TaskDecompositionResult/v1", "initiative": args.initiative, "state": "intent", "dry_run": dry, "next": [f"taskspec decompose prepare {args.initiative} --recipe <file>"]}
        elif args.action == "prepare":
            data = prepare(root, args.initiative, Path(args.recipe).resolve(), args.replace, dry)
        elif args.action == "review":
            from decompose.engine.compilation import derive_task_bundle
            proposed, errors = verify_plan(root, require_review=False)
            if proposed is None: raise ValueError("; ".join(d.message for d in errors))
            _, graph, errors = derive_task_bundle(root, proposed)
            if errors or graph != load_json(folder / "proposed-graph.json"):
                raise ValueError("proposed topology changed or is invalid; prepare --replace before review")
            source_sha = hashlib.sha256((folder / "source-recipe.yaml").read_bytes()).hexdigest()
            if source_sha != load_yaml(folder / "seam-map.yaml")["source_recipe"]["sha256"]:
                raise ValueError("authored recipe changed; prepare --replace before review")
            data = require_result(accept_plan(root, reviewer=args.reviewer, reason=args.reason, dry_run=dry))
            data["next"] = [f"taskspec decompose compile {args.initiative}"]
        elif args.action == "compile": data = compile_bundle(root, args.initiative, dry)
        elif args.action == "import":
            source = Path(args.source).resolve(); legacy = source / "seamwise" if (source / "seamwise").is_dir() else source
            recipe_path = legacy / "source-recipe.yaml"
            if not recipe_path.exists():
                candidates = list(source.glob("*.yaml"))
                candidates = [p for p in candidates if isinstance(load_yaml(p), dict) and "seams" in load_yaml(p)]
                if len(candidates) != 1: raise ValueError("import requires the original authored recipe (source-recipe.yaml or one recipe YAML at --source)")
                recipe_path = candidates[0]
            if folder.exists(): raise ValueError("import target exists; choose a new initiative")
            if legacy == root or legacy in folder.parents or folder in legacy.parents:
                raise ValueError("import source overlaps destination workspace")
            original_files = sorted(p for p in legacy.rglob("*") if p.is_file())
            if any(p.is_symlink() for p in legacy.rglob("*")):
                raise ValueError("legacy workspace contains symlinks")
            source_manifest = {str(p.relative_to(legacy)): hashlib.sha256(p.read_bytes()).hexdigest() for p in original_files}
            data = prepare(root, args.initiative, recipe_path, False, dry)
            if not dry:
                try:
                    migration = folder / "migration"; migration.mkdir()
                    shutil.copytree(legacy, migration / "original", symlinks=True)
                    copied = migration / "original"
                    if any(p.is_symlink() for p in copied.rglob("*")):
                        raise ValueError("legacy workspace changed to contain a symlink")
                    copied_manifest = {str(p.relative_to(copied)): hashlib.sha256(p.read_bytes()).hexdigest() for p in copied.rglob("*") if p.is_file()}
                    if source_manifest != copied_manifest: raise ValueError("legacy source changed during import; retry from a stable copy")
                    (migration / "receipt.json").write_text(json.dumps({"contract": "TaskPlanImport/v1", "source": str(legacy), "recipe_sha256": hashlib.sha256(recipe_path.read_bytes()).hexdigest(), "review_required": True, "source_files": source_manifest, "original_ids_preserved": True}, indent=2) + "\n")
                except BaseException:
                    shutil.rmtree(folder)
                    raise
        elif args.action == "impact":
            prior = load_json(Path(args.against)); current = load_json(folder / "bundle.json")
            from decompose.auth import verify
            if prior.get("contract") not in {"TaskPlanBundle/v1", "TaskPlanSnapshot/v1"} or not verify(root, prior):
                raise ValueError("impact comparison requires an authenticated prior bundle or snapshot")
            sys.path.insert(0, str(ROOT / "src/security")); from provenance import verify_bundle
            verify_bundle(root, folder / "task-plan.json")
            old = prior.get("units", {}); new = current.get("units", {})
            old = {k: v.get("projection_digest") if isinstance(v, dict) else v for k, v in old.items()}
            data = {"contract": "TaskPlanImpact/v1", "changed": sorted(k for k in old.keys() & new.keys() if old[k] != new[k]), "added": sorted(new.keys() - old.keys()), "removed": sorted(old.keys() - new.keys()), "unchanged": sorted(k for k in old.keys() & new.keys() if old[k] == new[k])}
        elif args.action in {"graph", "bundle-check"}:
            sys.path.insert(0, str(ROOT / "src/security"))
            from provenance import verify_bundle
            plan = verify_bundle(root, folder / "task-plan.json")
            from cli.initiative import view
            data = view(root, args.initiative, getattr(args, "view", "tasks"))
        else:
            plan, diagnostics = verify_plan(root)
            state = "reviewed" if plan else "needs_review"
            if plan:
                next_steps = [f"taskspec decompose compile {args.initiative}"]
            else:
                proposed, _ = verify_plan(root, require_review=False)
                if proposed and not (folder / "reviews/delivery-plan-review.json").exists():
                    next_steps = [f"Inspect the proposed topology, then explicitly approve it with: taskspec decompose review {args.initiative} --accept --reviewer <name> --reason <reason>"]
                elif (folder / "intake.md").exists() and not (folder / "delivery-plan.yaml").exists():
                    state = "intent"
                    next_steps = [f"taskspec decompose prepare {args.initiative} --recipe <file>"]
                else:
                    state = "blocked"
                    next_steps = ["Resolve the reported integrity or source issue before continuing.",
                                  f"For an intentional revision, use: taskspec decompose prepare {args.initiative} --recipe <file> --replace; then review the new snapshot."]
            if (folder / "bundle.json").exists():
                sys.path.insert(0, str(ROOT / "src/security")); from provenance import verify_bundle
                verify_bundle(root, folder / "task-plan.json"); state = "compiled"
            data = {"contract": "TaskInitiativeStatus/v1", "initiative": args.initiative, "state": state, "diagnostics": [d.as_dict() for d in diagnostics], "next": next_steps}
            if state == "compiled":
                from cli.initiative import view
                data = view(root, args.initiative)
        if os.environ.get("TASKSPEC_JSON_MODE") == "1": print(json.dumps(data, indent=2))
        else:
            print(f"DECOMPOSE={str(data.get('state', data.get('token', 'OK'))).upper()} initiative={args.initiative}")
            if args.action == "status":
                for diagnostic in data.get("diagnostics", []):
                    print(f"{diagnostic['code']}: {diagnostic['message']}")
            for step in data.get("next", []): print("NEXT: " + step)
            if args.action in {"graph", "impact"}: print(json.dumps(data, indent=2))
            if args.action == "status" and "tasks" in data:
                print(f"Accepted tasks: {len(data['accepted_tasks'])}/{len(data['tasks'])}; unproven capabilities: {len(data['proof_gaps'])}")
        return 0
    except ImportError as exc:
        print(f"DECOMPOSE=UNAVAILABLE {exc}; run taskspec setup decompose", file=sys.stderr); return 3
    except (OSError, ValueError, KeyError, TypeError) as exc:
        recovery = {
            "init": f"Inspect taskspec decompose status {args.initiative}; use a new identifier for a new intent.",
            "prepare": "Correct the reported recipe or source inputs, then retry prepare; use --replace only for an intentional revision.",
            "review": f"Inspect taskspec decompose status {args.initiative}; prepare the corrected recipe before reviewing it.",
            "compile": f"Inspect taskspec decompose status {args.initiative}; restore reviewed inputs or prepare and review the revision.",
            "import": "Keep the original workspace; supply its original recipe and resolvable evidence, then retry with an unused initiative identifier.",
            "impact": "Use a retained authenticated bundle or snapshot as --against and a valid current compiled bundle.",
        }.get(args.action, "Restore the reported missing or modified input; prepare and review intentional changes before continuing.")
        if os.environ.get("TASKSPEC_JSON_MODE") == "1": print(json.dumps({"contract": "TaskDecompositionResult/v1", "code": "DECOMPOSE_INVALID", "message": str(exc), "initiative": args.initiative, "next": [recovery]}))
        else: print(f"DECOMPOSE=INVALID {exc}\nNEXT: {recovery}", file=sys.stderr)
        return 1
    finally:
        lock.close()


if __name__ == "__main__": raise SystemExit(main())
