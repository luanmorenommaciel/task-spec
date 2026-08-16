#!/usr/bin/env python3
"""Create and validate Task-Spec 3.7 evidence receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
sys.path.insert(0, str(ROOT / "src" / "security"))
from taskspec_data import DataError, canonical_digest, frontmatter, sensitive_key_paths, sha256_file  # noqa: E402
from evaluator_trust import sign as sign_receipt  # noqa: E402


REQUIRED: dict[str, tuple[str, ...]] = {
    "EvaluationReceipt/v1": ("task_id", "check_type", "authorization_ref", "evaluator", "evaluated_at", "result", "evidence"),
    "EnvironmentReceipt/v1": ("task_id", "contract_digest", "provider", "environment_digest", "enforced", "observed_at"),
    "EngineRunReceipt/v1": (
        "run_id", "task_id", "task_digest", "handoff_digest", "source_commit", "provider", "model_id",
        "adapter_version", "engine_version", "environment_digest", "started_at", "finished_at", "attempts",
        "terminal_outcome", "acceptance_verdict", "artifacts", "deviations",
    ),
    "HumanAcceptanceReceipt/v1": ("task_id", "authorization_ref", "owner", "accepted_by", "accepted_at", "decision"),
    "GradedEvaluationReceipt/v1": (
        "task_id", "authorization_ref", "evaluator", "rubric_digest", "score", "threshold", "result", "evaluated_at"
    ),
    "AuthorizationReceipt/v1": (
        "task_id", "authorization_ref", "signer", "key_id", "public_key_fingerprint", "payload_digest",
        "algorithm", "signed_at", "signature", "status",
    ),
    "EvaluationReceipt/v2": ("subject", "observed_at", "check_type", "evaluator", "result", "evidence"),
    "EnvironmentReceipt/v2": ("subject", "observed_at", "contract_digest", "provider", "environment_digest", "enforced"),
    "EngineRunReceipt/v2": (
        "subject", "observed_at", "run_id", "handoff_digest", "provider", "model_id", "adapter_version",
        "engine_version", "environment_digest", "started_at", "finished_at", "attempts", "terminal_outcome",
        "acceptance_verdict", "artifacts", "deviations",
    ),
    "HumanAcceptanceReceipt/v2": ("subject", "observed_at", "owner", "accepted_by", "decision"),
    "GradedEvaluationReceipt/v2": ("subject", "observed_at", "evaluator", "rubric_digest", "score", "threshold", "result"),
}

V2_CONTRACTS = {contract for contract in REQUIRED if contract.endswith("/v2")}


def receipt_subject(handoff_path: pathlib.Path) -> tuple[dict[str, str], dict[str, Any]]:
    handoff = load(handoff_path)
    if handoff.get("contract") != "TaskHandoff/v3":
        raise ValueError("v2 receipts require --handoff TaskHandoff/v3")
    try:
        subject = {
            "task_id": str(handoff["task_id"]),
            "task_revision_digest": str(handoff["task_revision_digest"]),
            "authorization_ref": str(handoff["authorization"]["ref"]),
            "attempt_id": str(handoff["attempt"]["id"]),
            "base_commit": str(handoff["source"]["base_commit"]),
        }
    except (KeyError, TypeError) as exc:
        raise ValueError(f"TaskHandoff/v3 is missing receipt subject field: {exc}") from exc
    return subject, handoff


def load(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def validate(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    contract = value.get("contract")
    if contract not in REQUIRED:
        return [f"unsupported contract: {contract!r}"]
    for field in REQUIRED[contract]:
        if field not in value:
            errors.append(f"missing required field: {field}")
    for path in sensitive_key_paths(value):
        errors.append(f"credential-bearing key is forbidden: {path}")
    if str(value.get("authorization_ref", "")).startswith("structural:"):
        errors.append("structural:<task-id> authorization fallback is forbidden in evidence receipts")
    if contract in V2_CONTRACTS:
        subject = value.get("subject")
        required_subject = ("task_id", "task_revision_digest", "authorization_ref", "attempt_id", "base_commit")
        if not isinstance(subject, dict):
            errors.append("v2 receipt subject must be an object")
        else:
            for field in required_subject:
                if not isinstance(subject.get(field), str) or not subject[field]:
                    errors.append(f"v2 receipt subject missing {field}")
            if not str(subject.get("task_revision_digest", "")).startswith("sha256:"):
                errors.append("v2 receipt task_revision_digest must use sha256:<hex>")
            if not str(subject.get("authorization_ref", "")).startswith("hmac-sha256-v3:"):
                errors.append("v2 receipt authorization_ref must be HMAC v3")
        signature = value.get("signature")
        if signature is not None:
            if not isinstance(signature, dict) or signature.get("algorithm") != "Ed25519":
                errors.append("v2 receipt signature must be an Ed25519 signature object")
    if contract in {"EvaluationReceipt/v1", "EvaluationReceipt/v2"}:
        if value.get("check_type") not in {"deterministic", "holdout"}:
            errors.append("EvaluationReceipt check_type must be deterministic or holdout")
        if value.get("result") not in {"pass", "fail", "error"}:
            errors.append("EvaluationReceipt result must be pass, fail, or error")
    elif contract in {"EnvironmentReceipt/v1", "EnvironmentReceipt/v2"} and value.get("enforced") is not True:
        errors.append("EnvironmentReceipt enforced must be true")
    elif contract in {"EngineRunReceipt/v1", "EngineRunReceipt/v2"}:
        if value.get("terminal_outcome") not in {"pass", "fail", "parked", "blocked", "unavailable", "error"}:
            errors.append("EngineRunReceipt terminal_outcome is invalid")
        if value.get("acceptance_verdict") not in {"accepted", "rejected", "not_run"}:
            errors.append("EngineRunReceipt acceptance_verdict is invalid")
        if not isinstance(value.get("attempts"), int) or value.get("attempts", -1) < 0:
            errors.append("EngineRunReceipt attempts must be a non-negative integer")
    elif contract in {"HumanAcceptanceReceipt/v1", "HumanAcceptanceReceipt/v2"} and value.get("decision") not in {"accept", "reject"}:
        errors.append("HumanAcceptanceReceipt decision must be accept or reject")
    elif contract in {"GradedEvaluationReceipt/v1", "GradedEvaluationReceipt/v2"}:
        score, threshold = value.get("score"), value.get("threshold")
        if not isinstance(score, (int, float)) or not 0 <= score <= 1:
            errors.append("graded score must be between 0 and 1")
        if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
            errors.append("graded threshold must be between 0 and 1")
        if value.get("result") not in {"pass", "fail"}:
            errors.append("graded result must be pass or fail")
        elif isinstance(score, (int, float)) and isinstance(threshold, (int, float)):
            expected = "pass" if score >= threshold else "fail"
            if value.get("result") != expected:
                errors.append("graded result disagrees with score and threshold")
    elif contract == "AuthorizationReceipt/v1":
        if value.get("algorithm") != "Ed25519":
            errors.append("AuthorizationReceipt algorithm must be Ed25519")
        if value.get("status") != "verified":
            errors.append("AuthorizationReceipt status must be verified")
    return errors


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate_cmd = sub.add_parser("validate")
    validate_cmd.add_argument("files", nargs="+")

    sign_cmd = sub.add_parser("sign")
    sign_cmd.add_argument("receipt")
    sign_cmd.add_argument("--private-key", required=True)
    sign_cmd.add_argument("--public-key", required=True)
    sign_cmd.add_argument("--out", required=True)

    engine = sub.add_parser("engine")
    engine.add_argument("--spec", required=True)
    engine.add_argument("--handoff", required=True)
    engine.add_argument("--run-id", required=True)
    engine.add_argument("--provider", required=True)
    engine.add_argument("--model", required=True)
    engine.add_argument("--adapter-version", required=True)
    engine.add_argument("--source-commit", required=True)
    engine.add_argument("--environment-digest", default="unreported")
    engine.add_argument("--started-at", required=True)
    engine.add_argument("--finished-at", default=None)
    engine.add_argument("--attempts", type=int, default=1)
    engine.add_argument("--outcome", required=True, choices=["pass", "fail", "parked", "blocked", "unavailable", "error"])
    engine.add_argument("--acceptance", default="not_run", choices=["accepted", "rejected", "not_run"])
    engine.add_argument("--artifact", action="append", default=[])
    engine.add_argument("--deviation", action="append", default=[])
    engine.add_argument("--out", required=True)
    engine.add_argument("--legacy-v1", action="store_true")

    env = sub.add_parser("environment")
    env.add_argument("--task-id", required=True)
    env.add_argument("--contract", required=True)
    env.add_argument("--provider", required=True)
    env_digest = env.add_mutually_exclusive_group(required=True)
    env_digest.add_argument("--environment-digest")
    env_digest.add_argument("--attestation")
    env.add_argument("--out", required=True)
    env.add_argument("--handoff")
    env.add_argument("--legacy-v1", action="store_true")

    evaluation = sub.add_parser("evaluation")
    evaluation.add_argument("--handoff", required=True)
    evaluation.add_argument("--check-type", choices=["deterministic", "holdout"], required=True)
    evaluation.add_argument("--evaluator", required=True)
    evaluation.add_argument("--result", choices=["pass", "fail", "error"], required=True)
    evaluation.add_argument("--descriptor-digest")
    evaluation.add_argument("--evidence", action="append", default=[])
    evaluation.add_argument("--out", required=True)

    graded = sub.add_parser("graded")
    graded.add_argument("--task-id", required=True)
    graded.add_argument("--authorization-ref", required=True)
    graded.add_argument("--evaluator", required=True)
    graded.add_argument("--rubric-digest", required=True)
    graded.add_argument("--score", type=float, required=True)
    graded.add_argument("--threshold", type=float, required=True)
    graded.add_argument("--out", required=True)
    graded.add_argument("--handoff")
    graded.add_argument("--legacy-v1", action="store_true")

    human = sub.add_parser("human")
    human.add_argument("--task-id", required=True)
    human.add_argument("--authorization-ref", required=True)
    human.add_argument("--owner", required=True)
    human.add_argument("--accepted-by", required=True)
    human.add_argument("--decision", choices=["accept", "reject"], required=True)
    human.add_argument("--out", required=True)
    human.add_argument("--handoff")
    human.add_argument("--legacy-v1", action="store_true")

    args = parser.parse_args()
    try:
        if args.command == "validate":
            failures = 0
            for raw in args.files:
                path = pathlib.Path(raw)
                value = load(path)
                errors = validate(value)
                if errors:
                    failures += 1
                    print(f"INVALID {path}: {'; '.join(errors)}", file=sys.stderr)
                else:
                    print(f"VALID {path}: {value['contract']}")
            return 1 if failures else 0
        if args.command == "sign":
            source = load(pathlib.Path(args.receipt))
            if source.get("contract") not in V2_CONTRACTS:
                raise ValueError("only v2 evidence receipts can be signed")
            value = sign_receipt(source, pathlib.Path(args.private_key), pathlib.Path(args.public_key))
            errors = validate(value)
            if errors:
                raise ValueError("; ".join(errors))
            out = pathlib.Path(args.out); write(out, value)
            print(f"RECEIPT=SIGNED contract={value['contract']} key_id={value['signature']['key_id']} path={out}")
            return 0
        if args.command == "environment":
            contract = load(pathlib.Path(args.contract))
            if contract.get("contract") != "EnvironmentContract/v1":
                raise ValueError("--contract must be EnvironmentContract/v1")
            credential_paths = sensitive_key_paths(contract)
            if credential_paths:
                raise ValueError(f"environment contract contains credential-bearing keys: {credential_paths}")
            environment_digest = args.environment_digest
            if args.attestation:
                attestation_path = pathlib.Path(args.attestation)
                attestation = load(attestation_path)
                if attestation.get("contract") != "EnvironmentAttestation/v1":
                    raise ValueError("--attestation must be EnvironmentAttestation/v1")
                if attestation.get("result") != "pass" or attestation.get("verified") is not True:
                    raise ValueError("--attestation must report a verified pass")
                environment_digest = "sha256:" + hashlib.sha256(attestation_path.read_bytes()).hexdigest()
            assert environment_digest is not None
            if args.legacy_v1:
                value = {"contract": "EnvironmentReceipt/v1", "task_id": args.task_id, "contract_digest": f"sha256:{canonical_digest(contract)}", "provider": args.provider, "environment_digest": environment_digest, "enforced": True, "observed_at": now()}
            else:
                if not args.handoff: raise ValueError("environment v2 requires --handoff (or pass --legacy-v1)")
                subject, _ = receipt_subject(pathlib.Path(args.handoff))
                if args.task_id != subject["task_id"]: raise ValueError("--task-id does not match handoff")
                value = {"contract": "EnvironmentReceipt/v2", "subject": subject, "observed_at": now(), "contract_digest": f"sha256:{canonical_digest(contract)}", "provider": args.provider, "environment_digest": environment_digest, "enforced": True}
        elif args.command == "evaluation":
            subject, _ = receipt_subject(pathlib.Path(args.handoff))
            value = {"contract": "EvaluationReceipt/v2", "subject": subject, "observed_at": now(), "check_type": args.check_type, "evaluator": args.evaluator, "result": args.result, "evidence": args.evidence}
            if args.descriptor_digest: value["descriptor_digest"] = args.descriptor_digest
        elif args.command == "graded":
            if args.legacy_v1:
                value = {"contract": "GradedEvaluationReceipt/v1", "task_id": args.task_id, "authorization_ref": args.authorization_ref, "evaluator": args.evaluator, "rubric_digest": args.rubric_digest, "score": args.score, "threshold": args.threshold, "result": "pass" if args.score >= args.threshold else "fail", "evaluated_at": now()}
            else:
                if not args.handoff: raise ValueError("graded v2 requires --handoff (or pass --legacy-v1)")
                subject, _ = receipt_subject(pathlib.Path(args.handoff))
                if args.task_id != subject["task_id"] or args.authorization_ref != subject["authorization_ref"]: raise ValueError("graded arguments do not match handoff subject")
                value = {"contract": "GradedEvaluationReceipt/v2", "subject": subject, "observed_at": now(), "evaluator": args.evaluator, "rubric_digest": args.rubric_digest, "score": args.score, "threshold": args.threshold, "result": "pass" if args.score >= args.threshold else "fail"}
        elif args.command == "human":
            if args.legacy_v1:
                value = {"contract": "HumanAcceptanceReceipt/v1", "task_id": args.task_id, "authorization_ref": args.authorization_ref, "owner": args.owner, "accepted_by": args.accepted_by, "accepted_at": now(), "decision": args.decision}
            else:
                if not args.handoff: raise ValueError("human v2 requires --handoff (or pass --legacy-v1)")
                subject, _ = receipt_subject(pathlib.Path(args.handoff))
                if args.task_id != subject["task_id"] or args.authorization_ref != subject["authorization_ref"]: raise ValueError("human arguments do not match handoff subject")
                value = {"contract": "HumanAcceptanceReceipt/v2", "subject": subject, "observed_at": now(), "owner": args.owner, "accepted_by": args.accepted_by, "decision": args.decision}
        else:
            spec = pathlib.Path(args.spec)
            handoff = pathlib.Path(args.handoff)
            try:
                fm = frontmatter(spec.read_text(encoding="utf-8"))
            except (OSError, DataError) as exc:
                raise ValueError(str(exc)) from exc
            subject = None
            if not args.legacy_v1:
                subject, _ = receipt_subject(handoff)
                if str(fm.get("id")) != subject["task_id"]:
                    raise ValueError("spec task id does not match handoff subject")
            value = {
                "contract": "EngineRunReceipt/v1" if args.legacy_v1 else "EngineRunReceipt/v2",
                "run_id": args.run_id,
                "handoff_digest": sha256_file(handoff),
                "provider": args.provider,
                "model_id": args.model,
                "adapter_version": args.adapter_version,
                "engine_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
                "environment_digest": args.environment_digest,
                "started_at": args.started_at,
                "finished_at": args.finished_at or now(),
                "attempts": args.attempts,
                "terminal_outcome": args.outcome,
                "acceptance_verdict": args.acceptance,
                "artifacts": args.artifact,
                "deviations": args.deviation,
            }
            if args.legacy_v1:
                value.update({"task_id": fm.get("id"), "task_digest": sha256_file(spec), "source_commit": args.source_commit})
            else:
                assert subject is not None
                if args.source_commit != subject["base_commit"]: raise ValueError("--source-commit does not match handoff base_commit")
                value.update({"subject": subject, "observed_at": now()})
        errors = validate(value)
        if errors:
            raise ValueError("; ".join(errors))
        out = pathlib.Path(args.out)
        write(out, value)
        print(f"RECEIPT=WRITTEN contract={value['contract']} path={out}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"RECEIPT=INVALID error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
