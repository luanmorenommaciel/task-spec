#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI="$ROOT/bin/taskspec"
TMP="$(mktemp -d -t taskspec-mesh-routing-XXXXXX)"
REPO="$TMP/repository"
HELPER="$TMP/taskspec-meshd"
DAEMON_PID=""
cleanup() {
  if [[ -n "$DAEMON_PID" ]]; then kill "$DAEMON_PID" >/dev/null 2>&1 || true; fi
  rm -rf "$TMP"
}
trap cleanup EXIT

git init -q -b main "$REPO"
git -C "$REPO" config user.name taskspec-test
git -C "$REPO" config user.email taskspec@example.invalid
printf '# routing fixture\n' >"$REPO/README.md"
printf 'base\n' >"$REPO/shared.txt"
touch "$REPO/a.txt" "$REPO/b.txt" "$REPO/c.txt" "$REPO/d.txt"
git -C "$REPO" add README.md shared.txt a.txt b.txt c.txt d.txt
git -C "$REPO" commit -qm initial
TARGET_COMMIT="$(git -C "$REPO" rev-parse HEAD)"
(
  cd "$REPO"
  bash "$CLI" init >/dev/null
  bash "$CLI" setup signing >/dev/null
)
mkdir -p "$REPO/tasks"
for row in "alpha:a.txt" "bravo:b.txt" "charlie:c.txt" "delta:d.txt"; do
  slug="${row%%:*}"
  path="${row#*:}"
  task_id="T-20260816-$slug"
  sed -e "s/T-20260603-stamp-then-verify/$task_id/g" -e "s/- README.md/- $path/" \
    "$ROOT/tests/fixtures/T-20260603-stamp-then-verify.md" >"$REPO/tasks/$task_id.md"
  (cd "$REPO" && bash "$CLI" gate --stamp "tasks/$task_id.md" >/dev/null)
done
go build -o "$HELPER" "$ROOT/cmd/taskspec-meshd"

printf '{"order":["not-an-adapter","claude-native","codex-native"]}\n' >"$TMP/advisor.json"
(
  cd "$REPO"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh explain --task T-20260816-alpha --advisor-file "$TMP/advisor.json" >"$TMP/explain.json"
)
python3 - "$TMP/explain.json" <<'PY'
import json, pathlib, sys
decision = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]["decision"]
assert decision["contract"] == "DispatchDecision/v1"
assert decision["selected"] == "claude-native"
assert "not-an-adapter" not in {candidate["adapter"] for candidate in decision["candidates"]}
assert all(candidate["adapter"] != "not-an-adapter" for candidate in decision["candidates"])
PY

(
  cd "$REPO"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh run --task T-20260816-alpha --adapter codex-native >"$TMP/alpha-run.json"
)
python3 - "$TMP/alpha-run.json" "$TMP/alpha.env" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
attempt = value["attempts"][0]
assert attempt["adapter"] == "codex-native"
assert attempt["decision"]["selected"] == "codex-native"
assert attempt["branch"].startswith("taskmesh/")
assert pathlib.Path(attempt["workspace"]).is_dir()
lease = attempt["lease"]
run = value["run"]
pathlib.Path(sys.argv[2]).write_text("\n".join([lease["attempt_id"], str(lease["fencing_token"]), lease["task_id"], lease["task_revision_digest"], attempt["workspace"], run["run_id"], run["integration_branch"], run["target"]["commit"]]) + "\n")
PY

write_record() {
  local attempt="$1" token="$2" task="$3" revision="$4" base="$5" output="$6"
  mkdir -p "$(dirname "$output")"
  python3 - "$attempt" "$task" "$revision" "$base" "$output" <<'PY'
import json, pathlib, sys
attempt, task, revision, base, output = sys.argv[1:]
gate = lambda code: {"status": "pass", "code": code}
record = {
  "contract": "AcceptanceRecord/v1",
  "subject": {"task_id": task, "task_revision_digest": revision,
    "authorization_ref": "hmac-sha256-v3:12345678:" + "a" * 64,
    "attempt_id": attempt, "base_commit": base},
  "outcome": {"status": "accepted", "code": "ACCEPTED_TIER_1"},
  "gate_outcomes": {"authorization": gate("AUTHORIZATION_VALID"), "evaluation": gate("EVAL_PASSED"), "preflight": gate("PREFLIGHT_PASSED"), "evidence": gate("EVIDENCE_SATISFIED")},
  "receipts": [], "acceptance_tier": 1, "accepted_by": "routing-test",
  "accepted_at": "2026-08-16T19:00:00Z"
}
pathlib.Path(output).write_text(json.dumps(record, indent=2) + "\n")
PY
  TASKSPEC_HOME="$ROOT" "$HELPER" --repository "$REPO" --json record-acceptance --attempt-id "$attempt" --fencing-token "$token" --record "$output" >/dev/null
}

ALPHA_ATTEMPT="$(sed -n '1p' "$TMP/alpha.env")"
ALPHA_TOKEN="$(sed -n '2p' "$TMP/alpha.env")"
ALPHA_TASK="$(sed -n '3p' "$TMP/alpha.env")"
ALPHA_REVISION="$(sed -n '4p' "$TMP/alpha.env")"
ALPHA_WORKSPACE="$(sed -n '5p' "$TMP/alpha.env")"
ALPHA_INTEGRATION="$(sed -n '7p' "$TMP/alpha.env")"
ALPHA_BASE="$(sed -n '8p' "$TMP/alpha.env")"
printf 'alpha change\n' >"$ALPHA_WORKSPACE/a.txt"
git -C "$ALPHA_WORKSPACE" add a.txt
git -C "$ALPHA_WORKSPACE" commit -qm alpha
ALPHA_RECORD="$REPO/.taskspec/acceptance/$ALPHA_TASK/$ALPHA_ATTEMPT.json"
write_record "$ALPHA_ATTEMPT" "$ALPHA_TOKEN" "$ALPHA_TASK" "$ALPHA_REVISION" "$ALPHA_BASE" "$ALPHA_RECORD"
TASKSPEC_HOME="$ROOT" "$HELPER" --repository "$REPO" --json integrate --attempt-id "$ALPHA_ATTEMPT" >"$TMP/alpha-integrate.json"
grep -q 'MESH_INTEGRATED' "$TMP/alpha-integrate.json"
[[ "$(git -C "$REPO" rev-parse main)" == "$TARGET_COMMIT" ]]
[[ "$(git -C "$REPO" show "$ALPHA_INTEGRATION:a.txt")" == "alpha change" ]]
[[ -z "$(cat "$REPO/a.txt")" ]]

# Remove alpha from the canonical ready frontier; the task body and authority stay unchanged.
python3 - "$REPO/tasks/T-20260816-alpha.md" <<'PY'
import pathlib, sys
path = pathlib.Path(sys.argv[1])
text = path.read_text().replace("status: ready", "status: done", 1)
path.write_text(text)
PY

# Two write-disjoint authorized tasks are deliberately made to conflict at Git integration.
(
  cd "$REPO"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh run --frontier --max-parallel 2 >"$TMP/wave.json"
)
python3 - "$TMP/wave.json" "$TMP/wave.tsv" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
assert len(value["attempts"]) == 2
rows = []
for attempt in value["attempts"]:
    lease = attempt["lease"]
    rows.append("\t".join([lease["attempt_id"], str(lease["fencing_token"]), lease["task_id"], lease["task_revision_digest"], attempt["workspace"], value["run"]["target"]["commit"]]))
pathlib.Path(sys.argv[2]).write_text("\n".join(rows) + "\n")
PY

index=0
while IFS=$'\t' read -r attempt token task revision workspace base; do
  index=$((index + 1))
  printf 'conflict-%s\n' "$index" >"$workspace/shared.txt"
  git -C "$workspace" add shared.txt
  git -C "$workspace" commit -qm "conflict $index"
  record="$REPO/.taskspec/acceptance/$task/$attempt.json"
  write_record "$attempt" "$token" "$task" "$revision" "$base" "$record"
  if [[ "$index" -eq 1 ]]; then
    TASKSPEC_HOME="$ROOT" "$HELPER" --repository "$REPO" --json integrate --attempt-id "$attempt" >"$TMP/conflict-first.json"
  else
    set +e
    TASKSPEC_HOME="$ROOT" "$HELPER" --repository "$REPO" --json integrate --attempt-id "$attempt" >"$TMP/conflict-second.json"
    conflict_rc=$?
    set -e
    [[ "$conflict_rc" -eq 1 ]]
  fi
done <"$TMP/wave.tsv"
grep -q 'MESH_INTEGRATED' "$TMP/conflict-first.json"
grep -q 'INTEGRATION_CONFLICT' "$TMP/conflict-second.json"
[[ "$(git -C "$REPO" rev-parse main)" == "$TARGET_COMMIT" ]]

# Target divergence fails closed without rebasing or changing the target again.
(
  cd "$REPO"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh run --task T-20260816-delta >"$TMP/delta-run.json"
)
python3 - "$TMP/delta-run.json" "$TMP/delta.env" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]
attempt = value["attempts"][0]
lease = attempt["lease"]
pathlib.Path(sys.argv[2]).write_text("\n".join([lease["attempt_id"], str(lease["fencing_token"]), lease["task_id"], lease["task_revision_digest"], attempt["workspace"], value["run"]["target"]["commit"]]) + "\n")
PY
DELTA_ATTEMPT="$(sed -n '1p' "$TMP/delta.env")"
DELTA_TOKEN="$(sed -n '2p' "$TMP/delta.env")"
DELTA_TASK="$(sed -n '3p' "$TMP/delta.env")"
DELTA_REVISION="$(sed -n '4p' "$TMP/delta.env")"
DELTA_WORKSPACE="$(sed -n '5p' "$TMP/delta.env")"
DELTA_BASE="$(sed -n '6p' "$TMP/delta.env")"
printf 'delta change\n' >"$DELTA_WORKSPACE/d.txt"
git -C "$DELTA_WORKSPACE" add d.txt
git -C "$DELTA_WORKSPACE" commit -qm delta
write_record "$DELTA_ATTEMPT" "$DELTA_TOKEN" "$DELTA_TASK" "$DELTA_REVISION" "$DELTA_BASE" "$REPO/.taskspec/acceptance/$DELTA_TASK/$DELTA_ATTEMPT.json"
printf 'target moved\n' >>"$REPO/README.md"
git -C "$REPO" add README.md
git -C "$REPO" commit -qm 'move target'
MOVED_TARGET="$(git -C "$REPO" rev-parse main)"
set +e
TASKSPEC_HOME="$ROOT" "$HELPER" --repository "$REPO" --json integrate --attempt-id "$DELTA_ATTEMPT" >"$TMP/diverged.json"
diverged_rc=$?
set -e
[[ "$diverged_rc" -eq 1 ]]
grep -q 'TARGET_DIVERGED' "$TMP/diverged.json"
[[ "$(git -C "$REPO" rev-parse main)" == "$MOVED_TARGET" ]]

(
  cd "$REPO"
  TASKSPEC_MESH_HELPER="$HELPER" bash "$CLI" --json mesh doctor >"$TMP/doctor.json"
)
python3 - "$TMP/doctor.json" <<'PY'
import json, pathlib, sys
pid = json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]["daemon_pid"]
pathlib.Path(sys.argv[1] + ".pid").write_text(str(pid))
PY
DAEMON_PID="$(cat "$TMP/doctor.json.pid")"

echo "MESH_ROUTING_INTEGRATION=READY"
