#!/usr/bin/env python3
"""Optional Ed25519 identity receipts for Task-Spec HMAC authorizations."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
from taskspec_data import DataError, canonical_digest, frontmatter  # noqa: E402


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("identity receipt must be a JSON object")
    return value


def payload_for(spec: pathlib.Path) -> tuple[dict[str, str], dict[str, Any]]:
    fm = frontmatter(spec.read_text(encoding="utf-8"))
    signature = fm.get("signed_off_sig")
    if not isinstance(signature, str) or not signature.startswith("hmac-sha256-v2:"):
        raise ValueError("identity signing requires a verified Tier 1 HMAC v2 authorization")
    payload = {"task_id": str(fm.get("id")), "authorization_ref": signature}
    return payload, fm


def openssl(*args: str, stdin: bytes | None = None) -> bytes:
    completed = subprocess.run(["openssl", *args], input=stdin, capture_output=True, check=False)
    if completed.returncode:
        raise ValueError(completed.stderr.decode(errors="replace").strip() or "openssl failed")
    return completed.stdout


def fingerprint(public_key: pathlib.Path) -> str:
    der = openssl("pkey", "-pubin", "-in", str(public_key), "-outform", "DER")
    return hashlib.sha256(der).hexdigest()


def sign(spec: pathlib.Path, private_key: pathlib.Path, public_key: pathlib.Path, signer: str) -> dict[str, Any]:
    payload, _ = payload_for(spec)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    with tempfile.NamedTemporaryFile() as payload_file:
        payload_file.write(canonical); payload_file.flush()
        signature = openssl("pkeyutl", "-sign", "-rawin", "-inkey", str(private_key), "-in", payload_file.name)
    key_id = fingerprint(public_key)[:16]
    return {
        "contract": "AuthorizationReceipt/v1", **payload, "signer": signer, "key_id": key_id,
        "public_key_fingerprint": f"sha256:{fingerprint(public_key)}", "payload_digest": f"sha256:{canonical_digest(payload)}",
        "algorithm": "Ed25519", "signed_at": now(), "signature": base64.b64encode(signature).decode(), "status": "verified",
    }


def verify(receipt: dict[str, Any], public_key: pathlib.Path, revocations: pathlib.Path | None) -> list[str]:
    errors: list[str] = []
    if receipt.get("contract") != "AuthorizationReceipt/v1":
        errors.append("contract must be AuthorizationReceipt/v1")
        return errors
    key_id = fingerprint(public_key)[:16]
    if receipt.get("key_id") != key_id:
        errors.append("public key does not match receipt key_id")
    if revocations and revocations.exists():
        registry = load(revocations)
        if key_id in registry.get("revoked_key_ids", []):
            errors.append("signing key is revoked")
    payload = {"task_id": receipt.get("task_id"), "authorization_ref": receipt.get("authorization_ref")}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    try:
        signature = base64.b64decode(str(receipt.get("signature", "")), validate=True)
        with tempfile.NamedTemporaryFile() as handle, tempfile.NamedTemporaryFile() as payload_file:
            handle.write(signature); handle.flush()
            payload_file.write(canonical); payload_file.flush()
            openssl("pkeyutl", "-verify", "-rawin", "-pubin", "-inkey", str(public_key), "-sigfile", handle.name, "-in", payload_file.name)
    except (ValueError, base64.binascii.Error) as exc:
        errors.append(f"signature does not verify: {exc}")
    return errors


def write(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init"); init.add_argument("--out-dir", required=True); init.add_argument("--force", action="store_true")
    sign_cmd = sub.add_parser("sign"); sign_cmd.add_argument("spec"); sign_cmd.add_argument("--private-key", required=True); sign_cmd.add_argument("--public-key", required=True); sign_cmd.add_argument("--signer", required=True); sign_cmd.add_argument("--out", required=True)
    verify_cmd = sub.add_parser("verify"); verify_cmd.add_argument("receipt"); verify_cmd.add_argument("--public-key", required=True); verify_cmd.add_argument("--revocations")
    revoke = sub.add_parser("revoke"); revoke.add_argument("--key-id", required=True); revoke.add_argument("--registry", required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            out = pathlib.Path(args.out_dir); private = out / "identity.ed25519.pem"; public = out / "identity.ed25519.pub.pem"
            if not args.force and (private.exists() or public.exists()):
                raise ValueError("identity key already exists; pass --force to replace it")
            out.mkdir(parents=True, exist_ok=True)
            openssl("genpkey", "-algorithm", "Ed25519", "-out", str(private))
            openssl("pkey", "-in", str(private), "-pubout", "-out", str(public))
            private.chmod(0o600)
            print(f"IDENTITY=READY key_id={fingerprint(public)[:16]} public_key={public}")
        elif args.command == "sign":
            receipt = sign(pathlib.Path(args.spec), pathlib.Path(args.private_key), pathlib.Path(args.public_key), args.signer)
            signature_errors = verify(receipt, pathlib.Path(args.public_key), None)
            if signature_errors: raise ValueError("; ".join(signature_errors))
            write(pathlib.Path(args.out), receipt); print(f"IDENTITY=SIGNED key_id={receipt['key_id']} receipt={args.out}")
        elif args.command == "verify":
            receipt = load(pathlib.Path(args.receipt)); errors = verify(receipt, pathlib.Path(args.public_key), pathlib.Path(args.revocations) if args.revocations else None)
            if errors: raise ValueError("; ".join(errors))
            print(f"IDENTITY=VERIFIED signer={receipt.get('signer')} key_id={receipt.get('key_id')}")
        else:
            registry_path = pathlib.Path(args.registry)
            registry = load(registry_path) if registry_path.exists() else {"contract": "IdentityRevocations/v1", "revoked_key_ids": []}
            keys = registry.setdefault("revoked_key_ids", [])
            if args.key_id not in keys: keys.append(args.key_id)
            write(registry_path, registry); print(f"IDENTITY=REVOKED key_id={args.key_id}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, DataError) as exc:
        print(f"IDENTITY=INVALID error={exc}", file=sys.stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())
