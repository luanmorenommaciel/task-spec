#!/usr/bin/env bash
# Repository configuration (.taskspec/config) selects the backlog directory.
# Precedence: TASKSPEC_BACKLOG_DIR > .taskspec/config backlog_dir > tasks/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TS="$ROOT/bin/taskspec"
FIXTURE="$ROOT/tests/fixtures/T-20260603-stamp-then-verify.md"
WORK="$(mktemp -d -t taskspec-backlog-config-XXXXXX)"
trap 'rm -rf "$WORK"' EXIT
PASS=0

ok() { PASS=$((PASS + 1)); echo "ok $PASS - $1"; }
fail() { echo "not ok - $1" >&2; exit 1; }
# Assert that `cmd ...` succeeds and its output contains `pattern`.
emits() {
  local label="$1" pattern="$2"; shift 2
  local output rc
  set +e; output=$("$@" 2>&1); rc=$?; set -e
  if [[ $rc -eq 0 && "$output" == *"$pattern"* ]]; then ok "$label"; else
    echo "not ok - $label (rc=$rc)" >&2
    echo "$output" >&2
    exit 1
  fi
}
repo() {
  local path="$1"
  mkdir -p "$path"
  git -C "$path" init -q
  git -C "$path" config user.email backlog-config@example.invalid
  git -C "$path" config user.name backlog-config
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
config() { printf '%s\n' "$@" > "$1/.taskspec/config"; }

# ---------------------------------------------------------------------------
# No config: the tasks/ default is unchanged.
# ---------------------------------------------------------------------------
R="$WORK/default"; repo "$R"; spec "$R" tasks T-20260902-default
emits "no config resolves the tasks/ default" "TASK=T-20260902-default" \
  env -u TASKSPEC_BACKLOG_DIR bash -c "cd '$R' && '$TS' status T-20260902-default"

# ---------------------------------------------------------------------------
# backlog_dir selects a backlog outside tasks/ — the issue-26 reproduction.
# ---------------------------------------------------------------------------
R="$WORK/configured"; repo "$R"; spec "$R" custom/tasks T-20260902-configured
mkdir -p "$R/.taskspec"
printf '# Task-Spec repository configuration (no credentials)\nbacklog_dir=custom/tasks\nresearch_provider=none\n' \
  > "$R/.taskspec/config"

emits "backlog_dir resolves status" "TASK=T-20260902-configured" \
  env -u TASKSPEC_BACKLOG_DIR bash -c "cd '$R' && '$TS' status T-20260902-configured"
emits "backlog_dir resolves graph" "T-20260902-configured" \
  env -u TASKSPEC_BACKLOG_DIR bash -c "cd '$R' && '$TS' graph --json"
emits "backlog_dir resolves the readiness board" "custom/tasks" \
  env -u TASKSPEC_BACKLOG_DIR bash -c "cd '$R' && '$TS' setup"
emits "backlog_dir keeps init idempotent" "INIT=OK" \
  env -u TASKSPEC_BACKLOG_DIR bash -c "cd '$R' && '$TS' init"
[[ -d "$R/tasks" ]] && fail "init created tasks/ while backlog_dir names custom/tasks"
ok "init did not create an unconfigured tasks/ directory"

# ---------------------------------------------------------------------------
# Precedence: the environment variable still wins.
# ---------------------------------------------------------------------------
spec "$R" env/tasks T-20260902-fromenv
emits "TASKSPEC_BACKLOG_DIR overrides backlog_dir" "TASK=T-20260902-fromenv" \
  bash -c "cd '$R' && TASKSPEC_BACKLOG_DIR=env/tasks '$TS' status T-20260902-fromenv"

# ---------------------------------------------------------------------------
# Parsing: comments ignored, whitespace and quotes trimmed, absolute honored.
# ---------------------------------------------------------------------------
R="$WORK/parsing"; repo "$R"; spec "$R" quoted/tasks T-20260902-parsing
mkdir -p "$R/.taskspec"
printf '# backlog_dir=commented/out\nbacklog_dir=  "quoted/tasks"  \n' > "$R/.taskspec/config"
emits "commented keys ignored; quotes and padding trimmed" "TASK=T-20260902-parsing" \
  env -u TASKSPEC_BACKLOG_DIR bash -c "cd '$R' && '$TS' status T-20260902-parsing"

# backlog_dir is exported verbatim, so it means exactly what the same value in
# TASKSPEC_BACKLOG_DIR means: relative stays relative to the invocation
# directory, and only an absolute value is independent of it.
mkdir -p "$R/deep/nested"
printf 'backlog_dir=%s\n' "$R/quoted/tasks" > "$R/.taskspec/config"
emits "an absolute backlog_dir is honored" "TASK=T-20260902-parsing" \
  env -u TASKSPEC_BACKLOG_DIR bash -c "cd '$R' && '$TS' status T-20260902-parsing"
emits "an absolute backlog_dir resolves from a subdirectory" "TASK=T-20260902-parsing" \
  env -u TASKSPEC_BACKLOG_DIR bash -c "cd '$R/deep/nested' && '$TS' status T-20260902-parsing"

# ---------------------------------------------------------------------------
# The config file is parsed as text, never sourced.
# ---------------------------------------------------------------------------
SENTINEL="$WORK/sourced-not-parsed"
printf 'backlog_dir=$(touch %s)\n' "$SENTINEL" > "$R/.taskspec/config"
env -u TASKSPEC_BACKLOG_DIR bash -c "cd '$R' && '$TS' status T-20260902-parsing" >/dev/null 2>&1 || true
[[ -e "$SENTINEL" ]] && fail ".taskspec/config was sourced instead of parsed"
ok ".taskspec/config is parsed as text, never sourced"

echo "Results: $PASS passed, 0 failed"
