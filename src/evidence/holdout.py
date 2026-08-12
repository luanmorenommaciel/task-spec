#!/usr/bin/env python3
"""Seal, verify, and run hidden holdout bundles without exposing them to executors."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def _write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _key(path: str | None) -> bytes | None:
    if path:
        return pathlib.Path(path).read_bytes().rstrip(b"\n")
    raw = os.environ.get("TASKSPEC_HOLDOUT_KEY")
    return raw.encode("utf-8") if raw else None


def validate_bundle(bundle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if bundle.get("contract") != "HoldoutBundle/v1":
        errors.append("contract must be HoldoutBundle/v1")
    if not isinstance(bundle.get("task_id"), str) or not bundle.get("task_id"):
        errors.append("task_id is required")
    checks = bundle.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("checks must be a non-empty list")
        return errors
    seen: set[str] = set()
    for index, check in enumerate(checks):
        where = f"checks[{index}]"
        if not isinstance(check, dict):
            errors.append(f"{where} must be an object")
            continue
        check_id = check.get("id")
        if not isinstance(check_id, str) or not check_id.startswith("holdout_"):
            errors.append(f"{where}.id must start with holdout_")
        elif check_id in seen:
            errors.append(f"{where}.id is duplicated")
        else:
            seen.add(check_id)
        argv = check.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
            errors.append(f"{where}.argv must be a non-empty string array")
        verifies = check.get("verifies")
        if not isinstance(verifies, list) or not verifies or not all(isinstance(item, str) and item.startswith("B-") for item in verifies):
            errors.append(f"{where}.verifies must be a non-empty B-N array")
        timeout = check.get("timeout_sec", 300)
        if not isinstance(timeout, int) or not 1 <= timeout <= 3600:
            errors.append(f"{where}.timeout_sec must be 1..3600")
    return errors


def make_descriptor(bundle_path: pathlib.Path, bundle: dict[str, Any], key: bytes | None) -> dict[str, Any]:
    descriptor: dict[str, Any] = {
        "contract": "HoldoutDescriptor/v1",
        "task_id": bundle["task_id"],
        "bundle_digest": f"sha256:{_sha256(bundle_path)}",
        "behavior_refs": sorted({ref for check in bundle["checks"] for ref in check["verifies"]}),
        "check_count": len(bundle["checks"]),
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "seal": None,
    }
    if key:
        payload = dict(descriptor)
        payload.pop("seal", None)
        key_id = hashlib.sha256(key).hexdigest()[:12]
        mac = hmac.new(key, _canonical(payload), hashlib.sha256).hexdigest()
        descriptor["seal"] = f"hmac-sha256-v1:{key_id}:{mac}"
    return descriptor


def verify_descriptor(
    descriptor: dict[str, Any], bundle_path: pathlib.Path, bundle: dict[str, Any], key: bytes | None
) -> list[str]:
    errors = validate_bundle(bundle)
    if descriptor.get("contract") != "HoldoutDescriptor/v1":
        errors.append("descriptor contract must be HoldoutDescriptor/v1")
    if descriptor.get("task_id") != bundle.get("task_id"):
        errors.append("descriptor task_id does not match bundle")
    expected_digest = f"sha256:{_sha256(bundle_path)}"
    if descriptor.get("bundle_digest") != expected_digest:
        errors.append("holdout bundle digest mismatch")
    seal = descriptor.get("seal")
    if seal:
        if not key:
            errors.append("descriptor is sealed but no holdout key was supplied")
        else:
            parts = str(seal).split(":")
            if len(parts) != 3 or parts[0] != "hmac-sha256-v1":
                errors.append("descriptor seal is malformed")
            else:
                payload = dict(descriptor)
                payload.pop("seal", None)
                expected_key_id = hashlib.sha256(key).hexdigest()[:12]
                expected_mac = hmac.new(key, _canonical(payload), hashlib.sha256).hexdigest()
                if parts[1] != expected_key_id or not hmac.compare_digest(parts[2], expected_mac):
                    errors.append("descriptor HMAC does not verify")
    return errors


def run_bundle(bundle: dict[str, Any], workspace: pathlib.Path) -> tuple[bool, list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    for check in bundle["checks"]:
        started = datetime.now(timezone.utc)
        try:
            completed = subprocess.run(
                check["argv"],
                cwd=workspace,
                text=True,
                capture_output=True,
                timeout=check.get("timeout_sec", 300),
                check=False,
                env={**os.environ, "TASKSPEC_HOLDOUT": "1"},
            )
            exit_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except subprocess.TimeoutExpired as exc:
            exit_code = 124
            stdout = exc.stdout or ""
            stderr = (exc.stderr or "") + "\nholdout timed out"
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        finished = datetime.now(timezone.utc)
        expected = int(check.get("expected_exit", 0))
        results.append(
            {
                "id": check["id"],
                "verifies": check["verifies"],
                "passed": exit_code == expected,
                "exit_code": exit_code,
                "expected_exit": expected,
                "duration_ms": int((finished - started).total_seconds() * 1000),
                "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
                "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
            }
        )
    return all(item["passed"] for item in results), results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    seal = sub.add_parser("seal")
    seal.add_argument("bundle")
    seal.add_argument("--out", required=True)
    seal.add_argument("--key-file")

    verify = sub.add_parser("verify")
    verify.add_argument("descriptor")
    verify.add_argument("bundle")
    verify.add_argument("--key-file")

    run = sub.add_parser("run")
    run.add_argument("descriptor")
    run.add_argument("bundle")
    run.add_argument("--workspace", required=True)
    run.add_argument("--key-file")
    run.add_argument("--receipt-out")

    args = parser.parse_args()
    bundle_path = pathlib.Path(args.bundle).resolve()
    try:
        bundle = _read_json(bundle_path)
        errors = validate_bundle(bundle)
        if errors:
            raise ValueError("; ".join(errors))
        key = _key(args.key_file)
        if args.command == "seal":
            descriptor = make_descriptor(bundle_path, bundle, key)
            _write_json(pathlib.Path(args.out), descriptor)
            print(f"HOLDOUT=SEALED digest={descriptor['bundle_digest']} checks={descriptor['check_count']}")
            return 0
        descriptor = _read_json(pathlib.Path(args.descriptor))
        errors = verify_descriptor(descriptor, bundle_path, bundle, key)
        if errors:
            raise ValueError("; ".join(errors))
        if args.command == "verify":
            print(f"HOLDOUT=VERIFIED digest={descriptor['bundle_digest']}")
            return 0
        workspace = pathlib.Path(args.workspace).resolve()
        passed, results = run_bundle(bundle, workspace)
        receipt = {
            "contract": "EvaluationReceipt/v1",
            "task_id": bundle["task_id"],
            "check_type": "holdout",
            "authorization_ref": descriptor.get("seal") or descriptor["bundle_digest"],
            "descriptor_digest": f"sha256:{_sha256(pathlib.Path(args.descriptor))}",
            "evaluator": "taskspec-holdout-runner",
            "evaluated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "result": "pass" if passed else "fail",
            "evidence": results,
        }
        if args.receipt_out:
            _write_json(pathlib.Path(args.receipt_out), receipt)
        print(json.dumps(receipt, indent=2))
        return 0 if passed else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"HOLDOUT=INVALID error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
