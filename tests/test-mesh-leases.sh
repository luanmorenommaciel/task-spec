#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI="$ROOT/bin/taskspec"
TMP="$(mktemp -d -t taskspec-mesh-leases-XXXXXX)"
REPO="$TMP/repository"
HELPER="$TMP/taskspec-meshd"
DAEMON_PID=""
cleanup() {
  if [[ -n "$DAEMON_PID" ]]; then kill "$DAEMON_PID" >/dev/null 2>&1 || true; fi
  rm -rf "$TMP"
}
trap cleanup EXIT

git init -q "$REPO"
git -C "$REPO" config user.name taskspec-test
git -C "$REPO" config user.email taskspec@example.invalid
printf '# mesh lease fixture\n' >"$REPO/README.md"
touch "$REPO/a.txt" "$REPO/b.txt"
git -C "$REPO" add README.md a.txt b.txt
git -C "$REPO" commit -qm initial
(
  cd "$REPO"
  bash "$CLI" init >/dev/null
  bash "$CLI" setup signing >/dev/null
)

mkdir -p "$REPO/tasks"
for row in "alpha:a.txt" "bravo:b.txt" "charlie:a.txt"; do
  slug="${row%%:*}"
  path="${row#*:}"
  task_id="T-20260816-$slug"
  sed -e "s/T-20260603-stamp-then-verify/$task_id/g" -e "s/- README.md/- $path/" \
    "$ROOT/tests/fixtures/T-20260603-stamp-then-verify.md" >"$REPO/tasks/$task_id.md"
  (cd "$REPO" && bash "$CLI" gate --stamp "tasks/$task_id.md" >/dev/null)
done

go build -o "$HELPER" "$ROOT/mesh/cmd/taskspec-meshd"
(
  cd "$REPO"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh frontier >"$TMP/frontier.json"
)
python3 - "$TMP/frontier.json" <<'PY'
import json, pathlib, sys
frontier = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]["frontier"]
eligible = {task["task_id"] for task in frontier["tasks"] if task["eligible"]}
assert eligible == {"T-20260816-alpha", "T-20260816-bravo", "T-20260816-charlie"}
groups = [set(group) for group in frontier["concurrency_groups"]]
assert any({"T-20260816-alpha", "T-20260816-bravo"}.issubset(group) for group in groups)
assert all(not {"T-20260816-alpha", "T-20260816-charlie"}.issubset(group) for group in groups)
PY

set +e
(
  cd "$REPO"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh run --task T-20260816-alpha --request-id 11111111-1111-4111-8111-111111111111 >"$TMP/run-1.json"
  echo $? >"$TMP/run-1.rc"
) &
one=$!
(
  cd "$REPO"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh run --task T-20260816-alpha --request-id 22222222-2222-4222-8222-222222222222 >"$TMP/run-2.json"
  echo $? >"$TMP/run-2.rc"
) &
two=$!
wait "$one" "$two"
set -e

python3 - "$TMP/run-1.json" "$TMP/run-1.rc" "$TMP/run-2.json" "$TMP/run-2.rc" "$TMP/winner.json" <<'PY'
import json, pathlib, sys
runs = []
for output, rc_path in ((sys.argv[1], sys.argv[2]), (sys.argv[3], sys.argv[4])):
    value = json.loads(pathlib.Path(output).read_text())
    rc = int(pathlib.Path(rc_path).read_text())
    runs.append((value, rc))
assert sorted(rc for _, rc in runs) == [0, 1]
winner = next(value for value, rc in runs if rc == 0)
loser = next(value for value, rc in runs if rc == 1)
assert winner["data"]["code"] == "MESH_RUN_STARTED"
assert loser["data"]["code"] == "LEASE_CONFLICT"
pathlib.Path(sys.argv[5]).write_text(json.dumps(winner))
PY

python3 - "$TMP/winner.json" "$TMP/attempt.env" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
lease = value["data"]["data"]["leases"][0]
run = value["data"]["data"]["run"]
pathlib.Path(sys.argv[2]).write_text(f'{lease["attempt_id"]}\n{lease["fencing_token"]}\n{run["run_id"]}\n')
PY
ATTEMPT="$(sed -n '1p' "$TMP/attempt.env")"
TOKEN="$(sed -n '2p' "$TMP/attempt.env")"
RUN_ID="$(sed -n '3p' "$TMP/attempt.env")"

set +e
TASKSPEC_HOME="$ROOT" "$HELPER" --repository "$REPO" --json submit --attempt-id "$ATTEMPT" --fencing-token "$((TOKEN + 1))" >"$TMP/stale-submit.json"
stale_rc=$?
set -e
[[ "$stale_rc" -eq 1 ]]
python3 - "$TMP/stale-submit.json" <<'PY'
import json, pathlib, sys
assert json.loads(pathlib.Path(sys.argv[1]).read_text())["code"] == "ATTEMPT_STALE"
PY

TASKSPEC_HOME="$ROOT" "$HELPER" --repository "$REPO" --json heartbeat --attempt-id "$ATTEMPT" --fencing-token "$TOKEN" >"$TMP/heartbeat.json"
TASKSPEC_HOME="$ROOT" "$HELPER" --repository "$REPO" --json submit --attempt-id "$ATTEMPT" --fencing-token "$TOKEN" >"$TMP/submit.json"
(
  cd "$REPO"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh cancel "$ATTEMPT" >"$TMP/cancel.json"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh resume "$ATTEMPT" >"$TMP/resume.json"
)
python3 - "$TMP/resume.json" "$TOKEN" "$TMP/resumed.env" <<'PY'
import json, pathlib, sys
lease = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]["lease"]
assert lease["fencing_token"] > int(sys.argv[2])
pathlib.Path(sys.argv[3]).write_text(f'{lease["attempt_id"]}\n{lease["fencing_token"]}\n')
PY
NEW_ATTEMPT="$(sed -n '1p' "$TMP/resumed.env")"
NEW_TOKEN="$(sed -n '2p' "$TMP/resumed.env")"

set +e
TASKSPEC_HOME="$ROOT" "$HELPER" --repository "$REPO" --json submit --attempt-id "$ATTEMPT" --fencing-token "$TOKEN" >"$TMP/late-submit.json"
late_rc=$?
set -e
[[ "$late_rc" -eq 1 ]]
grep -q 'ATTEMPT_STALE' "$TMP/late-submit.json"

# Expiry plus daemon restart reconstructs state and fences the lost attempt.
(
  cd "$REPO"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh run --task T-20260816-bravo --lease-ttl 1 >"$TMP/expiring.json"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh doctor >"$TMP/doctor.json"
)
python3 - "$TMP/expiring.json" "$TMP/doctor.json" "$TMP/expiry.env" <<'PY'
import json, pathlib, sys
lease = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]["leases"][0]
doctor = json.loads(pathlib.Path(sys.argv[2]).read_text())["data"]["data"]
pathlib.Path(sys.argv[3]).write_text(f'{lease["attempt_id"]}\n{lease["fencing_token"]}\n{doctor["daemon_pid"]}\n')
PY
EXPIRED_ATTEMPT="$(sed -n '1p' "$TMP/expiry.env")"
EXPIRED_TOKEN="$(sed -n '2p' "$TMP/expiry.env")"
DAEMON_PID="$(sed -n '3p' "$TMP/expiry.env")"
kill "$DAEMON_PID"
DAEMON_PID=""
sleep 2
(
  cd "$REPO"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh status "$RUN_ID" >"$TMP/recovered-status.json"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh resume "$EXPIRED_ATTEMPT" >"$TMP/recovered-resume.json"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh doctor >"$TMP/final-doctor.json"
)
python3 - "$TMP/recovered-resume.json" "$EXPIRED_TOKEN" "$TMP/final-doctor.json" <<'PY'
import json, pathlib, sys
resume = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]["lease"]
assert resume["fencing_token"] > int(sys.argv[2])
doctor = json.loads(pathlib.Path(sys.argv[3]).read_text())["data"]["data"]
pathlib.Path(sys.argv[3] + ".pid").write_text(str(doctor["daemon_pid"]))
PY
DAEMON_PID="$(cat "$TMP/final-doctor.json.pid")"

set +e
TASKSPEC_HOME="$ROOT" "$HELPER" --repository "$REPO" --json submit --attempt-id "$EXPIRED_ATTEMPT" --fencing-token "$EXPIRED_TOKEN" >"$TMP/expired-submit.json"
expired_rc=$?
set -e
[[ "$expired_rc" -eq 1 ]]
grep -q 'ATTEMPT_STALE' "$TMP/expired-submit.json"

# Keep the resumed alpha lease referenced so shellcheck does not hide identity regressions.
[[ -n "$NEW_ATTEMPT" && "$NEW_TOKEN" -gt "$TOKEN" ]]

echo "MESH_LEASES=READY"
