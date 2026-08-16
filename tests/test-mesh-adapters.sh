#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI="$ROOT/bin/taskspec"
TMP="$(mktemp -d -t taskspec-mesh-adapters-XXXXXX)"
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
printf '# adapter fixture\n' >"$REPO/README.md"
touch "$REPO/a.txt" "$REPO/b.txt"
git -C "$REPO" add README.md a.txt b.txt
git -C "$REPO" commit -qm initial
(
  cd "$REPO"
  bash "$CLI" init >/dev/null
  bash "$CLI" setup signing >/dev/null
)
mkdir -p "$REPO/tasks"
for row in "alpha:a.txt" "bravo:b.txt"; do
  slug="${row%%:*}"
  path="${row#*:}"
  task_id="T-20260816-$slug"
  sed -e "s/T-20260603-stamp-then-verify/$task_id/g" -e "s/- README.md/- $path/" \
    "$ROOT/tests/fixtures/T-20260603-stamp-then-verify.md" >"$REPO/tasks/$task_id.md"
  (cd "$REPO" && bash "$CLI" gate --stamp "tasks/$task_id.md" >/dev/null)
done
git -C "$REPO" add tasks
git -C "$REPO" commit -qm 'authorize adapter fixtures'
TARGET_COMMIT="$(git -C "$REPO" rev-parse HEAD)"

mkdir -p "$ADAPTER_DIR"
cp "$ROOT/tests/fixtures/mesh/fake-adapter.sh" "$FAKE"
chmod +x "$FAKE"
python3 - "$ADAPTER_DIR" "$FAKE" <<'PY'
import json, pathlib, sys
directory, executable = pathlib.Path(sys.argv[1]), sys.argv[2]
common = {
  "contract": "TaskMeshAdapter/v1", "harness": "custom", "executable": executable,
  "version_args": ["--version"], "prompt_mode": "argument", "event_format": "jsonl",
  "assurance_modes": ["supervised"]
}
for name, command in (("fake", ["run"]), ("slow", ["--sleep"])):
    value = dict(common, name=name, command=command)
    (directory / f"{name}.json").write_text(json.dumps(value, indent=2) + "\n")
PY
go build -o "$HELPER" "$ROOT/cmd/taskspec-meshd"

mesh() {
  (
    cd "$REPO"
    TASKSPEC_MESH_HELPER="$HELPER" \
    TASKSPEC_MESH_ADAPTER_DIR="$ADAPTER_DIR" \
    TASKMESH_FAKE_WRITE_PATH=a.txt \
    TASKMESH_FAKE_SLEEP_SEC=30 \
    TASKSPEC_MESH_ADAPTER_TIMEOUT_SEC=45 \
    bash "$CLI" --json mesh "$@"
  )
}

mesh adapters probe fake >"$TMP/probe.json"
python3 - "$TMP/probe.json" <<'PY'
import json, pathlib, sys
probe = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]["adapters"][0]
assert probe["contract"] == "ExecutorCapability/v1"
assert probe["adapter"] == "fake"
assert probe["available"] is True
assert probe["adapter_version"] == "taskmesh-fake/1.0.0"
PY

# The built-in OMP definition disables extensions, skills, rules, sessions, and the task tool.
python3 - "$ROOT/adapters/mesh/omp-rpc.json" <<'PY'
import json, pathlib, sys
adapter = json.loads(pathlib.Path(sys.argv[1]).read_text())
command = adapter["command"]
for flag in ("--no-session", "--no-extensions", "--no-skills", "--no-rules"):
    assert flag in command
tools = command[command.index("--tools") + 1].split(",")
assert "task" not in tools
PY

mesh run --task T-20260816-alpha --adapter fake --execute >"$TMP/run.json"
python3 - "$TMP/run.json" "$TMP/run.env" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
attempt = value["attempts"][0]
lease = attempt["lease"]
pathlib.Path(sys.argv[2]).write_text("\n".join([lease["attempt_id"], value["run"]["integration_branch"]]) + "\n")
PY
ATTEMPT="$(sed -n '1p' "$TMP/run.env")"
INTEGRATION_BRANCH="$(sed -n '2p' "$TMP/run.env")"

FINAL_STATE=""
for _ in $(seq 1 80); do
  mesh status "$ATTEMPT" >"$TMP/status.json"
  FINAL_STATE="$(python3 - "$TMP/status.json" "$ATTEMPT" <<'PY'
import json, pathlib, sys
view = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
print(next(item["state"] for item in view["attempts"] if item["attempt_id"] == sys.argv[2]))
PY
)"
  [[ "$FINAL_STATE" == "awaiting_supervision" || "$FINAL_STATE" == "parked" || "$FINAL_STATE" == "cancelled" ]] && break
  sleep 0.25
done
[[ "$FINAL_STATE" == "awaiting_supervision" ]]
mesh accept "$ATTEMPT" --supervised-by adapter-test --reason 'reviewed deterministic fake adapter result' >"$TMP/accept.json"
grep -q 'MESH_SUPERVISED_ACCEPTED' "$TMP/accept.json"
mesh status "$ATTEMPT" >"$TMP/accepted-status.json"
FINAL_STATE="$(python3 - "$TMP/accepted-status.json" "$ATTEMPT" <<'PY'
import json, pathlib, sys
view = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
print(next(item["state"] for item in view["attempts"] if item["attempt_id"] == sys.argv[2]))
PY
)"
[[ "$FINAL_STATE" == "integrated" ]]
[[ "$(git -C "$REPO" rev-parse main)" == "$TARGET_COMMIT" ]]
[[ -z "$(cat "$REPO/a.txt")" ]]
[[ "$(git -C "$REPO" show "$INTEGRATION_BRANCH:a.txt")" == "completed by $ATTEMPT" ]]
git -C "$REPO" show "$INTEGRATION_BRANCH:tasks/done/T-20260816-alpha.md" | grep -q 'accepted: true'

RECORD="$REPO/.taskspec/acceptance/T-20260816-alpha/$ATTEMPT.json"
ARTIFACT="$REPO/.taskspec/mesh/artifacts/$ATTEMPT.json"
RECEIPT="$REPO/.taskspec/mesh/artifacts/$ATTEMPT-engine-receipt.json"
[[ -f "$RECORD" && -f "$ARTIFACT" && -f "$RECEIPT" ]]
grep -q '\[REDACTED\]' "$ARTIFACT"
! grep -q 'sk-taskmesh-should-be-redacted' "$ARTIFACT"
python3 - "$RECORD" "$RECEIPT" "$ROOT" <<'PY'
import importlib.util, json, pathlib, sys
record, receipt, root = map(pathlib.Path, sys.argv[1:])
spec = importlib.util.spec_from_file_location("schema_contracts", root / "tests" / "schema_contracts.py")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
module.validate_file(record, "acceptance-record.schema.json")
module.validate_file(receipt, "engine-run-receipt.schema.json")
value = json.loads(receipt.read_text())
assert value["subject"]["attempt_id"] == record.stem
PY

# Cancellation reaches the process group and preserves the cancelled fencing state.
mesh run --task T-20260816-bravo --adapter slow --execute >"$TMP/slow-run.json"
SLOW_ATTEMPT="$(python3 - "$TMP/slow-run.json" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
print(value["attempts"][0]["lease"]["attempt_id"])
PY
)"
for _ in $(seq 1 40); do
  mesh status "$SLOW_ATTEMPT" >"$TMP/slow-status.json"
  state="$(python3 - "$TMP/slow-status.json" "$SLOW_ATTEMPT" <<'PY'
import json, pathlib, sys
view = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
print(next(item["state"] for item in view["attempts"] if item["attempt_id"] == sys.argv[2]))
PY
)"
  [[ "$state" == "running" ]] && break
  sleep 0.1
done
[[ "$state" == "running" ]]
mesh cancel "$SLOW_ATTEMPT" >"$TMP/cancel.json"
sleep 0.5
mesh status "$SLOW_ATTEMPT" >"$TMP/cancelled-status.json"
python3 - "$TMP/cancelled-status.json" "$SLOW_ATTEMPT" <<'PY'
import json, pathlib, sys
view = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
assert next(item["state"] for item in view["attempts"] if item["attempt_id"] == sys.argv[2]) == "cancelled"
PY

mesh doctor >"$TMP/doctor.json"
python3 - "$TMP/doctor.json" <<'PY'
import json, pathlib, sys
pid = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]["daemon_pid"]
pathlib.Path(sys.argv[1] + ".pid").write_text(str(pid))
PY
DAEMON_PID="$(cat "$TMP/doctor.json.pid")"

echo "MESH_ADAPTERS=READY"
