#!/usr/bin/env bash
# Produce retained, externally signed proof for one format-v4 portable acceptance.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TS="$ROOT/bin/taskspec"
ATTEST="$ROOT/src/evidence/environment_attestation.py"
OUT_DIR="$ROOT/release/3.8.1"
IMAGE_TAG="taskspec/sandbox-attestor:3.8.1"
ATTEMPT_ID="8ae65cd7-e6aa-4e44-8aec-efbd524c3352"
CONTAINER_NAME=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out-dir) [[ $# -ge 2 ]] || { echo "--out-dir requires a value" >&2; exit 2; }; OUT_DIR="$2"; shift 2 ;;
    --image-tag) [[ $# -ge 2 ]] || { echo "--image-tag requires a value" >&2; exit 2; }; IMAGE_TAG="$2"; shift 2 ;;
    --help|-h) sed -n '1,18p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

command -v docker >/dev/null 2>&1 || { echo "SANDBOX_ATTESTATION=UNAVAILABLE reason=docker-cli-missing" >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo "SANDBOX_ATTESTATION=UNAVAILABLE reason=docker-daemon-unavailable" >&2; exit 1; }
command -v openssl >/dev/null 2>&1 || { echo "SANDBOX_ATTESTATION=UNAVAILABLE reason=openssl-missing" >&2; exit 1; }

WORK="$(mktemp -d /tmp/taskspec-sandbox-work.XXXXXX)"
HOST_ONLY="$(mktemp -d /tmp/taskspec-sandbox-attestor.XXXXXX)"
WORK="$(cd "$WORK" && pwd -P)"
HOST_ONLY="$(cd "$HOST_ONLY" && pwd -P)"
cleanup() {
  if [[ -n "$CONTAINER_NAME" ]]; then docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true; fi
  if [[ "${TASKSPEC_KEEP_SANDBOX_WORK:-0}" == "1" ]]; then
    echo "SANDBOX_DEBUG_WORK=$WORK" >&2
    echo "SANDBOX_DEBUG_HOST=$HOST_ONLY" >&2
  else
    rm -rf "$WORK" "$HOST_ONLY"
  fi
}
trap cleanup EXIT

mkdir -p "$WORK/tasks" "$WORK/evidence" "$OUT_DIR"
git -C "$WORK" init -q
git -C "$WORK" config user.email sandbox-attestor@taskspec.invalid
git -C "$WORK" config user.name "Task-Spec sandbox attestor"

python3 - "$WORK/evidence/environment.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
value = {
    "contract": "EnvironmentContract/v1",
    "runtime": {"name": "docker", "version": "pinned-image"},
    "network": {"mode": "deny"},
    "filesystem": {"workspace": ".", "writes": ["src/marker.txt"]},
}
path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
PY
ENV_DIGEST="sha256:$(python3 - "$WORK/evidence/environment.json" "$ROOT/src/lib" <<'PY'
import json, sys
sys.path.insert(0, sys.argv[2])
from taskspec_data import canonical_digest
print(canonical_digest(json.load(open(sys.argv[1], encoding="utf-8"))))
PY
)"

python3 - "$WORK/tasks/T-20260815-sandbox-proof.md" "$ENV_DIGEST" <<'PY'
import pathlib, sys
path = pathlib.Path(sys.argv[1])
env_digest = sys.argv[2]
path.write_text(f'''---
id: T-20260815-sandbox-proof
title: Prove a portable sandbox acceptance
status: ready
format_version: 4
profile: standard
effort: XS
budget_iterations: 2
agent: any
parent: (none)
depends_on: []
touches_paths: []
creates_paths: [src/marker.txt]
source_note: Task-Spec 3.8.1 release sandbox evidence
created: 2026-08-15T00:00:00Z
tags: [sandbox, release-evidence]
owner: (none)
priority: P1
severity: security
due_date: (none)
precondition: (none)
blocked_reason: (none)
tracker_ref: (none)
execution_backend: ref-executor
signed_off: false
signed_off_by: (none)
signed_off_at: (none)
accepted: false
accepted_by: (none)
accepted_at: (none)
evaluation_policy:
  acceptance_scope: portable
  deterministic:
    required: true
environment_contract:
  required: true
  ref: evidence/environment.json
  digest: {env_digest}
---

# Prove a portable sandbox acceptance

> **Why:** Portable acceptance needs externally signed proof of an enforced runtime boundary.

## Goal

Write the literal text `done` into `src/marker.txt`.

## Context

The bundled reference executor runs without signing, evaluator, model, or provider credentials.

## Behavior

- **B-1** — GIVEN an empty workspace WHEN the reference executor runs THEN src/marker.txt contains exactly done

## Success Criteria

```bash
eval_1() {{
  grep -qx 'done' src/marker.txt
}}
```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: The sandbox marker contains exactly done
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 1
retry_policy:
  max_iterations: 2
  circuit_breaker_no_progress: 1
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails, operations]
  produce: [code]
  required_tools: [git, bash]
  timeout_minutes: 2
  sandbox_type: isolated
  output_artifacts: [src/marker.txt]
  mcp_dependencies: []
  emit: [pass, fail, parked_with_context]
```

## Exit Check

```bash
eval_1
```

## Rollback Plan

Remove src/marker.txt.

## Observability Hooks

The container result and externally signed EnvironmentReceipt/v2 are retained.

## Anti-Patterns

- Never mount repository signing keys, evaluator private keys, a home directory, or the Docker socket.

## Do-Not-Touch

- `.git/info/taskspec-signing-key`

## Open Questions

(none)
''', encoding="utf-8")
PY

git -C "$WORK" add tasks evidence/environment.json
git -C "$WORK" commit -qm "Create portable sandbox fixture"
openssl rand -hex 32 > "$HOST_ONLY/taskspec.hmac"
chmod 600 "$HOST_ONLY/taskspec.hmac"
if ! (
  cd "$WORK"
  TASKSPEC_SIGNING_KEY="$HOST_ONLY/taskspec.hmac" TASKSPEC_BACKLOG_DIR="$WORK/tasks" TASKSPEC_WORKSPACE_ROOT="$WORK" \
    "$TS" gate --stamp tasks/T-20260815-sandbox-proof.md
) >"$HOST_ONLY/gate.log" 2>&1; then
  cat "$HOST_ONLY/gate.log" >&2
  exit 1
fi
git -C "$WORK" add tasks/T-20260815-sandbox-proof.md
git -C "$WORK" commit -qm "Authorize portable sandbox fixture"
(
  cd "$WORK"
  TASKSPEC_SIGNING_KEY="$HOST_ONLY/taskspec.hmac" TASKSPEC_BACKLOG_DIR="$WORK/tasks" TASKSPEC_WORKSPACE_ROOT="$WORK" \
    "$TS" handoff tasks/T-20260815-sandbox-proof.md --backend ref-executor --attempt-id "$ATTEMPT_ID" \
      --out evidence/handoff.json >/dev/null
)

docker build --pull=false --iidfile "$HOST_ONLY/image.id" -t "$IMAGE_TAG" -f "$ROOT/release/docker/Dockerfile" "$ROOT" \
  >"$HOST_ONLY/docker-build.log"
IMAGE_DIGEST="$(cat "$HOST_ONLY/image.id")"
[[ "$IMAGE_DIGEST" == sha256:* ]] || { echo "sandbox image did not resolve to a content digest" >&2; exit 1; }

chmod -R a+rwX "$WORK"
CONTAINER_NAME="taskspec-sandbox-${ATTEMPT_ID%%-*}-$RANDOM"
docker create \
  --name "$CONTAINER_NAME" \
  --network none \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --pids-limit 64 \
  --cpus 1 \
  --memory 256m \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777 \
  --mount "type=bind,src=$WORK,dst=$WORK" \
  --workdir "$WORK" \
  --env HOME=/tmp/home \
  --env TASKSPEC_BACKLOG_DIR="$WORK/tasks" \
  --env TASKSPEC_WORKSPACE_ROOT="$WORK" \
  --env GIT_CONFIG_COUNT=1 \
  --env GIT_CONFIG_KEY_0=safe.directory \
  --env GIT_CONFIG_VALUE_0="$WORK" \
  "$IMAGE_DIGEST" executor "$WORK/tasks/T-20260815-sandbox-proof.md" \
  >"$HOST_ONLY/container.id"
CONTAINER_ID="$(cat "$HOST_ONLY/container.id")"
docker inspect "$CONTAINER_ID" > "$HOST_ONLY/container-inspect.json"

python3 - "$HOST_ONLY/container-inspect.json" "$WORK" "$IMAGE_DIGEST" "$HOST_ONLY/container-security.json" <<'PY'
import json, pathlib, sys
source, workspace, image, output = map(pathlib.Path, (sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
value = json.loads(source.read_text(encoding="utf-8"))[0]
host, config, mounts = value["HostConfig"], value["Config"], value.get("Mounts", [])
failures = []
def require(condition, label):
    if not condition: failures.append(label)
require(host.get("NetworkMode") == "none", "network is not disabled")
require(host.get("ReadonlyRootfs") is True, "root filesystem is not read-only")
require("ALL" in (host.get("CapDrop") or []), "capabilities are not all dropped")
require(any(item.startswith("no-new-privileges") for item in (host.get("SecurityOpt") or [])), "no-new-privileges is absent")
require(host.get("PidsLimit") == 64, "PID limit differs")
require(host.get("NanoCpus") == 1_000_000_000, "CPU limit differs")
require(host.get("Memory") == 256 * 1024 * 1024, "memory limit differs")
require("/tmp" in (host.get("Tmpfs") or {}), "bounded tmpfs is absent")
binds = [item for item in mounts if item.get("Type") == "bind"]
require(len(binds) == 1, "exactly one bind mount is required")
if binds:
    require(pathlib.Path(binds[0].get("Source", "")).resolve() == workspace.resolve(), "bind source is not the attempt workspace")
    require(pathlib.PurePosixPath(binds[0].get("Destination", "")) == pathlib.PurePosixPath(str(workspace)), "bind destination changed")
require(config.get("User") == "65532:65532", "container user is not the unprivileged Task-Spec UID")
require(value.get("Image") == str(image), "container image is not the pinned build digest")
for raw in config.get("Env") or []:
    name = raw.split("=", 1)[0].upper()
    require(not (name.startswith("TASKSPEC_SIGNING") or name.startswith("TASKSPEC_HMAC") or "API_KEY" in name or "TOKEN" in name or "SECRET" in name or "PRIVATE_KEY" in name), f"credential-like environment variable mounted: {name}")
report = {
    "network_none": host.get("NetworkMode") == "none",
    "read_only_root": host.get("ReadonlyRootfs") is True,
    "capabilities_dropped": "ALL" in (host.get("CapDrop") or []),
    "no_new_privileges": any(item.startswith("no-new-privileges") for item in (host.get("SecurityOpt") or [])),
    "one_workspace_bind": len(binds) == 1,
    "docker_socket_mounted": any(item.get("Destination") == "/var/run/docker.sock" for item in mounts),
    "credential_environment_count": sum(1 for raw in (config.get("Env") or []) if any(mark in raw.split("=",1)[0].upper() for mark in ("API_KEY", "TOKEN", "SECRET", "PRIVATE_KEY", "TASKSPEC_SIGNING", "TASKSPEC_HMAC"))),
    "failures": failures,
}
output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
if failures:
    raise SystemExit("; ".join(failures))
PY

python3 - "$CONTAINER_ID" "$HOST_ONLY/container-output.log" <<'PY'
import pathlib, subprocess, sys
completed = subprocess.run(["docker", "start", "-a", sys.argv[1]], text=True, capture_output=True, timeout=120)
pathlib.Path(sys.argv[2]).write_text(completed.stdout + completed.stderr, encoding="utf-8")
raise SystemExit(completed.returncode)
PY
grep -qx done "$WORK/src/marker.txt"
grep -q '^status: parked$' "$WORK/tasks/parked/T-20260815-sandbox-proof.md"

RUNTIME_VERSION="$(docker version --format '{{.Server.Version}}')"
KERNEL_VERSION="$(docker info --format '{{.KernelVersion}}')"
python3 - "$HOST_ONLY/sandbox-artifact.json" "$CONTAINER_ID" "$WORK" "$HOST_ONLY/container-security.json" "$HOST_ONLY/container-output.log" <<'PY'
import hashlib, json, pathlib, subprocess, sys
out, container_id, workspace, security_path, log_path = map(pathlib.Path, sys.argv[1:])
changed = subprocess.run(["git", "-C", str(workspace), "status", "--porcelain"], text=True, capture_output=True, check=True).stdout.splitlines()
value = {
    "contract": "SandboxExecutionArtifact/v1",
    "container_id": str(container_id),
    "reference_executor_exit": 0,
    "marker_digest": "sha256:" + hashlib.sha256((workspace / "src/marker.txt").read_bytes()).hexdigest(),
    "changed_paths": sorted(line[3:] for line in changed if len(line) > 3),
    "security_checks": json.loads(security_path.read_text(encoding="utf-8")),
    "output_digest": "sha256:" + hashlib.sha256(log_path.read_bytes()).hexdigest(),
}
out.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
PY

COMMAND_JSON="$(python3 - "$WORK" <<'PY'
import json, sys
root = sys.argv[1]
print(json.dumps(["/opt/task-spec/bin/taskspec", "executor", root + "/tasks/T-20260815-sandbox-proof.md"]))
PY
)"
python3 "$ATTEST" record \
  --runtime docker --runtime-version "$RUNTIME_VERSION" --kernel "$KERNEL_VERSION" \
  --image-digest "$IMAGE_DIGEST" --network none --writable-mount "$WORK" --writable-mount /tmp \
  --cpus 1 --memory-mb 256 --pids 64 --timeout-sec 120 --tmpfs-mb 16 \
  --command-json "$COMMAND_JSON" --artifact "$HOST_ONLY/sandbox-artifact.json" \
  --out "$HOST_ONLY/environment-attestation.json" >/dev/null

"$TS" identity init --out-dir "$HOST_ONLY/evaluator" >/dev/null
KEY_ID="$(openssl pkey -pubin -in "$HOST_ONLY/evaluator/identity.ed25519.pub.pem" -outform DER | openssl dgst -sha256 | awk '{print substr($2,1,16)}')"
python3 - "$HOST_ONLY/evaluator-trust.json" "$KEY_ID" "$HOST_ONLY/evaluator/identity.ed25519.pub.pem" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
    "contract": "EvaluatorTrust/v1",
    "evaluators": [{"key_id": sys.argv[2], "public_key": sys.argv[3], "receipt_classes": ["EnvironmentReceipt/v2"]}],
}, indent=2) + "\n", encoding="utf-8")
PY
TASK_FILE="$WORK/tasks/parked/T-20260815-sandbox-proof.md"
"$TS" receipt environment --task-id T-20260815-sandbox-proof \
  --contract "$WORK/evidence/environment.json" --provider host-docker-attestor \
  --attestation "$HOST_ONLY/environment-attestation.json" --handoff "$WORK/evidence/handoff.json" \
  --out "$HOST_ONLY/environment-receipt-unsigned.json" >/dev/null
"$TS" receipt sign "$HOST_ONLY/environment-receipt-unsigned.json" \
  --private-key "$HOST_ONLY/evaluator/identity.ed25519.pem" \
  --public-key "$HOST_ONLY/evaluator/identity.ed25519.pub.pem" \
  --out "$HOST_ONLY/environment-receipt.json" >/dev/null
python3 "$ATTEST" verify "$HOST_ONLY/environment-attestation.json" \
  --receipt "$HOST_ONLY/environment-receipt.json" --trust-registry "$HOST_ONLY/evaluator-trust.json" >/dev/null

cp "$HOST_ONLY/environment-attestation.json" "$HOST_ONLY/environment-attestation-tampered.json"
python3 - "$HOST_ONLY/environment-attestation-tampered.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); value = json.loads(path.read_text(encoding="utf-8"))
value["command"][0] += "-tampered"
path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
PY
if python3 "$ATTEST" verify "$HOST_ONLY/environment-attestation-tampered.json" --receipt "$HOST_ONLY/environment-receipt.json" --trust-registry "$HOST_ONLY/evaluator-trust.json" >/dev/null 2>&1; then
  echo "tampered attestation passed verification" >&2; exit 1
fi
cp "$HOST_ONLY/environment-receipt.json" "$HOST_ONLY/environment-receipt-tampered.json"
python3 - "$HOST_ONLY/environment-receipt-tampered.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); value = json.loads(path.read_text(encoding="utf-8"))
value["environment_digest"] = "sha256:" + "0" * 64
path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
PY
if python3 "$ATTEST" verify "$HOST_ONLY/environment-attestation.json" --receipt "$HOST_ONLY/environment-receipt-tampered.json" --trust-registry "$HOST_ONLY/evaluator-trust.json" >/dev/null 2>&1; then
  echo "tampered receipt passed verification" >&2; exit 1
fi

(
  cd "$WORK"
  TASKSPEC_SIGNING_KEY="$HOST_ONLY/taskspec.hmac" TASKSPEC_BACKLOG_DIR="$WORK/tasks" TASKSPEC_WORKSPACE_ROOT="$WORK" \
    "$TS" transition T-20260815-sandbox-proof in-progress >/dev/null
  TASKSPEC_SIGNING_KEY="$HOST_ONLY/taskspec.hmac" TASKSPEC_BACKLOG_DIR="$WORK/tasks" TASKSPEC_WORKSPACE_ROOT="$WORK" \
    "$TS" accept --stamp --accepted-by host-attestor --handoff evidence/handoff.json \
      --environment-receipt "$HOST_ONLY/environment-receipt.json" \
      --trust-registry "$HOST_ONLY/evaluator-trust.json" tasks/T-20260815-sandbox-proof.md >/dev/null
  TASKSPEC_SIGNING_KEY="$HOST_ONLY/taskspec.hmac" TASKSPEC_BACKLOG_DIR="$WORK/tasks" TASKSPEC_WORKSPACE_ROOT="$WORK" \
    "$TS" transition T-20260815-sandbox-proof done >/dev/null
)
ACCEPTANCE_RECORD="$(find "$WORK/.taskspec/acceptance/T-20260815-sandbox-proof" -maxdepth 1 -type f -name '*.json' -print | head -1)"
[[ -n "$ACCEPTANCE_RECORD" ]] || { echo "portable acceptance record missing" >&2; exit 1; }

cp "$HOST_ONLY/environment-attestation.json" "$OUT_DIR/environment-attestation.json"
cp "$HOST_ONLY/environment-receipt.json" "$OUT_DIR/environment-receipt.json"
cp "$HOST_ONLY/evaluator/identity.ed25519.pub.pem" "$OUT_DIR/environment-evaluator.pub.pem"
cp "$HOST_ONLY/sandbox-artifact.json" "$OUT_DIR/sandbox-execution-artifact.json"
cp "$WORK/evidence/handoff.json" "$OUT_DIR/environment-handoff.json"
python3 - "$OUT_DIR/environment-trust.json" "$KEY_ID" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
    "contract": "EvaluatorTrust/v1",
    "evaluators": [{"key_id": sys.argv[2], "public_key": "environment-evaluator.pub.pem", "receipt_classes": ["EnvironmentReceipt/v2"]}],
}, indent=2) + "\n", encoding="utf-8")
PY
python3 "$ATTEST" verify "$OUT_DIR/environment-attestation.json" \
  --receipt "$OUT_DIR/environment-receipt.json" --trust-registry "$OUT_DIR/environment-trust.json" >/dev/null

python3 - "$OUT_DIR/environment-proof.json" "$OUT_DIR/environment-attestation.json" "$OUT_DIR/environment-receipt.json" "$ACCEPTANCE_RECORD" "$HOST_ONLY/container-security.json" "$IMAGE_DIGEST" <<'PY'
import hashlib, json, pathlib, sys
out, attestation, receipt, acceptance, security = map(pathlib.Path, sys.argv[1:6])
digest = lambda path: "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
acceptance_value = json.loads(acceptance.read_text(encoding="utf-8"))
value = {
    "contract": "SandboxReleaseProof/v1",
    "result": "pass",
    "image_digest": sys.argv[6],
    "attestation_digest": digest(attestation),
    "receipt_digest": digest(receipt),
    "acceptance_record_digest": digest(acceptance),
    "accepted_tier": acceptance_value.get("acceptance_tier"),
    "attempt_id": acceptance_value.get("subject", {}).get("attempt_id"),
    "reference_executor": "bundled",
    "security_checks": json.loads(security.read_text(encoding="utf-8")),
    "signing_key_mounted": False,
    "evaluator_private_key_mounted": False,
    "tampered_attestation_rejected": True,
    "tampered_receipt_rejected": True,
    "limitations": [
        "This is one release fixture, not evidence of production reliability.",
        "The host attestor proves observed Docker configuration; it does not make task semantics universally true."
    ],
}
out.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
PY

echo "SANDBOX_ATTESTATION=VERIFIED"
echo "PORTABLE_ACCEPTANCE=TIER1"
echo "TAMPER_TESTS=READY"
