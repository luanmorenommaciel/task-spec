#!/usr/bin/env python3
"""Optional DSSE export and independent verification for Task-Spec v2 receipts."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import pathlib
import subprocess
import tempfile
import sys
from typing import Any

PAYLOAD_TYPE = "application/vnd.taskspec.receipt+json"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pae(payload_type: str, payload: bytes) -> bytes:
    return b"DSSEv1 %d %s %d " % (len(payload_type.encode()), payload_type.encode(), len(payload)) + payload


def openssl(*args: str) -> bytes:
    result = subprocess.run(["openssl", *args], capture_output=True, check=False)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace").strip() or "openssl failed")
    return result.stdout


def fingerprint(public_key: pathlib.Path) -> str:
    return hashlib.sha256(openssl("pkey", "-pubin", "-in", str(public_key), "-outform", "DER")).hexdigest()


def export(receipt: dict[str, Any], private_key: pathlib.Path, public_key: pathlib.Path) -> dict[str, Any]:
    if not str(receipt.get("contract", "")).endswith("/v2"):
        raise ValueError("DSSE export accepts only v2 receipts")
    payload = canonical(receipt)
    signed = pae(PAYLOAD_TYPE, payload)
    with tempfile.NamedTemporaryFile() as handle:
        handle.write(signed); handle.flush()
        signature = openssl("pkeyutl", "-sign", "-rawin", "-inkey", str(private_key), "-in", handle.name)
    return {
        "payloadType": PAYLOAD_TYPE,
        "payload": base64.b64encode(payload).decode("ascii"),
        "signatures": [{"keyid": fingerprint(public_key)[:16], "sig": base64.b64encode(signature).decode("ascii")}],
    }


def verify(envelope: dict[str, Any], public_key: pathlib.Path) -> list[str]:
    errors: list[str] = []
    if envelope.get("payloadType") != PAYLOAD_TYPE:
        return ["DSSE payloadType is not a Task-Spec receipt"]
    try:
        payload = base64.b64decode(str(envelope.get("payload", "")), validate=True)
        receipt = json.loads(payload)
        signatures = envelope.get("signatures")
        if not isinstance(signatures, list) or len(signatures) != 1:
            return ["DSSE envelope requires exactly one signature"]
        signature = base64.b64decode(str(signatures[0].get("sig", "")), validate=True)
        if signatures[0].get("keyid") != fingerprint(public_key)[:16]:
            errors.append("DSSE keyid does not match public key")
        if not str(receipt.get("contract", "")).endswith("/v2"):
            errors.append("DSSE payload is not a v2 receipt")
        signed = pae(PAYLOAD_TYPE, payload)
        with tempfile.NamedTemporaryFile() as payload_file, tempfile.NamedTemporaryFile() as signature_file:
            payload_file.write(signed); payload_file.flush()
            signature_file.write(signature); signature_file.flush()
            result = subprocess.run(
                ["openssl", "pkeyutl", "-verify", "-rawin", "-pubin", "-inkey", str(public_key),
                 "-sigfile", signature_file.name, "-in", payload_file.name],
                capture_output=True, check=False,
            )
            if result.returncode:
                errors.append("DSSE Ed25519 signature does not verify")
    except (OSError, ValueError, json.JSONDecodeError, base64.binascii.Error) as exc:
        errors.append(f"invalid DSSE envelope: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    emit = sub.add_parser("export")
    emit.add_argument("receipt"); emit.add_argument("--private-key", required=True); emit.add_argument("--public-key", required=True); emit.add_argument("--out", required=True)
    check = sub.add_parser("verify")
    check.add_argument("envelope"); check.add_argument("--public-key", required=True)
    args = parser.parse_args()
    try:
        if args.command == "export":
            receipt = json.loads(pathlib.Path(args.receipt).read_text(encoding="utf-8"))
            value = export(receipt, pathlib.Path(args.private_key), pathlib.Path(args.public_key))
            pathlib.Path(args.out).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            print(f"DSSE=EXPORTED path={args.out}")
        else:
            value = json.loads(pathlib.Path(args.envelope).read_text(encoding="utf-8"))
            errors = verify(value, pathlib.Path(args.public_key))
            if errors: raise ValueError("; ".join(errors))
            print("DSSE=VERIFIED")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"DSSE=INVALID error={exc}", file=sys.stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())
