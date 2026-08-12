#!/usr/bin/env python3
"""Create and validate Task-Spec 3.7 evidence receipts."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
from taskspec_data import DataError, canonical_digest, frontmatter, sensitive_key_paths, sha256_file  # noqa: E402


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
}


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
    if contract == "EvaluationReceipt/v1":
        if value.get("check_type") not in {"deterministic", "holdout"}:
            errors.append("EvaluationReceipt check_type must be deterministic or holdout")
        if value.get("result") not in {"pass", "fail", "error"}:
            errors.append("EvaluationReceipt result must be pass, fail, or error")
    elif contract == "EnvironmentReceipt/v1" and value.get("enforced") is not True:
        errors.append("EnvironmentReceipt enforced must be true")
    elif contract == "EngineRunReceipt/v1":
        if value.get("terminal_outcome") not in {"pass", "fail", "parked", "blocked", "unavailable", "error"}:
            errors.append("EngineRunReceipt terminal_outcome is invalid")
        if value.get("acceptance_verdict") not in {"accepted", "rejected", "not_run"}:
            errors.append("EngineRunReceipt acceptance_verdict is invalid")
        if not isinstance(value.get("attempts"), int) or value.get("attempts", -1) < 0:
            errors.append("EngineRunReceipt attempts must be a non-negative integer")
    elif contract == "HumanAcceptanceReceipt/v1" and value.get("decision") not in {"accept", "reject"}:
        errors.append("HumanAcceptanceReceipt decision must be accept or reject")
    elif contract == "GradedEvaluationReceipt/v1":
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

    env = sub.add_parser("environment")
    env.add_argument("--task-id", required=True)
    env.add_argument("--contract", required=True)
    env.add_argument("--provider", required=True)
    env.add_argument("--environment-digest", required=True)
    env.add_argument("--out", required=True)

    graded = sub.add_parser("graded")
    graded.add_argument("--task-id", required=True)
    graded.add_argument("--authorization-ref", required=True)
    graded.add_argument("--evaluator", required=True)
    graded.add_argument("--rubric-digest", required=True)
    graded.add_argument("--score", type=float, required=True)
    graded.add_argument("--threshold", type=float, required=True)
    graded.add_argument("--out", required=True)

    human = sub.add_parser("human")
    human.add_argument("--task-id", required=True)
    human.add_argument("--authorization-ref", required=True)
    human.add_argument("--owner", required=True)
    human.add_argument("--accepted-by", required=True)
    human.add_argument("--decision", choices=["accept", "reject"], required=True)
    human.add_argument("--out", required=True)

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
        if args.command == "environment":
            contract = load(pathlib.Path(args.contract))
            if contract.get("contract") != "EnvironmentContract/v1":
                raise ValueError("--contract must be EnvironmentContract/v1")
            credential_paths = sensitive_key_paths(contract)
            if credential_paths:
                raise ValueError(f"environment contract contains credential-bearing keys: {credential_paths}")
            value = {
                "contract": "EnvironmentReceipt/v1",
                "task_id": args.task_id,
                "contract_digest": f"sha256:{canonical_digest(contract)}",
                "provider": args.provider,
                "environment_digest": args.environment_digest,
                "enforced": True,
                "observed_at": now(),
            }
        elif args.command == "graded":
            value = {
                "contract": "GradedEvaluationReceipt/v1", "task_id": args.task_id,
                "authorization_ref": args.authorization_ref, "evaluator": args.evaluator,
                "rubric_digest": args.rubric_digest, "score": args.score, "threshold": args.threshold,
                "result": "pass" if args.score >= args.threshold else "fail", "evaluated_at": now(),
            }
        elif args.command == "human":
            value = {
                "contract": "HumanAcceptanceReceipt/v1", "task_id": args.task_id,
                "authorization_ref": args.authorization_ref, "owner": args.owner,
                "accepted_by": args.accepted_by, "accepted_at": now(), "decision": args.decision,
            }
        else:
            spec = pathlib.Path(args.spec)
            handoff = pathlib.Path(args.handoff)
            try:
                fm = frontmatter(spec.read_text(encoding="utf-8"))
            except (OSError, DataError) as exc:
                raise ValueError(str(exc)) from exc
            value = {
                "contract": "EngineRunReceipt/v1",
                "run_id": args.run_id,
                "task_id": fm.get("id"),
                "task_digest": sha256_file(spec),
                "handoff_digest": sha256_file(handoff),
                "source_commit": args.source_commit,
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
