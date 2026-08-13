#!/usr/bin/env python3
"""Ed25519 signatures and scoped trust for external evidence receipts."""

from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import subprocess
import tempfile
from typing import Any


def _canonical_unsigned(receipt: dict[str, Any]) -> bytes:
    payload = {key: value for key, value in receipt.items() if key != "signature"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _openssl(*args: str) -> bytes:
    completed = subprocess.run(["openssl", *args], capture_output=True, check=False)
    if completed.returncode:
        raise ValueError(completed.stderr.decode(errors="replace").strip() or "openssl failed")
    return completed.stdout


def fingerprint(public_key: pathlib.Path) -> str:
    der = _openssl("pkey", "-pubin", "-in", str(public_key), "-outform", "DER")
    return hashlib.sha256(der).hexdigest()


def sign(receipt: dict[str, Any], private_key: pathlib.Path, public_key: pathlib.Path) -> dict[str, Any]:
    value = dict(receipt)
    value.pop("signature", None)
    payload = _canonical_unsigned(value)
    with tempfile.NamedTemporaryFile() as payload_file:
        payload_file.write(payload); payload_file.flush()
        raw = _openssl("pkeyutl", "-sign", "-rawin", "-inkey", str(private_key), "-in", payload_file.name)
    digest = fingerprint(public_key)
    value["signature"] = {
        "algorithm": "Ed25519",
        "key_id": digest[:16],
        "public_key_fingerprint": f"sha256:{digest}",
        "payload_digest": f"sha256:{hashlib.sha256(payload).hexdigest()}",
        "value": base64.b64encode(raw).decode("ascii"),
    }
    return value


def load_registry(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read evaluator trust registry {path}: {exc}") from exc
    if not isinstance(value, dict) or value.get("contract") != "EvaluatorTrust/v1":
        raise ValueError("evaluator trust registry must be EvaluatorTrust/v1")
    if not isinstance(value.get("evaluators"), list):
        raise ValueError("EvaluatorTrust/v1 requires an evaluators list")
    return value


def verify(receipt: dict[str, Any], registry_path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    signature = receipt.get("signature")
    if not isinstance(signature, dict):
        return ["receipt has no Ed25519 signature"]
    if signature.get("algorithm") != "Ed25519":
        errors.append("receipt signature algorithm must be Ed25519")
    key_id = signature.get("key_id")
    try:
        registry = load_registry(registry_path)
    except ValueError as exc:
        return [str(exc)]
    entry = next((item for item in registry["evaluators"] if isinstance(item, dict) and item.get("key_id") == key_id), None)
    if not entry:
        return [f"receipt signer {key_id!r} is not trusted"]
    allowed = entry.get("receipt_classes", [])
    if receipt.get("contract") not in allowed:
        errors.append(f"signer {key_id!r} is not trusted for {receipt.get('contract')}")
    public_raw = entry.get("public_key")
    if not isinstance(public_raw, str) or not public_raw:
        errors.append(f"trusted evaluator {key_id!r} has no public_key")
        return errors
    public_key = pathlib.Path(public_raw)
    if not public_key.is_absolute():
        public_key = (registry_path.parent / public_key).resolve()
    try:
        actual_fingerprint = fingerprint(public_key)
        if key_id != actual_fingerprint[:16]:
            errors.append("trusted public key fingerprint does not match key_id")
        if signature.get("public_key_fingerprint") != f"sha256:{actual_fingerprint}":
            errors.append("receipt public_key_fingerprint does not match trusted key")
        payload = _canonical_unsigned(receipt)
        expected_digest = f"sha256:{hashlib.sha256(payload).hexdigest()}"
        if signature.get("payload_digest") != expected_digest:
            errors.append("receipt payload_digest does not match receipt content")
        raw = base64.b64decode(str(signature.get("value", "")), validate=True)
        with tempfile.NamedTemporaryFile() as sig_file, tempfile.NamedTemporaryFile() as payload_file:
            sig_file.write(raw); sig_file.flush()
            payload_file.write(payload); payload_file.flush()
            completed = subprocess.run(
                ["openssl", "pkeyutl", "-verify", "-rawin", "-pubin", "-inkey", str(public_key), "-sigfile", sig_file.name, "-in", payload_file.name],
                capture_output=True,
                check=False,
            )
            if completed.returncode:
                errors.append("receipt Ed25519 signature does not verify")
    except (OSError, ValueError, base64.binascii.Error) as exc:
        errors.append(f"receipt signature verification failed: {exc}")
    return errors
