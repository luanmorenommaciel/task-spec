#!/usr/bin/env bash
# Nested workspace, backlog, and acceptance-store authority for v3.8.1.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TS="$ROOT/bin/taskspec"
FIXTURE="$ROOT/tests/fixtures/T-20260603-stamp-then-verify.md"
WORK="$(mktemp -d -t taskspec-v381-workspace-XXXXXX)"
OUTSIDE="$(mktemp -d -t taskspec-v381-outside-XXXXXX)"
trap 'rm -rf "$WORK" "$OUTSIDE"' EXIT
PASS=0

ok() { PASS=$((PASS + 1)); echo "ok $PASS - $1"; }
must() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then ok "$label"; else
    echo "not ok - $label" >&2
    "$@" >&2 || true
    exit 1
  fi
}
must_fail() {
  local label="$1" pattern="$2"; shift 2
  local output rc
  set +e; output=$("$@" 2>&1); rc=$?; set -e
  if [[ $rc -ne 0 && "$output" == *"$pattern"* ]]; then ok "$label"; else
    echo "not ok - $label (rc=$rc)" >&2
    echo "$output" >&2
    exit 1
  fi
}
repo() {
  local path="$1"
  mkdir -p "$path"
  git -C "$path" init -q
  git -C "$path" config user.email workspace@example.invalid
  git -C "$path" config user.name workspace
  printf '# workspace\n' > "$path/README.md"
  git -C "$path" add README.md
  git -C "$path" commit -qm baseline
}
spec() {
  local repo="$1" backlog="$2" id="$3"
  mkdir -p "$repo/$backlog"
  python3 - "$FIXTURE" "$repo/$backlog/$id.md" "$id" <<'PY'
import pathlib, sys
source, target, task_id = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
text = source.read_text(encoding="utf-8")
text = text.replace("T-20260603-stamp-then-verify", task_id)
text = text.replace("format_version: 2", "format_version: 3\nprofile: lite")
text = text.replace('(none — see references/concepts/signed-off.md "The three tiers")', "(none)")
target.write_text(text, encoding="utf-8")
PY
}

# A nested integration backlog uses the Git root for code paths and a distinct
# acceptance root. No Converge operational-receipt location is implied.
R="$WORK/nested"; repo "$R"; spec "$R" cvg/tasks T-20260815-nested
TASKSPEC_SIGNING_KEY=workspace-key TASKSPEC_BACKLOG_DIR="$R/cvg/tasks" TASKSPEC_WORKSPACE_ROOT="$R" \
  "$TS" gate --stamp "$R/cvg/tasks/T-20260815-nested.md" >/dev/null
git -C "$R" add cvg; git -C "$R" commit -qm authorized
H="$R/.taskspec/handoff.json"
TASKSPEC_SIGNING_KEY=workspace-key TASKSPEC_BACKLOG_DIR="$R/cvg/tasks" TASKSPEC_WORKSPACE_ROOT="$R" \
  "$TS" handoff "$R/cvg/tasks/T-20260815-nested.md" --backend codex \
  --attempt-id 10101010-1010-4010-8010-101010101010 --out "$H" >/dev/null
must "nested handoff binds the Git workspace" python3 - "$H" "$R" <<'PY'
import json, pathlib, sys
value = json.load(open(sys.argv[1]))
root = str(pathlib.Path(sys.argv[2]).resolve())
assert value["workspace"] == root == value["source"]["workspace"]
PY
must "nested acceptance uses the configured contained store" env \
  TASKSPEC_SIGNING_KEY=workspace-key TASKSPEC_BACKLOG_DIR="$R/cvg/tasks" TASKSPEC_WORKSPACE_ROOT="$R" \
  "$TS" accept --stamp --handoff "$H" --acceptance-dir cvg/.taskspec/acceptance \
  "$R/cvg/tasks/T-20260815-nested.md"
must "nested acceptance record is separate from Converge receipts" bash -c \
  "test -f '$R/cvg/.taskspec/acceptance/T-20260815-nested/10101010-1010-4010-8010-101010101010.json' && test ! -e '$R/cvg/receipts'"

# Git authority is inferred consistently even when an adapter omits the
# explicit workspace variable, but a conflicting explicit claim fails closed.
R="$WORK/inferred"; repo "$R"; spec "$R" cvg/tasks T-20260815-inferred
TASKSPEC_SIGNING_KEY=workspace-key TASKSPEC_BACKLOG_DIR="$R/cvg/tasks" \
  "$TS" gate --stamp "$R/cvg/tasks/T-20260815-inferred.md" >/dev/null
git -C "$R" add cvg; git -C "$R" commit -qm authorized
H="$R/handoff.json"
TASKSPEC_SIGNING_KEY=workspace-key TASKSPEC_BACKLOG_DIR="$R/cvg/tasks" \
  "$TS" handoff "$R/cvg/tasks/T-20260815-inferred.md" --backend codex --out "$H" >/dev/null
must "nested backlog infers repository root" python3 - "$H" "$R" <<'PY'
import json, pathlib, sys
assert json.load(open(sys.argv[1]))["workspace"] == str(pathlib.Path(sys.argv[2]).resolve())
PY
must_fail "conflicting explicit workspace is rejected" "must equal the Git repository root" env \
  TASKSPEC_SIGNING_KEY=workspace-key TASKSPEC_BACKLOG_DIR="$R/cvg/tasks" TASKSPEC_WORKSPACE_ROOT="$R/cvg" \
  "$TS" handoff "$R/cvg/tasks/T-20260815-inferred.md" --backend codex

# Acceptance storage is contained, traversal-safe, symlink-safe, and uses
# CLI-over-environment precedence.
R="$WORK/acceptance"; repo "$R"; spec "$R" tasks T-20260815-acceptance
TASKSPEC_SIGNING_KEY=workspace-key TASKSPEC_BACKLOG_DIR="$R/tasks" \
  "$TS" gate --stamp "$R/tasks/T-20260815-acceptance.md" >/dev/null
git -C "$R" add tasks; git -C "$R" commit -qm authorized
H="$R/handoff.json"
TASKSPEC_SIGNING_KEY=workspace-key TASKSPEC_BACKLOG_DIR="$R/tasks" \
  "$TS" handoff "$R/tasks/T-20260815-acceptance.md" --backend codex \
  --attempt-id 20202020-2020-4020-8020-202020202020 --out "$H" >/dev/null
must_fail "acceptance traversal is rejected" "traversal" env \
  TASKSPEC_SIGNING_KEY=workspace-key TASKSPEC_BACKLOG_DIR="$R/tasks" \
  "$TS" accept --stamp --handoff "$H" --acceptance-dir ../escaped "$R/tasks/T-20260815-acceptance.md"
mkdir -p "$R/.taskspec"; ln -s "$OUTSIDE" "$R/.taskspec/escaped-link"
git -C "$R" add .taskspec/escaped-link; git -C "$R" commit -qm symlink-fixture
TASKSPEC_SIGNING_KEY=workspace-key TASKSPEC_BACKLOG_DIR="$R/tasks" \
  "$TS" handoff "$R/tasks/T-20260815-acceptance.md" --backend codex \
  --attempt-id 30303030-3030-4030-8030-303030303030 --out "$H" --force >/dev/null
must_fail "acceptance symlink escape is rejected" "symlink" env \
  TASKSPEC_SIGNING_KEY=workspace-key TASKSPEC_BACKLOG_DIR="$R/tasks" \
  "$TS" accept --stamp --handoff "$H" --acceptance-dir .taskspec/escaped-link "$R/tasks/T-20260815-acceptance.md"
must "CLI acceptance directory overrides an unsafe environment value" env \
  TASKSPEC_SIGNING_KEY=workspace-key TASKSPEC_BACKLOG_DIR="$R/tasks" TASKSPEC_ACCEPTANCE_DIR="$OUTSIDE" \
  "$TS" accept --stamp --handoff "$H" --acceptance-dir .taskspec/acceptance "$R/tasks/T-20260815-acceptance.md"
must "unsafe environment store was never written" bash -c "test -z \"\$(find '$OUTSIDE' -mindepth 1 -print -quit)\""

# Worktrees use Git's common directory for the signing key while each handoff
# remains bound to its own worktree root.
R="$WORK/common-key"; repo "$R"; spec "$R" tasks T-20260815-common-key
git -C "$R" add tasks; git -C "$R" commit -qm task
(cd "$R" && "$ROOT/tools/setup-taskspec-signing-key.sh" >/dev/null)
WT="$WORK/common-key-worktree"
git -C "$R" worktree add -q -b workspace-key-test "$WT"
must "worktree gate resolves the common-directory key" bash -c \
  "cd '$WT' && '$TS' gate --stamp tasks/T-20260815-common-key.md | grep -q 'TIER=1'"

echo "PASS: Task-Spec 3.8.1 nested workspace suite ($PASS checks)"
