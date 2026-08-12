#!/usr/bin/env python3
"""Enforce opt-in Task-Spec v4 acceptance policies against external receipts."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
sys.path.insert(0, str(ROOT / "src" / "evidence"))
from taskspec_data import DataError, frontmatter  # noqa: E402
from receipts import load as load_receipt, validate as validate_receipt  # noqa: E402
sys.path.insert(0, str(ROOT / "src" / "security"))
from identity import verify as verify_identity  # noqa: E402


def _required(policy: Any) -> bool:
    return isinstance(policy, dict) and policy.get("required") is True


def _authorization(fm: dict[str, Any]) -> str:
    return str(fm.get("signed_off_sig") or f"structural:{fm.get('id', 'unknown')}")


def _load(path: str | None, expected: str, errors: list[str]) -> dict[str, Any] | None:
    if not path:
        errors.append(f"required {expected} was not supplied")
        return None
    try:
        receipt = load_receipt(pathlib.Path(path))
    except ValueError as exc:
        errors.append(str(exc))
        return None
    receipt_errors = validate_receipt(receipt)
    if receipt_errors:
        errors.extend(f"{path}: {item}" for item in receipt_errors)
        return None
    if receipt.get("contract") != expected:
        errors.append(f"{path}: expected {expected}, got {receipt.get('contract')!r}")
        return None
    return receipt


def evaluate(
    fm: dict[str, Any], *, holdout: str | None, graded: str | None,
    human: str | None, environment: str | None, identity: str | None,
    identity_public_key: str | None, identity_revocations: str | None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    proof: list[str] = []
    if int(str(fm.get("format_version", 0)).split(".")[0]) < 4:
        return errors, ["format v3 or earlier: policy receipts are not required"]

    policy = fm.get("evaluation_policy")
    if not isinstance(policy, dict):
        return ["format v4 requires evaluation_policy"], proof
    scope = policy.get("acceptance_scope")
    if scope not in {"local", "portable", "human-authorized"}:
        errors.append("evaluation_policy.acceptance_scope must be local, portable, or human-authorized")
    auth = _authorization(fm)
    task_id = fm.get("id")

    holdout_policy = policy.get("holdout")
    if _required(holdout_policy):
        receipt = _load(holdout, "EvaluationReceipt/v1", errors)
        if receipt:
            if receipt.get("task_id") != task_id or receipt.get("check_type") != "holdout":
                errors.append("holdout receipt does not belong to this task/check type")
            if receipt.get("result") != "pass":
                errors.append("holdout receipt is not a pass")
            expected_auth = holdout_policy.get("authorization_ref")
            expected_descriptor = holdout_policy.get("descriptor_digest")
            if expected_auth and receipt.get("authorization_ref") != expected_auth:
                errors.append("holdout receipt authorization_ref does not match policy")
            if expected_descriptor and receipt.get("descriptor_digest") != expected_descriptor:
                errors.append("holdout receipt descriptor_digest does not match policy")
            proof.append(f"holdout:{receipt.get('result')}")

    graded_policy = policy.get("graded")
    if _required(graded_policy):
        receipt = _load(graded, "GradedEvaluationReceipt/v1", errors)
        if receipt:
            if receipt.get("task_id") != task_id or receipt.get("authorization_ref") != auth:
                errors.append("graded receipt does not match task authorization")
            if receipt.get("rubric_digest") != graded_policy.get("rubric_digest"):
                errors.append("graded receipt rubric_digest does not match policy")
            threshold = graded_policy.get("threshold")
            if threshold is not None and receipt.get("threshold") != threshold:
                errors.append("graded receipt threshold does not match policy")
            if receipt.get("result") != "pass":
                errors.append("graded receipt is not a pass")
            proof.append(f"graded:{receipt.get('score')}/{receipt.get('threshold')}")

    human_policy = policy.get("human")
    if _required(human_policy):
        receipt = _load(human, "HumanAcceptanceReceipt/v1", errors)
        if receipt:
            if receipt.get("task_id") != task_id or receipt.get("authorization_ref") != auth:
                errors.append("human receipt does not match task authorization")
            if receipt.get("owner") != human_policy.get("owner"):
                errors.append("human receipt owner does not match policy")
            if receipt.get("decision") != "accept":
                errors.append("human acceptance decision is not accept")
            proof.append(f"human:{receipt.get('accepted_by')}")

    env_policy = fm.get("environment_contract")
    if _required(env_policy):
        receipt = _load(environment, "EnvironmentReceipt/v1", errors)
        if receipt:
            if receipt.get("task_id") != task_id:
                errors.append("environment receipt does not belong to this task")
            if receipt.get("contract_digest") != env_policy.get("digest"):
                errors.append("environment receipt contract_digest does not match policy")
            proof.append(f"environment:{receipt.get('provider')}")

    identity_policy = fm.get("identity_policy")
    if _required(identity_policy):
        receipt = _load(identity, "AuthorizationReceipt/v1", errors)
        if receipt:
            if receipt.get("task_id") != task_id or receipt.get("authorization_ref") != auth:
                errors.append("identity receipt does not match task authorization")
            trusted = identity_policy.get("key_id")
            if trusted and receipt.get("key_id") != trusted:
                errors.append("identity receipt key_id is not trusted by policy")
            if receipt.get("status") != "verified":
                errors.append("identity receipt is not verified")
            if not identity_public_key:
                errors.append("required identity receipt needs --identity-public-key for cryptographic verification")
            else:
                crypto_errors = verify_identity(
                    receipt, pathlib.Path(identity_public_key),
                    pathlib.Path(identity_revocations) if identity_revocations else None,
                )
                errors.extend(f"identity verification: {item}" for item in crypto_errors)
            proof.append(f"identity:{receipt.get('signer')}")
    return errors, proof


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--holdout-receipt")
    parser.add_argument("--graded-receipt")
    parser.add_argument("--human-receipt")
    parser.add_argument("--environment-receipt")
    parser.add_argument("--identity-receipt")
    parser.add_argument("--identity-public-key")
    parser.add_argument("--identity-revocations")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        fm = frontmatter(pathlib.Path(args.spec).read_text(encoding="utf-8"))
        errors, proof = evaluate(
            fm, holdout=args.holdout_receipt, graded=args.graded_receipt,
            human=args.human_receipt, environment=args.environment_receipt,
            identity=args.identity_receipt,
            identity_public_key=args.identity_public_key, identity_revocations=args.identity_revocations,
        )
    except (OSError, DataError, ValueError) as exc:
        errors, proof = [str(exc)], []
    result = {"contract": "AcceptancePolicyResult/v1", "ok": not errors, "proof": proof, "errors": errors}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif errors:
        for error in errors:
            print(f"BLOCK — {error}")
    else:
        print("PASS — acceptance evidence policy satisfied" + (f" ({', '.join(proof)})" if proof else ""))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
