#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI="$ROOT/bin/taskspec"
TMP="$(mktemp -d -t taskspec-mesh-daemon-XXXXXX)"
REPO="$TMP/repository"
HELPER="$TMP/taskspec-meshd"
LAST_PID=""
cleanup() {
  if [[ -n "$LAST_PID" ]]; then kill "$LAST_PID" >/dev/null 2>&1 || true; fi
  rm -rf "$TMP"
}
trap cleanup EXIT

git init -q "$REPO"
git -C "$REPO" config user.name taskspec-test
git -C "$REPO" config user.email taskspec@example.invalid
touch "$REPO/README.md"
git -C "$REPO" add README.md
git -C "$REPO" commit -qm initial

go build -o "$HELPER" "$ROOT/mesh/cmd/taskspec-meshd"

(
  cd "$REPO"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh init --request-id 11111111-1111-4111-8111-111111111111 >"$TMP/init-1.json"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh init --request-id 11111111-1111-4111-8111-111111111111 >"$TMP/init-2.json"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh doctor >"$TMP/doctor.json"
)

python3 - "$TMP/init-1.json" "$TMP/init-2.json" "$TMP/doctor.json" <<'PY'
import json, pathlib, stat, sys
first, second, doctor = [json.loads(pathlib.Path(path).read_text()) for path in sys.argv[1:]]
assert first == second
assert first["data"]["code"] == "MESH_INIT_OK"
data = doctor["data"]["data"]
assert data["journal_mode"] == "wal"
assert data["event_count"] == 1
assert stat.S_IMODE(pathlib.Path(data["socket"]).stat().st_mode) == 0o600
assert stat.S_IMODE(pathlib.Path(data["socket"]).parent.stat().st_mode) == 0o700
assert stat.S_IMODE(pathlib.Path(data["database"]).parent.stat().st_mode) == 0o700
pathlib.Path(sys.argv[3] + ".pid").write_text(str(data["daemon_pid"]))
pathlib.Path(sys.argv[3] + ".socket").write_text(data["socket"])
PY

LAST_PID="$(cat "$TMP/doctor.json.pid")"
SOCKET="$(cat "$TMP/doctor.json.socket")"
[[ -z "$(git -C "$REPO" status --porcelain)" ]]
grep -q '^.taskspec/mesh/$' "$REPO/.git/info/exclude"

kill "$LAST_PID"
for _ in 1 2 3 4 5 6 7 8 9 10; do
  [[ ! -S "$SOCKET" ]] && break
  sleep 0.1
done
LAST_PID=""

(
  cd "$REPO"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh status >"$TMP/status.json"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh doctor >"$TMP/doctor-after.json"
)
python3 - "$TMP/status.json" "$TMP/doctor-after.json" <<'PY'
import json, pathlib, sys
status = json.loads(pathlib.Path(sys.argv[1]).read_text())
doctor = json.loads(pathlib.Path(sys.argv[2]).read_text())
view = status["data"]["data"]
assert view["contract"] == "TaskMeshRepositoryView/v1"
assert view["latest_sequence"] == 1
assert len(view["events"]) == 1
assert doctor["data"]["data"]["event_count"] == 1
pathlib.Path(sys.argv[2] + ".pid").write_text(str(doctor["data"]["data"]["daemon_pid"]))
PY
LAST_PID="$(cat "$TMP/doctor-after.json.pid")"

# A second repository resolves to a different hashed socket and durable database.
SECOND="$TMP/second"
git init -q "$SECOND"
git -C "$SECOND" config user.name taskspec-test
git -C "$SECOND" config user.email taskspec@example.invalid
touch "$SECOND/README.md"
git -C "$SECOND" add README.md
git -C "$SECOND" commit -qm initial
(
  cd "$SECOND"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh doctor >"$TMP/second-doctor.json"
)
python3 - "$TMP/doctor-after.json" "$TMP/second-doctor.json" <<'PY'
import json, pathlib, sys
left, right = [json.loads(pathlib.Path(path).read_text())["data"]["data"] for path in sys.argv[1:]]
assert left["repository"] != right["repository"]
assert left["socket"] != right["socket"]
assert left["database"] != right["database"]
pathlib.Path(sys.argv[2] + ".pid").write_text(str(right["daemon_pid"]))
PY
kill "$(cat "$TMP/second-doctor.json.pid")" >/dev/null 2>&1 || true

echo "MESH_DAEMON=READY"
