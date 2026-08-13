#!/usr/bin/env python3
"""Enforce sealed format-v4 evidence policy against attempt-bound receipts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
sys.path.insert(0, str(ROOT / "src" / "evidence"))
sys.path.insert(0, str(ROOT / "src" / "security"))
from taskspec_data import DataError, frontmatter  # noqa: E402
from receipts import V2_CONTRACTS, load as load_receipt, validate as validate_receipt  # noqa: E402
from evaluator_trust import verify as verify_evaluator  # noqa: E402
from identity import verify as verify_identity  # noqa: E402


def _required(policy: Any) -> bool:
    return isinstance(policy, dict) and policy.get("required") is True


def _parse_time(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("timestamp is missing")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def _observed_at(receipt: dict[str, Any]) -> Any:
    return receipt.get("observed_at") or receipt.get("evaluated_at") or receipt.get("accepted_at")


def _load(
    path: str | None, expected_v2: str, expected_v1: str, errors: list[str]
) -> tuple[dict[str, Any] | None, bool]:
    if not path:
        errors.append(f"required {expected_v2} was not supplied")
        return None, False
    try:
        receipt = load_receipt(pathlib.Path(path))
    except ValueError as exc:
        errors.append(str(exc))
        return None, False
    receipt_errors = validate_receipt(receipt)
    if receipt_errors:
        errors.extend(f"{path}: {item}" for item in receipt_errors)
        return None, False
    contract = receipt.get("contract")
    if contract not in {expected_v2, expected_v1}:
        errors.append(f"{path}: expected {expected_v2} or compatibility {expected_v1}, got {contract!r}")
        return None, False
    return receipt, contract == expected_v2


def _subject(handoff: dict[str, Any]) -> dict[str, str]:
    try:
        return {
            "task_id": str(handoff["task_id"]),
            "task_revision_digest": str(handoff["task_revision_digest"]),
            "authorization_ref": str(handoff["authorization"]["ref"]),
            "attempt_id": str(handoff["attempt"]["id"]),
            "base_commit": str(handoff["source"]["base_commit"]),
        }
    except (KeyError, TypeError) as exc:
        raise ValueError(f"TaskHandoff/v3 is missing receipt subject field: {exc}") from exc


def _check_receipt_binding(
    receipt: dict[str, Any], *, expected_subject: dict[str, str], earliest: datetime,
    tier2_reasons: list[str], errors: list[str], max_age_sec: Any,
) -> None:
    if receipt.get("contract") not in V2_CONTRACTS:
        tier2_reasons.append(f"{receipt.get('contract')}:LEGACY_RECEIPT")
        if receipt.get("task_id") != expected_subject["task_id"]:
            errors.append(f"{receipt.get('contract')}: legacy receipt task_id does not match task")
        if str(receipt.get("authorization_ref", "")).startswith("structural:"):
            errors.append(f"{receipt.get('contract')}: structural authorization fallback is forbidden for required evidence")
    elif receipt.get("subject") != expected_subject:
        errors.append(f"{receipt.get('contract')}: receipt subject does not match task revision, authorization, attempt, and base commit")
    try:
        observed = _parse_time(_observed_at(receipt))
    except (TypeError, ValueError) as exc:
        errors.append(f"{receipt.get('contract')}: invalid observed_at: {exc}")
        return
    if observed < earliest:
        errors.append(f"{receipt.get('contract')}: receipt predates authorization or handoff")
    if max_age_sec is not None:
        if not isinstance(max_age_sec, int) or max_age_sec < 1:
            errors.append("evaluation_policy.max_age_sec must be a positive integer")
        elif (datetime.now(timezone.utc) - observed).total_seconds() > max_age_sec:
            errors.append(f"{receipt.get('contract')}: receipt exceeds max_age_sec")


def _check_external_signature(
    receipt: dict[str, Any], *, trust_registry: str | None, errors: list[str]
) -> None:
    if not trust_registry:
        errors.append(f"{receipt.get('contract')}: portable evidence requires --trust-registry")
        return
    errors.extend(
        f"{receipt.get('contract')}: evaluator signature: {item}"
        for item in verify_evaluator(receipt, pathlib.Path(trust_registry))
    )


def evaluate(
    fm: dict[str, Any], *, handoff: dict[str, Any] | None, holdout: str | None,
    graded: str | None, human: str | None, environment: str | None,
    identity: str | None, identity_public_key: str | None,
    identity_revocations: str | None, trust_registry: str | None,
) -> dict[str, Any]:
    errors: list[str] = []
    proof: list[str] = []
    tier2_reasons: list[str] = []
    if int(str(fm.get("format_version", 0)).split(".")[0]) < 4:
        return {
            "contract": "AcceptancePolicyResult/v1", "ok": True, "tier": 1,
            "proof": ["format v3 or earlier: v4 policy receipts are not required"],
            "tier2_reasons": [], "errors": [], "failure_codes": [],
        }

    policy = fm.get("evaluation_policy")
    if not isinstance(policy, dict):
        errors.append("format v4 requires evaluation_policy")
        policy = {}
    scope = policy.get("acceptance_scope")
    if scope not in {"local", "portable", "human-authorized"}:
        errors.append("evaluation_policy.acceptance_scope must be local, portable, or human-authorized")

    if not handoff or handoff.get("contract") != "TaskHandoff/v3":
        errors.append("format v4 acceptance requires TaskHandoff/v3")
        expected_subject = None
        earliest = datetime.min.replace(tzinfo=timezone.utc)
    else:
        try:
            expected_subject = _subject(handoff)
            earliest = max(
                _parse_time(fm.get("signed_off_at")),
                _parse_time(handoff.get("attempt", {}).get("issued_at")),
            )
        except (TypeError, ValueError) as exc:
            errors.append(str(exc))
            expected_subject = None
            earliest = datetime.min.replace(tzinfo=timezone.utc)

    max_age = policy.get("max_age_sec")

    def evidence(
        path: str | None, expected_v2: str, expected_v1: str,
        policy_part: dict[str, Any], label: str,
    ) -> dict[str, Any] | None:
        receipt, is_v2 = _load(path, expected_v2, expected_v1, errors)
        if not receipt:
            return None
        if expected_subject is not None:
            _check_receipt_binding(
                receipt, expected_subject=expected_subject, earliest=earliest,
                tier2_reasons=tier2_reasons, errors=errors,
                max_age_sec=policy_part.get("max_age_sec", max_age),
            )
        if is_v2 and scope in {"portable", "human-authorized"}:
            _check_external_signature(receipt, trust_registry=trust_registry, errors=errors)
        proof.append(f"{label}:{receipt.get('contract')}")
        if not is_v2 and label != "holdout" and receipt.get("authorization_ref") not in {None, expected_subject and expected_subject["authorization_ref"]}:
            errors.append(f"{receipt.get('contract')}: legacy authorization_ref does not match current authorization")
        return receipt

    holdout_policy = policy.get("holdout")
    if _required(holdout_policy):
        receipt = evidence(holdout, "EvaluationReceipt/v2", "EvaluationReceipt/v1", holdout_policy, "holdout")
        if receipt:
            if receipt.get("check_type") != "holdout" or receipt.get("result") != "pass":
                errors.append("holdout receipt must be a passing holdout check")
            expected_descriptor = holdout_policy.get("descriptor_digest")
            if expected_descriptor and receipt.get("descriptor_digest") != expected_descriptor:
                errors.append("holdout receipt descriptor_digest does not match policy")
            expected_legacy_auth = holdout_policy.get("authorization_ref")
            if receipt.get("contract") == "EvaluationReceipt/v1" and expected_legacy_auth and receipt.get("authorization_ref") != expected_legacy_auth:
                errors.append("holdout legacy receipt authorization_ref does not match policy")

    graded_policy = policy.get("graded")
    if _required(graded_policy):
        receipt = evidence(graded, "GradedEvaluationReceipt/v2", "GradedEvaluationReceipt/v1", graded_policy, "graded")
        if receipt:
            if receipt.get("rubric_digest") != graded_policy.get("rubric_digest"):
                errors.append("graded receipt rubric_digest does not match policy")
            if graded_policy.get("threshold") is not None and receipt.get("threshold") != graded_policy.get("threshold"):
                errors.append("graded receipt threshold does not match policy")
            if receipt.get("result") != "pass":
                errors.append("graded receipt is not a pass")

    human_policy = policy.get("human")
    if _required(human_policy):
        receipt = evidence(human, "HumanAcceptanceReceipt/v2", "HumanAcceptanceReceipt/v1", human_policy, "human")
        if receipt:
            if receipt.get("owner") != human_policy.get("owner"):
                errors.append("human receipt owner does not match policy")
            if receipt.get("decision") != "accept":
                errors.append("human acceptance decision is not accept")

    env_policy = fm.get("environment_contract")
    if _required(env_policy):
        receipt = evidence(environment, "EnvironmentReceipt/v2", "EnvironmentReceipt/v1", env_policy, "environment")
        if receipt:
            if receipt.get("contract_digest") != env_policy.get("digest"):
                errors.append("environment receipt contract_digest does not match policy")
            if receipt.get("enforced") is not True:
                errors.append("environment receipt does not report enforcement")

    identity_policy = fm.get("identity_policy")
    if _required(identity_policy):
        receipt, _ = _load(identity, "AuthorizationReceipt/v1", "AuthorizationReceipt/v1", errors)
        if receipt:
            auth = str(fm.get("signed_off_sig", ""))
            if receipt.get("task_id") != fm.get("id") or receipt.get("authorization_ref") != auth:
                errors.append("identity receipt does not match task authorization")
            if identity_policy.get("key_id") and receipt.get("key_id") != identity_policy.get("key_id"):
                errors.append("identity receipt key_id is not trusted by policy")
            if not identity_public_key:
                errors.append("required identity receipt needs --identity-public-key")
            else:
                errors.extend(
                    f"identity verification: {item}" for item in verify_identity(
                        receipt, pathlib.Path(identity_public_key),
                        pathlib.Path(identity_revocations) if identity_revocations else None,
                    )
                )
            proof.append(f"identity:{receipt.get('key_id')}")

    failure_codes: list[str] = []
    if any("was not supplied" in error for error in errors):
        failure_codes.append("RECEIPT_MISSING")
    if any("subject" in error or "does not match" in error for error in errors):
        failure_codes.append("RECEIPT_SUBJECT_MISMATCH")
    if any("predates" in error or "max_age" in error for error in errors):
        failure_codes.append("RECEIPT_STALE")
    if any("signature" in error or "trust-registry" in error for error in errors):
        failure_codes.append("RECEIPT_SIGNATURE_INVALID")
    if errors and not failure_codes:
        failure_codes.append("RECEIPT_SUBJECT_MISMATCH")
    tier = 2 if tier2_reasons else 1
    return {
        "contract": "AcceptancePolicyResult/v1", "ok": not errors,
        "tier": tier, "proof": proof, "tier2_reasons": sorted(set(tier2_reasons)),
        "errors": errors, "failure_codes": sorted(set(failure_codes)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--handoff")
    parser.add_argument("--holdout-receipt")
    parser.add_argument("--graded-receipt")
    parser.add_argument("--human-receipt")
    parser.add_argument("--environment-receipt")
    parser.add_argument("--identity-receipt")
    parser.add_argument("--identity-public-key")
    parser.add_argument("--identity-revocations")
    parser.add_argument("--trust-registry")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        fm = frontmatter(pathlib.Path(args.spec).read_text(encoding="utf-8"))
        handoff = load_receipt(pathlib.Path(args.handoff)) if args.handoff else None
        result = evaluate(
            fm, handoff=handoff, holdout=args.holdout_receipt, graded=args.graded_receipt,
            human=args.human_receipt, environment=args.environment_receipt,
            identity=args.identity_receipt, identity_public_key=args.identity_public_key,
            identity_revocations=args.identity_revocations, trust_registry=args.trust_registry,
        )
    except (OSError, DataError, ValueError) as exc:
        result = {
            "contract": "AcceptancePolicyResult/v1", "ok": False, "tier": 2,
            "proof": [], "tier2_reasons": [], "errors": [str(exc)],
            "failure_codes": ["RECEIPT_SUBJECT_MISMATCH"],
        }
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    elif not result["ok"]:
        for error in result["errors"]:
            print(f"BLOCK — {error}")
    else:
        suffix = f" ({', '.join(result['proof'])})" if result["proof"] else ""
        print(f"PASS — acceptance evidence policy satisfied; Tier {result['tier']}{suffix}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
