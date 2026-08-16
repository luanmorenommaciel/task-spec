#!/usr/bin/env python3
"""Normalize local release gates, packaging, checksums, and install evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import pathlib
import re
import subprocess
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]


def digest(path: pathlib.Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def timestamp() -> str:
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "0"))
    return datetime.fromtimestamp(epoch, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def required_tokens(log: str) -> dict[str, bool]:
    return {
        token: bool(re.search(rf"^{re.escape(token)}$", log, re.M))
        for token in (
            "CHECK=READY", "CONFORMANCE=L2", "DEMO=READY", "INSTALL=OK",
            "MESH_CONFORMANCE=READY", "MESH_RECOVERY=READY", "MESH_DEMO=READY",
            "MESH_INSTALL=READY", "MESH_ISOLATION=READY",
        )
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-archive", required=True)
    parser.add_argument("--evidence-archive", required=True)
    parser.add_argument("--sbom", required=True)
    parser.add_argument("--gate-log", required=True)
    parser.add_argument("--install-log", required=True)
    parser.add_argument("--mesh-manifest")
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    out_dir = pathlib.Path(args.out_dir or f"release/{version}").resolve()
    source_archive = pathlib.Path(args.source_archive).resolve()
    evidence_archive = pathlib.Path(args.evidence_archive).resolve()
    sbom = pathlib.Path(args.sbom).resolve()
    gate_log_path = pathlib.Path(args.gate_log).resolve()
    install_log_path = pathlib.Path(args.install_log).resolve()
    gate_log = gate_log_path.read_text(encoding="utf-8", errors="replace")
    install_log = install_log_path.read_text(encoding="utf-8", errors="replace")
    tokens = required_tokens(gate_log)
    if not all(tokens.values()):
        missing = [name for name, present in tokens.items() if not present]
        raise SystemExit("local gate log is missing: " + ", ".join(missing))
    install_checks = {
        "checkout_copy": "✓ copy install" in install_log,
        "checkout_symlink": "✓ checkout symlink install" in install_log,
        "local_npm": "✓ local npm package install" in install_log,
        "checksum_archive": "✓ checksum-backed remote install" in install_log,
        "tamper_rejection": "✓ tampered release archive fails closed" in install_log,
        "taskmesh_helper": "MESH_INSTALL=READY" in install_log,
    }
    if not all(install_checks.values()) or "INSTALL=OK" not in install_log:
        raise SystemExit("local installation matrix did not pass every required door")

    local_gates = {
        "contract": "TaskSpecLocalGateEvidence/v1",
        "version": version,
        "observed_at": timestamp(),
        "source": {
            "commit_before_evidence_finalization": git("rev-parse", "HEAD"),
            "branch": git("branch", "--show-current"),
            "source_archive": source_archive.name,
            "source_archive_digest": digest(source_archive),
        },
        "command": ["make", "check"],
        "tokens": tokens,
        "log_asset": {"name": f"task-spec-{version}-local-gates.log", "digest": digest(gate_log_path)},
        "suites": {
            "authority_contracts": {"state": "pass", "proof": ["TaskAuthorization/v3", "TaskHandoff/v3", "ReceiptSubject/v1"]},
            "honest_hmac_boundary": {"state": "pass", "proof": ["HMAC is documented as shared-key tamper evidence, not identity or semantic truth"]},
            "graph_recovery": {"state": "pass", "proof": ["TaskGraphView/v1 deterministic graph and crash recovery suites"]},
            "atomic_acceptance": {"state": "pass", "proof": ["AcceptanceRecord/v1 replay, mismatch, and crash-fault suites"]},
            "taskmesh_control_plane": {"state": "pass", "proof": ["leases, fencing, recovery, routing, adapters, cockpit, isolation, and target-branch safety"]},
        },
        "limitations": ["Local evidence is not hosted CI evidence."],
    }
    install_matrix = {
        "contract": "InstallationMatrixEvidence/v1",
        "version": version,
        "observed_at": timestamp(),
        "source_archive_digest": digest(source_archive),
        "local": {name: {"state": "pass" if passed else "fail"} for name, passed in install_checks.items()},
        "remote": {
            "pinned_curl_linux": {"state": "pending"},
            "pinned_curl_macos": {"state": "pending"},
            "github_npm_linux": {"state": "pending"},
            "github_npm_macos": {"state": "pending"},
        },
        "log_asset": {"name": f"task-spec-{version}-install.log", "digest": digest(install_log_path)},
        "complete": False,
    }
    local_path = out_dir / "local-gates.json"
    install_path = out_dir / "install-matrix.json"
    write(local_path, local_gates)
    write(install_path, install_matrix)

    artifact_rows = [
        {"name": source_archive.name, "digest": digest(source_archive)},
        {"name": evidence_archive.name, "digest": digest(evidence_archive)},
        {"name": sbom.name, "digest": digest(sbom)},
    ]
    if args.mesh_manifest:
        mesh_manifest = pathlib.Path(args.mesh_manifest).resolve()
        artifact_rows.append({"name": mesh_manifest.name, "digest": digest(mesh_manifest)})
    checksum_path = out_dir / "checksums.txt"
    checksum_path.write_text(
        "".join(f"{row['digest'][7:]}  {row['name']}\n" for row in sorted(artifact_rows, key=lambda row: row["name"])),
        encoding="utf-8",
    )
    report = {
        "contract": "TaskSpecReleaseReport/v1",
        "version": version,
        "generated_at": timestamp(),
        "source": local_gates["source"],
        "artifacts": artifact_rows,
        "checksums": {"path": "checksums.txt", "digest": digest(checksum_path)},
        "sbom": {"format": "SPDX-2.3", "path": sbom.name, "digest": digest(sbom)},
        "local_gates": {"path": "local-gates.json", "digest": digest(local_path), "state": "pass"},
        "installation": {"path": "install-matrix.json", "digest": digest(install_path), "state": "partial"},
        "hosted_ci": {"state": "pending"},
        "provenance_attestation": {"state": "pending"},
        "publication": {"state": "pending"},
    }
    write(out_dir / "release-report.json", report)
    print(f"LOCAL_GATES=READY source_archive={digest(source_archive)}")
    print("INSTALL_MATRIX=LOCAL_READY remote=pending")
    print(f"RELEASE_REPORT=READY path={out_dir / 'release-report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
