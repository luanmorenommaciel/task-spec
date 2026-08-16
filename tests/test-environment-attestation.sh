#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ATTEST="$ROOT/src/evidence/environment_attestation.py"
RELEASE="$ROOT/release/3.8.1"
WORK="$(mktemp -d /tmp/taskspec-attestation-test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

python3 "$ATTEST" validate --require-verified "$RELEASE/environment-attestation.json" >/dev/null
python3 "$ATTEST" verify "$RELEASE/environment-attestation.json" \
  --receipt "$RELEASE/environment-receipt.json" \
  --trust-registry "$RELEASE/environment-trust.json" >/dev/null
"$ROOT/bin/taskspec" receipt validate "$RELEASE/environment-receipt.json" >/dev/null

python3 - "$ROOT" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root / "tests"))
from schema_contracts import validate_instance

attestation = json.loads((root / "release/3.8.1/environment-attestation.json").read_text(encoding="utf-8"))
proof = json.loads((root / "release/3.8.1/environment-proof.json").read_text(encoding="utf-8"))
validate_instance(attestation, "environment-attestation.schema.json")
assert attestation["result"] == "pass" and attestation["verified"] is True
assert attestation["isolation"] == {
    "network": "none",
    "read_only_root": True,
    "capabilities_dropped": True,
    "no_new_privileges": True,
    "writable_mounts": attestation["isolation"]["writable_mounts"],
    "limits": {"cpus": 1.0, "memory_mb": 256, "pids": 64, "timeout_sec": 120, "tmpfs_mb": 16},
}
assert len(attestation["isolation"]["writable_mounts"]) == 2
assert proof["contract"] == "SandboxReleaseProof/v1" and proof["result"] == "pass"
assert proof["accepted_tier"] == 1
assert proof["security_checks"]["one_workspace_bind"]
assert not proof["security_checks"]["docker_socket_mounted"]
assert proof["security_checks"]["credential_environment_count"] == 0
assert not proof["signing_key_mounted"] and not proof["evaluator_private_key_mounted"]
assert proof["tampered_attestation_rejected"] and proof["tampered_receipt_rejected"]
PY

cp "$RELEASE/environment-attestation.json" "$WORK/attestation.json"
python3 - "$WORK/attestation.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); value = json.loads(path.read_text(encoding="utf-8"))
value["isolation"]["network"] = "attempt_proxy_only"
path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
PY
if python3 "$ATTEST" verify "$WORK/attestation.json" --receipt "$RELEASE/environment-receipt.json" --trust-registry "$RELEASE/environment-trust.json" >/dev/null 2>&1; then
  echo "tampered attestation passed" >&2
  exit 1
fi

cp "$RELEASE/environment-receipt.json" "$WORK/receipt.json"
python3 - "$WORK/receipt.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); value = json.loads(path.read_text(encoding="utf-8"))
value["provider"] = "forged-attestor"
path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
PY
if python3 "$ATTEST" verify "$RELEASE/environment-attestation.json" --receipt "$WORK/receipt.json" --trust-registry "$RELEASE/environment-trust.json" >/dev/null 2>&1; then
  echo "tampered receipt passed" >&2
  exit 1
fi

grep -q '^FROM python@sha256:[0-9a-f]\{64\}$' "$ROOT/release/docker/Dockerfile"
grep -q -- '--network none' "$ROOT/release/docker/run-attestation.sh"
grep -q -- '--read-only' "$ROOT/release/docker/run-attestation.sh"
grep -q -- '--cap-drop ALL' "$ROOT/release/docker/run-attestation.sh"
grep -q -- '--security-opt no-new-privileges:true' "$ROOT/release/docker/run-attestation.sh"

echo "ENVIRONMENT_ATTESTATION=READY"
