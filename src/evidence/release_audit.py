#!/usr/bin/env python3
"""Generate and verify an evidence-derived Task-Spec release scorecard."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import tempfile
from typing import Any, Dict, List, Tuple


PASS = "pass"
SCORE_STATES = {"pass", "fail", "pending", "not_run", "unavailable"}
RELEASE_STATES = SCORE_STATES | {"blocked"}
EVIDENCE_CLASSES = {
    "local",
    "hosted",
    "published",
    "external_engine",
    "external_enforcement",
    "protocol",
    "provenance",
}


class AuditError(Exception):
    """A release artifact violates the score contract."""


def load_json(path: pathlib.Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AuditError("cannot read JSON {}: {}".format(path, exc))
    if not isinstance(value, dict):
        raise AuditError("{} must contain a JSON object".format(path))
    return value


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def digest_file(path: pathlib.Path) -> str:
    try:
        return digest_bytes(path.read_bytes())
    except OSError as exc:
        raise AuditError("cannot digest {}: {}".format(path, exc))


def atomic_json(path: pathlib.Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".{}.".format(path.name), dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def relative_artifact(root: pathlib.Path, raw: str) -> pathlib.Path:
    candidate = pathlib.PurePosixPath(raw)
    if not raw or candidate.is_absolute() or ".." in candidate.parts or ".git" in candidate.parts:
        raise AuditError("unsafe evidence path: {}".format(raw))
    root_real = root.resolve()
    path = (root / pathlib.Path(*candidate.parts)).resolve(strict=True)
    try:
        path.relative_to(root_real)
    except ValueError:
        raise AuditError("evidence path escapes root: {}".format(raw))
    if not path.is_file():
        raise AuditError("evidence path is not a file: {}".format(raw))
    return path


def validate_rubric(rubric: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    if rubric.get("contract") != "QualityRubric/v1" or rubric.get("version") != 1:
        raise AuditError("unsupported quality rubric contract")
    dimensions = rubric.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        raise AuditError("rubric dimensions must be a non-empty list")
    dimension_ids = set()
    criterion_ids = set()
    criteria_by_id: Dict[str, Dict[str, Any]] = {}
    computed_max = 0
    for dimension in dimensions:
        dimension_id = dimension.get("id")
        if not isinstance(dimension_id, str) or dimension_id in dimension_ids:
            raise AuditError("duplicate or invalid dimension id: {}".format(dimension_id))
        dimension_ids.add(dimension_id)
        criteria = dimension.get("criteria")
        if not isinstance(criteria, list) or not criteria:
            raise AuditError("dimension {} has no criteria".format(dimension_id))
        dimension_sum = 0
        for criterion in criteria:
            criterion_id = criterion.get("id")
            if not isinstance(criterion_id, str) or criterion_id in criterion_ids:
                raise AuditError("duplicate or invalid criterion id: {}".format(criterion_id))
            criterion_ids.add(criterion_id)
            points = criterion.get("points")
            if not isinstance(points, int) or isinstance(points, bool) or points < 1:
                raise AuditError("criterion {} has invalid points".format(criterion_id))
            classes = criterion.get("evidence_classes")
            if not isinstance(classes, list) or not classes or any(item not in EVIDENCE_CLASSES for item in classes):
                raise AuditError("criterion {} has invalid evidence classes".format(criterion_id))
            falsifiers = criterion.get("falsifiers")
            if not isinstance(falsifiers, list) or not falsifiers or not all(isinstance(item, str) and item for item in falsifiers):
                raise AuditError("criterion {} has no falsifier".format(criterion_id))
            if not isinstance(criterion.get("blocking"), bool):
                raise AuditError("criterion {} must declare blocking".format(criterion_id))
            dimension_sum += points
            criteria_by_id[criterion_id] = criterion
        if dimension_sum != dimension.get("max_points"):
            raise AuditError(
                "dimension {} declares {} points but criteria sum to {}".format(
                    dimension_id, dimension.get("max_points"), dimension_sum
                )
            )
        computed_max += dimension_sum
    if computed_max != rubric.get("max_score"):
        raise AuditError("rubric max_score does not equal its criteria")
    target = rubric.get("target_score")
    if not isinstance(target, int) or isinstance(target, bool) or target < 1 or target > computed_max:
        raise AuditError("rubric target_score is invalid")
    return dimensions, criteria_by_id


def release_gate(evidence: Dict[str, Any], criterion_id: str) -> Dict[str, Any]:
    gates = evidence.get("gates")
    if not isinstance(gates, dict):
        raise AuditError("release evidence gates must be an object")
    gate = gates.get(criterion_id)
    if gate is None:
        return {"state": "not_run", "evidence": None, "reason": "No retained gate evidence."}
    if not isinstance(gate, dict) or gate.get("state") not in RELEASE_STATES:
        raise AuditError("gate {} has an invalid state".format(criterion_id))
    return gate


def evaluate_criterion(
    root: pathlib.Path, criterion: Dict[str, Any], gate: Dict[str, Any]
) -> Tuple[Dict[str, Any], bool]:
    criterion_id = criterion["id"]
    declared_state = gate["state"]
    state = "fail" if declared_state == "blocked" else declared_state
    evidence_rows: List[Dict[str, Any]] = []
    reason = gate.get("reason") or "Gate state is {}.".format(declared_state)
    artifact = gate.get("evidence")
    artifact_valid = False
    if artifact is not None:
        if not isinstance(artifact, dict) or set(artifact) != {"path", "digest"}:
            raise AuditError("gate {} has an invalid artifact reference".format(criterion_id))
        raw_path = artifact.get("path")
        expected_digest = artifact.get("digest")
        if not isinstance(raw_path, str) or not isinstance(expected_digest, str):
            raise AuditError("gate {} artifact fields must be strings".format(criterion_id))
        try:
            path = relative_artifact(root, raw_path)
            observed_digest = digest_file(path)
            artifact_valid = observed_digest == expected_digest
            if not artifact_valid:
                state = "fail"
                reason = "Evidence digest mismatch for {}.".format(raw_path)
        except AuditError as exc:
            state = "fail"
            reason = str(exc)
        evidence_rows.append(
            {
                "path": raw_path,
                "digest": expected_digest,
                "class": criterion["evidence_classes"][0],
                "state": state if state in SCORE_STATES else "fail",
            }
        )
    elif declared_state == PASS:
        state = "fail"
        reason = "Pass denied: no retained evidence artifact."
    awarded = criterion["points"] if state == PASS and artifact_valid else 0
    if state not in SCORE_STATES:
        state = "fail"
    result = {
        "id": criterion_id,
        "points": criterion["points"],
        "awarded": awarded,
        "state": state,
        "evidence": evidence_rows,
        "reason": reason,
    }
    blocking_ok = not criterion["blocking"] or (state == PASS and awarded == criterion["points"])
    return result, blocking_ok


def generate_scorecard(
    root: pathlib.Path, rubric_path: pathlib.Path, evidence_path: pathlib.Path
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    rubric = load_json(rubric_path)
    evidence = load_json(evidence_path)
    dimensions, _criteria_by_id = validate_rubric(rubric)
    if evidence.get("contract") != "TaskSpecReleaseEvidence/v2":
        raise AuditError("release evidence must use TaskSpecReleaseEvidence/v2")
    if not isinstance(evidence.get("generated_at"), str):
        raise AuditError("release evidence must declare generated_at")
    score_dimensions = []
    total_awarded = 0
    all_blocking = True
    for dimension in dimensions:
        criterion_results = []
        awarded_points = 0
        for criterion in dimension["criteria"]:
            result, blocking_ok = evaluate_criterion(root, criterion, release_gate(evidence, criterion["id"]))
            criterion_results.append(result)
            awarded_points += result["awarded"]
            all_blocking = all_blocking and blocking_ok
        total_awarded += awarded_points
        score_dimensions.append(
            {
                "id": dimension["id"],
                "awarded_points": awarded_points,
                "max_points": dimension["max_points"],
                "criteria": criterion_results,
            }
        )
    target = rubric["target_score"]
    scorecard = {
        "contract": "TaskSpecQualityScorecard/v1",
        "release_version": evidence.get("version"),
        "rubric_digest": digest_file(rubric_path),
        "generated_at": evidence["generated_at"],
        "dimensions": score_dimensions,
        "total": {
            "awarded": total_awarded,
            "maximum": rubric["max_score"],
            "target": target,
            "passed": total_awarded >= target and all_blocking,
        },
    }
    return scorecard, evidence


def scorecard_bytes(scorecard: Dict[str, Any]) -> bytes:
    return (json.dumps(scorecard, indent=2, sort_keys=False) + "\n").encode("utf-8")


def write_scorecard(
    scorecard_path: pathlib.Path,
    scorecard: Dict[str, Any],
    evidence_path: pathlib.Path,
    evidence: Dict[str, Any],
    update_evidence: bool,
) -> None:
    atomic_json(scorecard_path, scorecard)
    if update_evidence:
        root = evidence_path.parent.parent.resolve()
        try:
            relative = scorecard_path.resolve().relative_to(root).as_posix()
        except ValueError:
            raise AuditError("scorecard must be inside the release evidence root")
        evidence["quality_scorecard"] = {"path": relative, "digest": digest_file(scorecard_path)}
        atomic_json(evidence_path, evidence)


def compare_scorecard(
    root: pathlib.Path,
    scorecard_path: pathlib.Path,
    expected: Dict[str, Any],
    evidence: Dict[str, Any],
) -> List[str]:
    failures = []
    try:
        actual = load_json(scorecard_path)
    except AuditError as exc:
        return [str(exc)]
    if actual != expected:
        failures.append("stored scorecard does not match the derived score")
    pointer = evidence.get("quality_scorecard")
    if not isinstance(pointer, dict):
        failures.append("release evidence has no scorecard pointer")
    else:
        try:
            pointer_path = relative_artifact(root, pointer.get("path", ""))
            if pointer_path != scorecard_path.resolve():
                failures.append("release evidence points to a different scorecard")
            elif digest_file(pointer_path) != pointer.get("digest"):
                failures.append("release evidence scorecard digest is stale")
        except AuditError as exc:
            failures.append(str(exc))
    return failures


def criterion_state(scorecard: Dict[str, Any], criterion_id: str) -> str:
    for dimension in scorecard["dimensions"]:
        for criterion in dimension["criteria"]:
            if criterion["id"] == criterion_id:
                return criterion["state"]
    return "not_run"


def audit_tokens(scorecard: Dict[str, Any], failures: List[str]) -> Tuple[List[str], bool]:
    protocol_ready = all(criterion_state(scorecard, item) == PASS for item in ("a2a_official", "mcp_official"))
    engine_ready = criterion_state(scorecard, "real_engine_matrix") == PASS
    sandbox_ready = criterion_state(scorecard, "signed_sandbox") == PASS
    release_ready = scorecard["total"]["passed"] and not failures
    tokens = [
        "PROTOCOLS={}".format("READY" if protocol_ready else "BLOCKED"),
        "ENGINE_MATRIX={}".format("READY" if engine_ready else "BLOCKED"),
        "SANDBOX_ATTESTATION={}".format("VERIFIED" if sandbox_ready else "BLOCKED"),
        "QUALITY_SCORE={}".format(scorecard["total"]["awarded"]),
        "RELEASE_AUDIT={}".format("READY" if release_ready else "BLOCKED"),
    ]
    return tokens, release_ready


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("command", choices=("generate", "check", "audit"))
    result.add_argument("--root", default=None)
    result.add_argument("--rubric", default="release/quality-rubric.json")
    result.add_argument("--evidence", default="release/evidence.json")
    result.add_argument("--scorecard", default="release/3.8.1/scorecard.json")
    result.add_argument("--update-evidence", action="store_true")
    result.add_argument("--json", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    default_root = pathlib.Path(__file__).resolve().parents[2]
    root = pathlib.Path(args.root).resolve() if args.root else default_root
    rubric_path = (root / args.rubric).resolve()
    evidence_path = (root / args.evidence).resolve()
    scorecard_path = (root / args.scorecard).resolve()
    try:
        scorecard, evidence = generate_scorecard(root, rubric_path, evidence_path)
        if args.command == "generate":
            write_scorecard(scorecard_path, scorecard, evidence_path, evidence, args.update_evidence)
            if args.json:
                print(json.dumps(scorecard, sort_keys=True))
            else:
                print("QUALITY_SCORE={} SCORECARD={}".format(scorecard["total"]["awarded"], scorecard_path))
            return 0
        failures = compare_scorecard(root, scorecard_path, scorecard, evidence)
        if args.command == "check":
            if failures:
                for failure in failures:
                    print("RELEASE_AUDIT_ERROR={}".format(failure))
                return 1
            if args.json:
                print(json.dumps(scorecard, sort_keys=True))
            else:
                print("QUALITY_SCORE={} SCORECARD=VALID".format(scorecard["total"]["awarded"]))
            return 0
        tokens, ready = audit_tokens(scorecard, failures)
        if args.json:
            print(json.dumps({"scorecard": scorecard, "failures": failures, "tokens": tokens, "ready": ready}, sort_keys=True))
        else:
            for failure in failures:
                print("RELEASE_AUDIT_ERROR={}".format(failure))
            for token in tokens:
                print(token)
        return 0 if ready else 1
    except AuditError as exc:
        if args.json:
            print(json.dumps({"error": str(exc), "ready": False}, sort_keys=True))
        else:
            print("RELEASE_AUDIT_ERROR={}".format(exc))
            print("RELEASE_AUDIT=BLOCKED")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
