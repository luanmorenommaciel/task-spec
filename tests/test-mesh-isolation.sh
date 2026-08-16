#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI="$ROOT/bin/taskspec"
TMP="$(mktemp -d /tmp/taskspec-mesh-isolation-XXXXXX)"
REPO="$TMP/repository"
UNREADY_REPO="$TMP/unready"
EXPIRED_REPO="$TMP/expired"
HELPER="$TMP/taskspec-meshd"
GATEWAY_PID=""
DAEMON_PIDS=""
cleanup() {
  if [[ -n "$GATEWAY_PID" ]]; then kill "$GATEWAY_PID" >/dev/null 2>&1 || true; fi
  for pid in $DAEMON_PIDS; do kill "$pid" >/dev/null 2>&1 || true; done
  rm -rf "$TMP"
}
trap cleanup EXIT

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  [[ "${TASKSPEC_REQUIRE_MESH_ISOLATION:-0}" != "1" ]] || { echo "MESH_ISOLATION=UNAVAILABLE reason=docker" >&2; exit 1; }
  echo "MESH_ISOLATION=UNAVAILABLE reason=docker"
  exit 0
fi

go build -o "$HELPER" "$ROOT/cmd/taskspec-meshd"

prepare_repo() {
  local repository="$1" task_id="$2"
  git init -q -b main "$repository"
  git -C "$repository" config user.name taskspec-test
  git -C "$repository" config user.email taskspec@example.invalid
  printf '# autonomous fixture\n' >"$repository/README.md"
  : >"$repository/autonomous.txt"
  git -C "$repository" add README.md autonomous.txt
  git -C "$repository" commit -qm initial
  (
    cd "$repository"
    bash "$CLI" init >/dev/null
    bash "$CLI" setup signing >/dev/null
  )
  mkdir -p "$repository/tasks"
  sed -e "s/T-20260603-stamp-then-verify/$task_id/g" -e 's/README\.md/autonomous.txt/g' \
    "$ROOT/tests/fixtures/T-20260603-stamp-then-verify.md" >"$repository/tasks/$task_id.md"
  (cd "$repository" && bash "$CLI" gate --stamp "tasks/$task_id.md" >/dev/null)
  git -C "$repository" add tasks
  git -C "$repository" commit -qm 'authorize autonomous fixture'
}

prepare_repo "$REPO" T-20260816-autonomous
prepare_repo "$UNREADY_REPO" T-20260816-unready
prepare_repo "$EXPIRED_REPO" T-20260816-expired

# An autonomous request never falls back to a host worktree when the sandbox is not prepared.
set +e
(
  cd "$UNREADY_REPO"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh run --task T-20260816-unready \
    --mode autonomous --provider test --model fixed-model >"$TMP/unready.json"
)
unready_rc=$?
set -e
[[ "$unready_rc" -eq 1 ]]
grep -q 'SANDBOX_UNAVAILABLE' "$TMP/unready.json"
UNREADY_PID="$(cd "$UNREADY_REPO" && TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh doctor 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["data"]["daemon_pid"])' || true)"
[[ -z "$UNREADY_PID" ]] || DAEMON_PIDS="$DAEMON_PIDS $UNREADY_PID"

# Host-owned evaluator keys live outside both repository and worker.
bash "$CLI" identity init --out-dir "$TMP/attestor" >/dev/null
PRIVATE_KEY="$TMP/attestor/identity.ed25519.pem"
PUBLIC_KEY="$TMP/attestor/identity.ed25519.pub.pem"
KEY_ID="$(openssl pkey -pubin -in "$PUBLIC_KEY" -outform DER | openssl dgst -sha256 | awk '{print substr($2,1,16)}')"
python3 - "$TMP/trust.json" "$KEY_ID" "$PUBLIC_KEY" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
    "contract": "EvaluatorTrust/v1",
    "evaluators": [{"key_id": sys.argv[2], "public_key": sys.argv[3], "receipt_classes": ["EnvironmentReceipt/v2"]}],
}, indent=2) + "\n", encoding="utf-8")
PY

# Fake upstream speaks the OMP auth-gateway paths. The proxy must replace the attempt token
# with this host-only upstream capability and preserve the fixed model.
python3 -u - "$TMP/gateway.port" <<'PY' &
import http.server, json, pathlib, sys
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_): return
    def do_POST(self):
        if self.path != "/v1/pi/stream" or self.headers.get("authorization") != "Bearer upstream-secret-value":
            self.send_response(403); self.end_headers(); return
        value = json.loads(self.rfile.read(int(self.headers.get("content-length", "0"))))
        if value.get("model") != "fixed-model":
            self.send_response(403); self.end_headers(); return
        raw = json.dumps({"ok": True, "model": value["model"]}).encode()
        self.send_response(200); self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw))); self.end_headers(); self.wfile.write(raw)
# Docker Desktop forwards host.docker.internal to the host loopback, while
# Linux Docker resolves host-gateway to the bridge address. Listen on every
# host interface so the same credential-boundary proof reaches the fake
# upstream on both runner families.
server = http.server.ThreadingHTTPServer(("0.0.0.0", 0), Handler)
pathlib.Path(sys.argv[1]).write_text(str(server.server_port), encoding="utf-8")
server.serve_forever()
PY
GATEWAY_PID=$!
for _ in $(seq 1 50); do [[ -s "$TMP/gateway.port" ]] && break; sleep 0.1; done
GATEWAY_PORT="$(cat "$TMP/gateway.port")"

mesh() {
  (
    cd "$REPO"
    TASKSPEC_MESH_HELPER="$HELPER" \
    TASKSPEC_MESH_GATEWAY_URL="http://127.0.0.1:$GATEWAY_PORT" \
    TASKSPEC_MESH_GATEWAY_TOKEN="upstream-secret-value" \
    TASKSPEC_MESH_ATTESTOR_PRIVATE_KEY="$PRIVATE_KEY" \
    TASKSPEC_MESH_ATTESTOR_PUBLIC_KEY="$PUBLIC_KEY" \
    TASKSPEC_MESH_TRUST_REGISTRY="$TMP/trust.json" \
    TASKSPEC_MESH_FAKE_WORKER=1 \
    TASKSPEC_MESH_ADAPTER_TIMEOUT_SEC=120 \
    bash "$CLI" --json mesh "$@"
  )
}

mesh setup sandbox >"$TMP/setup.json"
grep -q 'MESH_SANDBOX_READY' "$TMP/setup.json"
python3 - "$REPO/.taskspec/mesh/sandbox.json" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert value["contract"] == "TaskMeshSandboxSetup/v1"
assert value["verified"] is True
assert value["image_digest"].startswith("sha256:")
assert value["omp_version"] == "17.3.3"
PY

# A changed setup digest invalidates the runtime and does not create an autonomous run.
python3 - "$REPO/.taskspec/mesh/sandbox.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); value = json.loads(path.read_text())
value["lock_digest"] = "sha256:" + "0" * 64
path.write_text(json.dumps(value, indent=2) + "\n")
PY
set +e
mesh run --task T-20260816-autonomous --mode autonomous --provider test --model fixed-model >"$TMP/tampered-lock.json"
tampered_rc=$?
set -e
[[ "$tampered_rc" -eq 1 ]]
grep -q 'SANDBOX_UNAVAILABLE' "$TMP/tampered-lock.json"
mesh setup sandbox >/dev/null

TARGET_COMMIT="$(git -C "$REPO" rev-parse main)"
mesh run --task T-20260816-autonomous --mode autonomous --provider test --model fixed-model --execute >"$TMP/run.json"
python3 - "$TMP/run.json" "$TMP/run.env" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
assert value["run"]["mode"] == "autonomous"
attempt = value["attempts"][0]
assert attempt["adapter"] == "omp-rpc"
assert attempt["decision"]["selected"] == "omp-rpc"
pathlib.Path(sys.argv[2]).write_text(attempt["lease"]["attempt_id"] + "\n" + value["run"]["integration_branch"] + "\n")
PY
ATTEMPT="$(sed -n '1p' "$TMP/run.env")"
INTEGRATION_BRANCH="$(sed -n '2p' "$TMP/run.env")"

FINAL_STATE=""
for _ in $(seq 1 240); do
  mesh status "$ATTEMPT" >"$TMP/status.json"
  FINAL_STATE="$(python3 - "$TMP/status.json" "$ATTEMPT" <<'PY'
import json, pathlib, sys
view = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
print(next(item["state"] for item in view["attempts"] if item["attempt_id"] == sys.argv[2]))
PY
)"
  [[ "$FINAL_STATE" == "integrated" || "$FINAL_STATE" == "parked" || "$FINAL_STATE" == "cancelled" ]] && break
  sleep 0.25
done
if [[ "$FINAL_STATE" != "integrated" ]]; then
  cat "$TMP/status.json" >&2
  cat "$REPO/.taskspec/mesh/daemon.log" >&2 || true
  exit 1
fi

[[ "$(git -C "$REPO" rev-parse main)" == "$TARGET_COMMIT" ]]
[[ ! -s "$REPO/autonomous.txt" ]]
[[ "$(git -C "$REPO" show "$INTEGRATION_BRANCH:autonomous.txt")" == 'completed by autonomous TaskMesh' ]]
git -C "$REPO" show "$INTEGRATION_BRANCH:tasks/done/T-20260816-autonomous.md" | grep -q 'accepted_tier: 1'

ARTIFACTS="$REPO/.taskspec/mesh/artifacts"
ATTESTATION="$ARTIFACTS/$ATTEMPT-environment-attestation.json"
RECEIPT="$ARTIFACTS/$ATTEMPT-environment-receipt.json"
EVIDENCE="$ARTIFACTS/$ATTEMPT-sandbox-evidence.json"
CREDENTIAL="$ARTIFACTS/$ATTEMPT-credential-lease.json"
for path in "$ATTESTATION" "$RECEIPT" "$EVIDENCE" "$CREDENTIAL"; do [[ -f "$path" ]]; done
python3 "$ROOT/src/evidence/environment_attestation.py" verify "$ATTESTATION" --receipt "$RECEIPT" --trust-registry "$TMP/trust.json" >/dev/null
cp "$ATTESTATION" "$TMP/tampered-attestation.json"
python3 - "$TMP/tampered-attestation.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); value = json.loads(path.read_text()); value["command"][0] += "-tampered"
path.write_text(json.dumps(value, indent=2) + "\n")
PY
if python3 "$ROOT/src/evidence/environment_attestation.py" verify "$TMP/tampered-attestation.json" --receipt "$RECEIPT" --trust-registry "$TMP/trust.json" >/dev/null 2>&1; then
  echo "mutated sandbox attestation verified" >&2
  exit 1
fi
python3 - "$ROOT" "$EVIDENCE" "$CREDENTIAL" "$REPO/.taskspec/mesh/mesh.db" "$ATTEMPT" "$RECEIPT" <<'PY'
import importlib.util, json, pathlib, sqlite3, sys
root, evidence, credential, database = map(pathlib.Path, sys.argv[1:5]); attempt = sys.argv[5]
receipt = json.loads(pathlib.Path(sys.argv[6]).read_text()); evidence_value = json.loads(evidence.read_text())
spec = importlib.util.spec_from_file_location("schema_contracts", root / "tests" / "schema_contracts.py")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
module.validate_file(evidence, "sandbox-evidence.schema.json")
module.validate_file(credential, "credential-lease.schema.json")
assert receipt["subject"] == evidence_value["subject"]
row = sqlite3.connect(database).execute("SELECT provider, model, state, scopes_json FROM credential_leases WHERE attempt_id = ?", (attempt,)).fetchone()
assert row[:3] == ("test", "fixed-model", "revoked")
assert "inference.create" in json.loads(row[3])
PY

# Neither upstream nor attempt capability may survive in repository state or retained artifacts.
if grep -R -a -E -l 'upstream-secret-value|TASKMESH_ATTEMPT_TOKEN=' "$REPO/.taskspec/mesh" >/dev/null 2>&1; then
  echo "credential value survived in TaskMesh state" >&2
  exit 1
fi
mesh doctor >"$TMP/doctor.json"
python3 - "$TMP/doctor.json" "$TMP/doctor.env" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
pathlib.Path(sys.argv[2]).write_text(str(value["daemon_pid"]) + "\n" + value["socket"] + "\n")
PY
DAEMON_PID="$(sed -n '1p' "$TMP/doctor.env")"
RUNTIME_DIR="$(dirname "$(sed -n '2p' "$TMP/doctor.env")")"
[[ -z "$(find "$RUNTIME_DIR/credentials" -maxdepth 1 -name "$ATTEMPT.*" -print 2>/dev/null)" ]]
DAEMON_PIDS="$DAEMON_PIDS $DAEMON_PID"

# Expired attempt capabilities are rejected by the proxy and park the attempt; they never
# downgrade to supervised host execution.
mesh_expired() {
  (
    cd "$EXPIRED_REPO"
    TASKSPEC_MESH_HELPER="$HELPER" \
    TASKSPEC_MESH_GATEWAY_URL="http://127.0.0.1:$GATEWAY_PORT" \
    TASKSPEC_MESH_GATEWAY_TOKEN="upstream-secret-value" \
    TASKSPEC_MESH_ATTESTOR_PRIVATE_KEY="$PRIVATE_KEY" \
    TASKSPEC_MESH_ATTESTOR_PUBLIC_KEY="$PUBLIC_KEY" \
    TASKSPEC_MESH_TRUST_REGISTRY="$TMP/trust.json" \
    TASKSPEC_MESH_FAKE_WORKER=1 TASKSPEC_MESH_FAKE_WORKER_DELAY_SEC=2 \
    TASKSPEC_MESH_CREDENTIAL_TTL_SEC=1 TASKSPEC_MESH_ADAPTER_TIMEOUT_SEC=120 \
    bash "$CLI" --json mesh "$@"
  )
}
mesh_expired setup sandbox >/dev/null
mesh_expired run --task T-20260816-expired --mode autonomous --provider test --model fixed-model --execute >"$TMP/expired-run.json"
EXPIRED_ATTEMPT="$(python3 - "$TMP/expired-run.json" <<'PY'
import json, pathlib, sys
print(json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]["attempts"][0]["lease"]["attempt_id"])
PY
)"
for _ in $(seq 1 80); do
  mesh_expired status "$EXPIRED_ATTEMPT" >"$TMP/expired-status.json"
  expired_state="$(python3 - "$TMP/expired-status.json" "$EXPIRED_ATTEMPT" <<'PY'
import json, pathlib, sys
view = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
print(next(item["state"] for item in view["attempts"] if item["attempt_id"] == sys.argv[2]))
PY
)"
  [[ "$expired_state" == "parked" ]] && break
  sleep 0.25
done
[[ "$expired_state" == "parked" ]]
python3 - "$EXPIRED_REPO/.taskspec/mesh/mesh.db" "$EXPIRED_ATTEMPT" <<'PY'
import sqlite3, sys
row = sqlite3.connect(sys.argv[1]).execute("SELECT state FROM credential_leases WHERE attempt_id = ?", (sys.argv[2],)).fetchone()
assert row == ("expired",)
PY
mesh_expired doctor >"$TMP/expired-doctor.json"
EXPIRED_DAEMON_PID="$(python3 - "$TMP/expired-doctor.json" <<'PY'
import json, pathlib, sys
print(json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]["daemon_pid"])
PY
)"
DAEMON_PIDS="$DAEMON_PIDS $EXPIRED_DAEMON_PID"

echo "MESH_ISOLATION=READY"
