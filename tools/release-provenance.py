#!/usr/bin/env python3
"""Create and verify private Task-Spec release provenance.

The output is a standard DSSE envelope containing an in-toto Statement/v1 with
an SLSA Provenance/v1 predicate. Signing uses an Ed25519 private key that is
supplied explicitly and never embedded in the envelope.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
from typing import Any


PAYLOAD_TYPE = "application/vnd.in-toto+json"
STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_TYPE = "https://slsa.dev/provenance/v1"
BUILD_TYPE = "https://taskspec.dev/build/private-release/v1"


class ProvenanceError(Exception):
    """A release provenance contract is invalid."""


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_file(path: pathlib.Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ProvenanceError(f"cannot digest {path}: {exc}") from exc


def pae(payload_type: str, payload: bytes) -> bytes:
    encoded_type = payload_type.encode("utf-8")
    return b"DSSEv1 %d %s %d " % (len(encoded_type), encoded_type, len(payload)) + payload


def openssl(*args: str) -> bytes:
    completed = subprocess.run(["openssl", *args], capture_output=True, check=False)
    if completed.returncode:
        message = completed.stderr.decode(errors="replace").strip() or "openssl failed"
        raise ProvenanceError(message)
    return completed.stdout


def fingerprint(public_key: pathlib.Path) -> str:
    der = openssl("pkey", "-pubin", "-in", str(public_key), "-outform", "DER")
    return hashlib.sha256(der).hexdigest()


def parse_time(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProvenanceError(f"invalid UTC timestamp: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ProvenanceError(f"timestamp must be UTC: {value}")
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_statement(args: argparse.Namespace) -> dict[str, Any]:
    source_commit = args.source_commit.lower()
    if len(source_commit) != 40 or any(ch not in "0123456789abcdef" for ch in source_commit):
        raise ProvenanceError("source commit must be a full 40-character Git SHA")
    started = parse_time(args.started_at)
    finished = parse_time(args.finished_at)
    if finished < started:
        raise ProvenanceError("finished-at precedes started-at")
    archive = pathlib.Path(args.subject).resolve(strict=True)
    sbom = pathlib.Path(args.sbom).resolve(strict=True)
    return {
        "_type": STATEMENT_TYPE,
        "subject": [
            {"name": archive.name, "digest": {"sha256": digest_file(archive)}},
            {"name": sbom.name, "digest": {"sha256": digest_file(sbom)}},
        ],
        "predicateType": PREDICATE_TYPE,
        "predicate": {
            "buildDefinition": {
                "buildType": BUILD_TYPE,
                "externalParameters": {
                    "releaseVersion": args.release_version,
                    "releaseRef": args.release_ref,
                    "repositoryVisibility": "private",
                },
                "internalParameters": {},
                "resolvedDependencies": [
                    {
                        "uri": f"git+https://github.com/{args.source_repository}.git@{source_commit}",
                        "digest": {"gitCommit": source_commit},
                    }
                ],
            },
            "runDetails": {
                "builder": {"id": args.builder_id},
                "metadata": {
                    "invocationId": args.invocation_id,
                    "startedOn": started,
                    "finishedOn": finished,
                },
                "byproducts": [],
            },
        },
    }


def sign_statement(
    statement: dict[str, Any], private_key: pathlib.Path, public_key: pathlib.Path
) -> dict[str, Any]:
    payload = canonical(statement)
    signed = pae(PAYLOAD_TYPE, payload)
    with tempfile.NamedTemporaryFile() as payload_file:
        payload_file.write(signed)
        payload_file.flush()
        signature = openssl(
            "pkeyutl", "-sign", "-rawin", "-inkey", str(private_key), "-in", payload_file.name
        )
    return {
        "payloadType": PAYLOAD_TYPE,
        "payload": base64.b64encode(payload).decode("ascii"),
        "signatures": [
            {
                "keyid": fingerprint(public_key)[:16],
                "sig": base64.b64encode(signature).decode("ascii"),
            }
        ],
    }


def load_object(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProvenanceError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProvenanceError(f"{path} must contain a JSON object")
    return value


def expected_subject(path: pathlib.Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    return {"name": resolved.name, "digest": {"sha256": digest_file(resolved)}}


def verify_envelope(args: argparse.Namespace) -> dict[str, Any]:
    envelope = load_object(pathlib.Path(args.envelope))
    if set(envelope) != {"payloadType", "payload", "signatures"}:
        raise ProvenanceError("DSSE envelope contains unsupported fields")
    if envelope.get("payloadType") != PAYLOAD_TYPE:
        raise ProvenanceError("DSSE payloadType is not application/vnd.in-toto+json")
    signatures = envelope.get("signatures")
    if not isinstance(signatures, list) or len(signatures) != 1 or not isinstance(signatures[0], dict):
        raise ProvenanceError("DSSE envelope requires exactly one signature")
    try:
        payload = base64.b64decode(str(envelope.get("payload", "")), validate=True)
        signature = base64.b64decode(str(signatures[0].get("sig", "")), validate=True)
        statement = json.loads(payload)
    except (base64.binascii.Error, json.JSONDecodeError, ValueError) as exc:
        raise ProvenanceError(f"invalid DSSE encoding: {exc}") from exc
    if not isinstance(statement, dict) or canonical(statement) != payload:
        raise ProvenanceError("in-toto payload is not canonical JSON")

    public_key = pathlib.Path(args.public_key)
    if signatures[0].get("keyid") != fingerprint(public_key)[:16]:
        raise ProvenanceError("DSSE keyid does not match the trusted public key")
    signed = pae(PAYLOAD_TYPE, payload)
    with tempfile.NamedTemporaryFile() as payload_file, tempfile.NamedTemporaryFile() as signature_file:
        payload_file.write(signed)
        payload_file.flush()
        signature_file.write(signature)
        signature_file.flush()
        completed = subprocess.run(
            [
                "openssl", "pkeyutl", "-verify", "-rawin", "-pubin", "-inkey", str(public_key),
                "-sigfile", signature_file.name, "-in", payload_file.name,
            ],
            capture_output=True,
            check=False,
        )
        if completed.returncode:
            raise ProvenanceError("DSSE Ed25519 signature does not verify")

    if statement.get("_type") != STATEMENT_TYPE or statement.get("predicateType") != PREDICATE_TYPE:
        raise ProvenanceError("unsupported in-toto statement or predicate type")
    subjects = statement.get("subject")
    expected = [expected_subject(pathlib.Path(args.subject)), expected_subject(pathlib.Path(args.sbom))]
    if subjects != expected:
        raise ProvenanceError("release archive or SBOM digest does not match provenance")
    predicate = statement.get("predicate")
    if not isinstance(predicate, dict):
        raise ProvenanceError("provenance predicate is missing")
    definition = predicate.get("buildDefinition")
    details = predicate.get("runDetails")
    if not isinstance(definition, dict) or not isinstance(details, dict):
        raise ProvenanceError("provenance build definition or run details are missing")
    if definition.get("buildType") != BUILD_TYPE:
        raise ProvenanceError("unexpected private release build type")
    parameters = definition.get("externalParameters")
    if not isinstance(parameters, dict) or parameters != {
        "releaseVersion": args.release_version,
        "releaseRef": args.release_ref,
        "repositoryVisibility": "private",
    }:
        raise ProvenanceError("release identity does not match provenance")
    source_commit = args.source_commit.lower()
    expected_dependency = {
        "uri": f"git+https://github.com/{args.source_repository}.git@{source_commit}",
        "digest": {"gitCommit": source_commit},
    }
    if definition.get("resolvedDependencies") != [expected_dependency]:
        raise ProvenanceError("source repository or commit does not match provenance")
    metadata = details.get("metadata")
    builder = details.get("builder")
    if not isinstance(builder, dict) or not builder.get("id"):
        raise ProvenanceError("provenance builder identity is missing")
    if not isinstance(metadata, dict) or not metadata.get("invocationId"):
        raise ProvenanceError("provenance invocation identity is missing")
    parse_time(str(metadata.get("startedOn", "")))
    parse_time(str(metadata.get("finishedOn", "")))
    return statement


def write_atomic(path: pathlib.Path, value: dict[str, Any], force: bool) -> None:
    if path.exists() and not force:
        raise ProvenanceError(f"refusing to overwrite {path}; pass --force")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def add_identity_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--release-version", required=True)
    parser.add_argument("--release-ref", required=True)
    parser.add_argument("--source-repository", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--sbom", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    add_identity_flags(create)
    create.add_argument("--builder-id", required=True)
    create.add_argument("--invocation-id", required=True)
    create.add_argument("--started-at", required=True)
    create.add_argument("--finished-at", required=True)
    create.add_argument("--private-key", required=True)
    create.add_argument("--public-key", required=True)
    create.add_argument("--out", required=True)
    create.add_argument("--force", action="store_true")
    verify = commands.add_parser("verify")
    add_identity_flags(verify)
    verify.add_argument("--envelope", required=True)
    verify.add_argument("--public-key", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "create":
            statement = build_statement(args)
            envelope = sign_statement(
                statement, pathlib.Path(args.private_key), pathlib.Path(args.public_key)
            )
            write_atomic(pathlib.Path(args.out), envelope, args.force)
            print(f"PROVENANCE=CREATED path={args.out} key_id={envelope['signatures'][0]['keyid']}")
        else:
            statement = verify_envelope(args)
            print(
                "PROVENANCE=VERIFIED "
                f"release_ref={args.release_ref} subjects={len(statement['subject'])}"
            )
        return 0
    except (OSError, ProvenanceError) as exc:
        print(f"PROVENANCE=INVALID error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
