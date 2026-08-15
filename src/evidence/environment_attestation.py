#!/usr/bin/env python3
"""Create and verify EnvironmentAttestation/v1 sandbox evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import tempfile
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(ROOT / "src" / "evidence"))
sys.path.insert(0, str(ROOT / "src" / "security"))
from receipts import load as load_receipt, validate as validate_receipt  # noqa: E402
from evaluator_trust import verify as verify_evaluator  # noqa: E402


TOP_LEVEL = {
    "contract", "observed_at", "result", "verified", "runtime", "image_digest",
    "isolation", "command", "command_digest", "artifact_digest", "error",
}


class AttestationError(ValueError):
    """The attestation cannot establish the declared environment boundary."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def digest_file(path: pathlib.Path) -> str:
    return digest_bytes(path.read_bytes())


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return digest_bytes(payload)


def load(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AttestationError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AttestationError(f"{path}: expected a JSON object")
    return value


def atomic_write(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _sha256(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
        errors.append(f"{field} must use sha256:<64 lowercase hex>")
        return
    try:
        int(value[7:], 16)
    except ValueError:
        errors.append(f"{field} must use sha256:<64 lowercase hex>")
    if value[7:] != value[7:].lower():
        errors.append(f"{field} must use lowercase hex")


def validate(value: dict[str, Any], *, require_verified: bool = False) -> list[str]:
    errors: list[str] = []
    unknown = sorted(set(value) - TOP_LEVEL)
    if unknown:
        errors.append(f"unknown fields: {', '.join(unknown)}")
    if value.get("contract") != "EnvironmentAttestation/v1":
        errors.append("contract must be EnvironmentAttestation/v1")
    try:
        datetime.fromisoformat(str(value.get("observed_at", "")).replace("Z", "+00:00"))
    except ValueError:
        errors.append("observed_at must be an ISO-8601 timestamp")
    result = value.get("result")
    if result not in {"pass", "fail", "unavailable"}:
        errors.append("result must be pass, fail, or unavailable")
    verified = value.get("verified")
    if not isinstance(verified, bool):
        errors.append("verified must be a boolean")
    if require_verified and (result != "pass" or verified is not True):
        errors.append("verified sandbox evidence requires result=pass and verified=true")
    if result == "pass":
        if verified is not True:
            errors.append("pass requires verified=true")
        runtime = value.get("runtime")
        if not isinstance(runtime, dict) or set(runtime) != {"name", "version", "kernel"}:
            errors.append("runtime must contain exactly name, version, and kernel")
        else:
            if runtime.get("name") not in {"docker", "podman"}:
                errors.append("runtime.name must be docker or podman")
            if not all(isinstance(runtime.get(item), str) and runtime[item] for item in ("version", "kernel")):
                errors.append("runtime version and kernel must be non-empty strings")
        _sha256(value.get("image_digest"), "image_digest", errors)
        command = value.get("command")
        if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
            errors.append("command must be a non-empty string array")
        elif value.get("command_digest") != canonical_digest(command):
            errors.append("command_digest does not match command")
        _sha256(value.get("command_digest"), "command_digest", errors)
        _sha256(value.get("artifact_digest"), "artifact_digest", errors)
        isolation = value.get("isolation")
        expected_isolation = {
            "network", "read_only_root", "capabilities_dropped", "no_new_privileges",
            "writable_mounts", "limits",
        }
        if not isinstance(isolation, dict) or set(isolation) != expected_isolation:
            errors.append("isolation has an incomplete or unknown field set")
        else:
            if isolation.get("network") not in {"none", "attempt_proxy_only"}:
                errors.append("isolation.network is invalid")
            for field in ("read_only_root", "capabilities_dropped", "no_new_privileges"):
                if isolation.get(field) is not True:
                    errors.append(f"isolation.{field} must be true")
            mounts = isolation.get("writable_mounts")
            if not isinstance(mounts, list) or not 1 <= len(mounts) <= 2 or not all(isinstance(item, str) and item for item in mounts):
                errors.append("isolation.writable_mounts must contain one or two paths")
            limits = isolation.get("limits")
            expected_limits = {"cpus", "memory_mb", "pids", "timeout_sec", "tmpfs_mb"}
            if not isinstance(limits, dict) or set(limits) != expected_limits:
                errors.append("isolation.limits has an incomplete or unknown field set")
            else:
                if not isinstance(limits.get("cpus"), (int, float)) or isinstance(limits.get("cpus"), bool) or limits["cpus"] <= 0:
                    errors.append("isolation.limits.cpus must be positive")
                for field in ("memory_mb", "pids", "timeout_sec", "tmpfs_mb"):
                    if not isinstance(limits.get(field), int) or isinstance(limits.get(field), bool) or limits[field] < 1:
                        errors.append(f"isolation.limits.{field} must be a positive integer")
    else:
        if verified is True:
            errors.append("fail or unavailable requires verified=false")
        if not isinstance(value.get("error"), str) or not value["error"]:
            errors.append("fail or unavailable requires a non-empty error")
    return errors


def record(args: argparse.Namespace) -> dict[str, Any]:
    command = json.loads(args.command_json)
    if not isinstance(command, list):
        raise AttestationError("--command-json must encode an array")
    value: dict[str, Any] = {
        "contract": "EnvironmentAttestation/v1",
        "observed_at": args.observed_at or utc_now(),
        "result": "pass",
        "verified": True,
        "runtime": {"name": args.runtime, "version": args.runtime_version, "kernel": args.kernel},
        "image_digest": args.image_digest,
        "isolation": {
            "network": args.network,
            "read_only_root": True,
            "capabilities_dropped": True,
            "no_new_privileges": True,
            "writable_mounts": args.writable_mount,
            "limits": {
                "cpus": args.cpus,
                "memory_mb": args.memory_mb,
                "pids": args.pids,
                "timeout_sec": args.timeout_sec,
                "tmpfs_mb": args.tmpfs_mb,
            },
        },
        "command": command,
        "command_digest": canonical_digest(command),
        "artifact_digest": digest_file(pathlib.Path(args.artifact)),
    }
    errors = validate(value, require_verified=True)
    if errors:
        raise AttestationError("; ".join(errors))
    return value


def verify(attestation_path: pathlib.Path, receipt_path: pathlib.Path, registry_path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    attestation = load(attestation_path)
    errors.extend(validate(attestation, require_verified=True))
    receipt = load_receipt(receipt_path)
    errors.extend(validate_receipt(receipt))
    if receipt.get("contract") != "EnvironmentReceipt/v2":
        errors.append("receipt must be EnvironmentReceipt/v2")
    if receipt.get("environment_digest") != digest_file(attestation_path):
        errors.append("EnvironmentReceipt environment_digest does not match attestation bytes")
    errors.extend(verify_evaluator(receipt, registry_path))
    return errors


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command_name", required=True)
    validate_cmd = sub.add_parser("validate")
    validate_cmd.add_argument("attestation")
    validate_cmd.add_argument("--require-verified", action="store_true")
    digest_cmd = sub.add_parser("digest")
    digest_cmd.add_argument("attestation")
    verify_cmd = sub.add_parser("verify")
    verify_cmd.add_argument("attestation")
    verify_cmd.add_argument("--receipt", required=True)
    verify_cmd.add_argument("--trust-registry", required=True)
    record_cmd = sub.add_parser("record")
    record_cmd.add_argument("--runtime", choices=("docker", "podman"), required=True)
    record_cmd.add_argument("--runtime-version", required=True)
    record_cmd.add_argument("--kernel", required=True)
    record_cmd.add_argument("--image-digest", required=True)
    record_cmd.add_argument("--network", choices=("none", "attempt_proxy_only"), required=True)
    record_cmd.add_argument("--writable-mount", action="append", required=True)
    record_cmd.add_argument("--cpus", type=float, required=True)
    record_cmd.add_argument("--memory-mb", type=int, required=True)
    record_cmd.add_argument("--pids", type=int, required=True)
    record_cmd.add_argument("--timeout-sec", type=int, required=True)
    record_cmd.add_argument("--tmpfs-mb", type=int, required=True)
    record_cmd.add_argument("--command-json", required=True)
    record_cmd.add_argument("--artifact", required=True)
    record_cmd.add_argument("--observed-at")
    record_cmd.add_argument("--out", required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command_name == "record":
            value = record(args)
            atomic_write(pathlib.Path(args.out), value)
            print(f"SANDBOX_ATTESTATION=RECORDED digest={digest_file(pathlib.Path(args.out))} path={args.out}")
        elif args.command_name == "digest":
            print(digest_file(pathlib.Path(args.attestation)))
        elif args.command_name == "validate":
            errors = validate(load(pathlib.Path(args.attestation)), require_verified=args.require_verified)
            if errors:
                raise AttestationError("; ".join(errors))
            print(f"SANDBOX_ATTESTATION=VALID path={args.attestation}")
        else:
            errors = verify(pathlib.Path(args.attestation), pathlib.Path(args.receipt), pathlib.Path(args.trust_registry))
            if errors:
                raise AttestationError("; ".join(errors))
            print(f"SANDBOX_ATTESTATION=VERIFIED path={args.attestation}")
        return 0
    except (OSError, json.JSONDecodeError, AttestationError, ValueError) as exc:
        print(f"SANDBOX_ATTESTATION=INVALID error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
