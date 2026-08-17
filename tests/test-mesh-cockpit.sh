#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI="$ROOT/bin/taskspec"
TMP="$(mktemp -d -t taskspec-mesh-cockpit-XXXXXX)"
REPO="$TMP/repository"
HELPER="$TMP/taskspec-meshd"
ADAPTER_DIR="$TMP/adapters"
FAKE="$TMP/fake-adapter.sh"
DAEMON_PID=""
cleanup() {
  if [[ -n "$DAEMON_PID" ]]; then kill "$DAEMON_PID" >/dev/null 2>&1 || true; fi
  rm -rf "$TMP"
}
trap cleanup EXIT

git init -q -b main "$REPO"
git -C "$REPO" config user.name taskspec-test
git -C "$REPO" config user.email taskspec@example.invalid
printf '# cockpit fixture\n' >"$REPO/README.md"
: >"$REPO/cockpit.txt"
git -C "$REPO" add README.md cockpit.txt
git -C "$REPO" commit -qm initial
(
  cd "$REPO"
  bash "$CLI" init >/dev/null
  bash "$CLI" setup signing >/dev/null
)
mkdir -p "$REPO/tasks"
sed -e 's/T-20260603-stamp-then-verify/T-20260816-cockpit/g' -e 's/README\.md/cockpit.txt/g' \
  "$ROOT/tests/fixtures/T-20260603-stamp-then-verify.md" >"$REPO/tasks/T-20260816-cockpit.md"
(cd "$REPO" && bash "$CLI" gate --stamp tasks/T-20260816-cockpit.md >/dev/null)
git -C "$REPO" add tasks
git -C "$REPO" commit -qm 'authorize cockpit fixture'
TARGET_COMMIT="$(git -C "$REPO" rev-parse main)"

mkdir -p "$ADAPTER_DIR"
cp "$ROOT/tests/fixtures/mesh/fake-adapter.sh" "$FAKE"
chmod +x "$FAKE"
python3 - "$ADAPTER_DIR/fake.json" "$FAKE" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
  "contract": "TaskMeshAdapter/v1", "name": "fake", "harness": "custom",
  "executable": sys.argv[2], "version_args": ["--version"], "command": ["run"],
  "prompt_mode": "argument", "event_format": "jsonl", "assurance_modes": ["supervised"],
}, indent=2) + "\n")
PY
go build -o "$HELPER" "$ROOT/mesh/cmd/taskspec-meshd"

mesh() {
  (
    cd "$REPO"
    TASKSPEC_MESH_HELPER="$HELPER" TASKSPEC_MESH_ADAPTER_DIR="$ADAPTER_DIR" \
    TASKMESH_FAKE_WRITE_PATH=cockpit.txt TASKSPEC_MESH_ADAPTER_TIMEOUT_SEC=60 \
    bash "$CLI" --json mesh "$@"
  )
}

mesh_human() {
  (
    cd "$REPO"
    TASKSPEC_MESH_HELPER="$HELPER" TASKSPEC_MESH_ADAPTER_DIR="$ADAPTER_DIR" \
    TASKMESH_FAKE_WRITE_PATH=cockpit.txt TASKSPEC_MESH_ADAPTER_TIMEOUT_SEC=60 \
    bash "$CLI" mesh "$@"
  )
}

mesh run --task T-20260816-cockpit --adapter fake --execute >"$TMP/run.json"
python3 - "$TMP/run.json" "$TMP/run.env" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
attempt = value["attempts"][0]
pathlib.Path(sys.argv[2]).write_text("\n".join([
    value["run"]["run_id"], attempt["lease"]["attempt_id"], value["run"]["integration_branch"],
]) + "\n")
PY
RUN_ID="$(sed -n '1p' "$TMP/run.env")"
ATTEMPT="$(sed -n '2p' "$TMP/run.env")"
INTEGRATION_BRANCH="$(sed -n '3p' "$TMP/run.env")"

for _ in $(seq 1 80); do
  mesh status "$ATTEMPT" >"$TMP/status.json"
  STATE="$(python3 - "$TMP/status.json" "$ATTEMPT" <<'PY'
import json, pathlib, sys
view = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
print(next(item["state"] for item in view["attempts"] if item["attempt_id"] == sys.argv[2]))
PY
)"
  [[ "$STATE" == "awaiting_supervision" || "$STATE" == "parked" ]] && break
  sleep 0.2
done
[[ "$STATE" == "awaiting_supervision" ]]

# A host adapter cannot accept itself. Identity and reason are mandatory.
set +e
mesh accept "$ATTEMPT" >"$TMP/unsupervised.json"
unsupervised_rc=$?
set -e
[[ "$unsupervised_rc" -eq 1 ]]
grep -q 'MESH_USAGE' "$TMP/unsupervised.json"
mesh status "$ATTEMPT" >"$TMP/still-waiting.json"
grep -q 'awaiting_supervision' "$TMP/still-waiting.json"

# Codex can close after this snapshot; a later process gets the same ordered history.
mesh watch "$RUN_ID" >"$TMP/codex-watch.json"
sleep 0.1
mesh watch "$RUN_ID" >"$TMP/claude-watch.json"
python3 - "$TMP/codex-watch.json" "$TMP/claude-watch.json" <<'PY'
import json, pathlib, sys
def value(path): return json.loads(pathlib.Path(path).read_text())["data"]["data"]
left, right = value(sys.argv[1]), value(sys.argv[2])
assert left == right
sequences = [event["sequence"] for event in left["events"]]
assert sequences == sorted(sequences) and len(sequences) == len(set(sequences))
assert any(event["type"] == "SUPERVISION_REQUIRED" for event in left["events"])
PY
mesh_human watch "$RUN_ID" >"$TMP/human-watch.txt"
grep -q 'SUPERVISION_REQUIRED' "$TMP/human-watch.txt"

# A third cockpit uses the stateless MCP facade. Every mutation still goes through the
# same daemon and canonical Task-Spec acceptance command.
(
  cd "$REPO"
  TASKSPEC_MESH_HELPER="$HELPER" TASKSPEC_MESH_ADAPTER_DIR="$ADAPTER_DIR" \
  TASKMESH_FAKE_WRITE_PATH=cockpit.txt TASKSPEC_MESH_ADAPTER_TIMEOUT_SEC=60 \
  python3 - "$CLI" "$RUN_ID" "$ATTEMPT" "$TMP/mcp-result.json" <<'PY'
import json, os, pathlib, subprocess, sys
cli, run_id, attempt_id, output = sys.argv[1:]
process = subprocess.Popen(["bash", cli, "mesh", "mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
meta = {
  "io.modelcontextprotocol/protocolVersion": "2026-07-28",
  "io.modelcontextprotocol/clientInfo": {"name": "grok-cockpit", "version": "test"},
  "io.modelcontextprotocol/clientCapabilities": {},
}
def call(ident, method, params=None, modern=True):
    params = dict(params or {})
    if modern: params["_meta"] = meta
    request = {"jsonrpc": "2.0", "id": ident, "method": method, "params": params}
    process.stdin.write(json.dumps(request) + "\n"); process.stdin.flush()
    return json.loads(process.stdout.readline())
discover = call(1, "server/discover")
listed = call(2, "tools/list")
names = {tool["name"] for tool in listed["result"]["tools"]}
assert names == {"taskmesh.frontier", "taskmesh.explain_route", "taskmesh.start_run", "taskmesh.get_run", "taskmesh.cancel_attempt", "taskmesh.accept_attempt", "taskmesh.finish_run"}
view = call(3, "tools/call", {"name": "taskmesh.get_run", "arguments": {"id": run_id}})
assert view["result"]["structuredContent"]["code"] == "MESH_STATUS_READY"
assert view["result"]["structuredContent"]["history"]["contract"] == "TaskMeshEventLog/v1"
dry = call(4, "tools/call", {"name": "taskmesh.cancel_attempt", "arguments": {"attempt_id": attempt_id, "dry_run": True}})
assert dry["result"]["structuredContent"]["contract"] == "TaskMeshDryRun/v1"
accepted = call(5, "tools/call", {"name": "taskmesh.accept_attempt", "arguments": {"attempt_id": attempt_id, "supervised_by": "grok-cockpit", "reason": "reviewed the bounded fake-adapter result"}})
assert accepted["result"]["structuredContent"]["code"] == "MESH_SUPERVISED_ACCEPTED"
resources = call(6, "resources/list")
assert any(item["uri"] == "taskmesh://run/" + run_id for item in resources["result"]["resources"])
resource = call(7, "resources/read", {"uri": "taskmesh://attempt/" + attempt_id})
assert resource["result"]["contents"][0]["mimeType"] == "application/json"
finished = call(8, "tools/call", {"name": "taskmesh.finish_run", "arguments": {"run_id": run_id}})
assert finished["result"]["structuredContent"]["code"] == "MESH_FINISHED"
missing = call(9, "tools/list", {}, modern=False)
assert missing["error"]["code"] == -32602
process.stdin.close(); process.wait(timeout=10)
assert process.returncode == 0, process.stderr.read()
pathlib.Path(output).write_text(json.dumps({"discover": discover, "view": view, "accepted": accepted, "finished": finished}, indent=2) + "\n")
PY
)

[[ "$(git -C "$REPO" rev-parse main)" == "$TARGET_COMMIT" ]]
[[ ! -s "$REPO/cockpit.txt" ]]
[[ "$(git -C "$REPO" show "$INTEGRATION_BRANCH:cockpit.txt")" == "completed by $ATTEMPT" ]]
git -C "$REPO" show "$INTEGRATION_BRANCH:tasks/done/T-20260816-cockpit.md" | grep -q 'accepted: true'

mesh status "$RUN_ID" >"$TMP/finished-status.json"
python3 - "$TMP/finished-status.json" <<'PY'
import json, pathlib, sys
view = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
assert view["run"]["state"] == "finished"
assert view["run"]["finished_at"]
assert view["attempts"][-1]["state"] == "integrated"
PY
mesh watch "$RUN_ID" >"$TMP/final-watch.json"
LATEST="$(python3 - "$TMP/final-watch.json" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
assert value["events"][-1]["type"] == "RUN_FINISHED"
print(value["latest_sequence"])
PY
)"
mesh watch "$RUN_ID" --after "$LATEST" >"$TMP/no-new-events.json"
python3 - "$TMP/no-new-events.json" <<'PY'
import json, pathlib, sys
assert json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]["events"] == []
PY
mesh_human finish "$RUN_ID" >"$TMP/finish-human.txt"
grep -q 'target mutated: false' "$TMP/finish-human.txt"
grep -q '^NEXT=git checkout' "$TMP/finish-human.txt"

RECEIPT="$REPO/.taskspec/mesh/artifacts/$ATTEMPT-engine-receipt.json"
grep -q 'not a security sandbox' "$RECEIPT"

mesh doctor >"$TMP/doctor.json"
DAEMON_PID="$(python3 - "$TMP/doctor.json" <<'PY'
import json, pathlib, sys
print(json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]["daemon_pid"])
PY
)"

echo "MESH_COCKPIT=READY"
