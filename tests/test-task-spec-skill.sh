#!/usr/bin/env bash
# test-task-spec-skill.sh — Self-test suite for the task-spec skill
#
# Exercises the skill's toolchain end-to-end in an isolated temp directory:
#   1. generate-task-spec.sh   → create a dummy task
#   2. fill stubs              → produce a valid Task-Spec v2
#   3. validate-task-spec.sh   → expect PASS
#   4. controlled error        → expect FAIL with specific message
#   5. transition-status.sh    → ready → in-progress → done
#   6. verify file moves       → tasks/ → tasks/done/
#   7. rebuild-state.sh        → confirm _state.yaml reflects the task
#   8. list-ready.sh           → confirm done task excluded
#   9. archive.sh              → confirm no-op for already-archived
#  10. backup-backlog.sh       → confirm archive created
#
# Safe to run anytime. Does NOT write to the real tasks/ backlog.

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration (engine repo layout: scripts live under src/<verb>/)
# ---------------------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_AUTHOR="$REPO_ROOT/src/author"
SRC_GATE="$REPO_ROOT/src/gate"
SRC_BACKLOG="$REPO_ROOT/src/backlog"
SRC_ACCEPT="$REPO_ROOT/src/accept"
FIXTURES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/fixtures" && pwd)"
PASS=0
FAIL=0

# --- Flag parsing (v2.1 — adds --suite) ---
SUITE="default"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --suite=*)
      SUITE="${1#*=}"
      shift
      ;;
    --suite)
      SUITE="${2:-default}"
      shift 2
      ;;
    --help|-h)
      sed -n '2,16p' "$0"
      echo ""
      echo "Suites:"
      echo "  default          E2E walkthrough (generate → validate → transition → ...)"
      echo "  fixtures         Inverted-grep-c + structural sign-off envelope oracle (WS5)"
      echo "  hmac             Keyed B2 HMAC sign-off envelope suite (Tier 1/2/3, v2.2)"
      echo "  bash-portability bash-3.2 version-guard checks for the aux/core scripts"
      echo "  conformance      Reference conformance driver (run_conformance.sh, self adapter)"
      echo "  all              Run all (default + fixtures + hmac + bash-portability)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

pass() {
  echo "  ✓ $1"
  PASS=$((PASS + 1))
}

fail() {
  echo "  ✗ $1" >&2
  FAIL=$((FAIL + 1))
}

# ---------------------------------------------------------------------------
# --suite fixtures  →  oracle-driven inverted-grep + sign-off envelope assertions
# ---------------------------------------------------------------------------
run_fixtures_suite() {
  local oracle="$FIXTURES_DIR/oracle.json"
  if [[ ! -f "$oracle" ]]; then
    echo "✗ oracle.json not found at $oracle" >&2
    return 1
  fi
  echo "Suite: fixtures — running validate-task-spec.sh against $FIXTURES_DIR/*.md per oracle.json"

  # Parse oracle entries (use python3 for JSON; it ships with macOS and every Linux).
  while IFS=$'\t' read -r fixture expected_exit expected_match description; do
    [[ -z "$fixture" ]] && continue
    local fpath="$FIXTURES_DIR/$fixture"
    if [[ ! -f "$fpath" ]]; then
      fail "fixture missing: $fixture"
      continue
    fi
    set +e
    out=$(bash "$SRC_GATE/validate-task-spec.sh" --skip-touches-paths --skip-id-filename "$fpath" 2>&1)
    rc=$?
    set -e
    if [[ "$rc" != "$expected_exit" ]]; then
      fail "$fixture: expected exit $expected_exit, got $rc — $description"
      continue
    fi
    if [[ -n "$expected_match" ]] && ! echo "$out" | grep -qF "$expected_match"; then
      fail "$fixture: exit $rc OK but missing '$expected_match' in output — $description"
      continue
    fi
    pass "$fixture (exit $rc, matched '$expected_match')"
  done < <(python3 -c "
import json, sys
o = json.load(open('$oracle'))
for f in o['fixtures']:
    print(f'{f[\"fixture\"]}\t{f[\"expected_exit\"]}\t{f[\"expected_match\"]}\t{f[\"description\"]}')
")
}

# ---------------------------------------------------------------------------
# --suite bash-portability  →  delegate to test-bash-portability.sh
# ---------------------------------------------------------------------------
run_bash_portability_suite() {
  local portability_test
  portability_test="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/test-bash-portability.sh"
  if [[ ! -f "$portability_test" ]]; then
    fail "test-bash-portability.sh not found at $portability_test"
    return 1
  fi
  echo "Suite: bash-portability — delegating to test-bash-portability.sh"
  if bash "$portability_test"; then
    pass "bash-portability suite passed"
  else
    fail "bash-portability suite reported failures"
  fi
}

# ---------------------------------------------------------------------------
# --suite hmac  →  delegate to test-hmac-envelope.sh (keyed B2 suite)
# ---------------------------------------------------------------------------
run_hmac_suite() {
  local hmac_test
  hmac_test="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/test-hmac-envelope.sh"
  if [[ ! -f "$hmac_test" ]]; then
    fail "test-hmac-envelope.sh not found at $hmac_test"
    return 1
  fi
  echo "Suite: hmac — delegating to test-hmac-envelope.sh (keyed B2 envelope)"
  if env -u TASKSPEC_SIGNING_KEY bash "$hmac_test"; then
    pass "hmac suite passed"
  else
    fail "hmac suite reported failures"
  fi
}

# ---------------------------------------------------------------------------
# --suite conformance  →  run the reference conformance driver (self adapter)
# ---------------------------------------------------------------------------
run_conformance_suite() {
  local driver
  driver="$REPO_ROOT/spec/conformance/run_conformance.sh"
  if [[ ! -f "$driver" ]]; then
    fail "run_conformance.sh not found at $driver"
    return 1
  fi
  echo "Suite: conformance — delegating to run_conformance.sh (self adapter)"
  set +e
  bash "$driver" --adapter "$(dirname "$driver")/adapters/self.sh"
  local rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    pass "conformance suite passed (0 non-waived failures)"
  else
    fail "conformance suite reported $rc non-waived failure(s)"
  fi
}

# Dispatch on --suite
case "$SUITE" in
  fixtures)
    run_fixtures_suite
    echo ""
    echo "========================================"
    printf "Results: %d passed, %d failed\n" "$PASS" "$FAIL"
    echo "========================================"
    [[ $FAIL -gt 0 ]] && exit 1
    exit 0
    ;;
  hmac)
    run_hmac_suite
    echo ""
    echo "========================================"
    printf "Results: %d passed, %d failed\n" "$PASS" "$FAIL"
    echo "========================================"
    [[ $FAIL -gt 0 ]] && exit 1
    exit 0
    ;;
  bash-portability)
    run_bash_portability_suite
    echo ""
    echo "========================================"
    printf "Results: %d passed, %d failed\n" "$PASS" "$FAIL"
    echo "========================================"
    [[ $FAIL -gt 0 ]] && exit 1
    exit 0
    ;;
  conformance)
    run_conformance_suite
    echo ""
    echo "========================================"
    printf "Results: %d passed, %d failed\n" "$PASS" "$FAIL"
    echo "========================================"
    [[ $FAIL -gt 0 ]] && exit 1
    exit 0
    ;;
  all)
    run_fixtures_suite
    echo ""
    run_hmac_suite
    echo ""
    run_bash_portability_suite
    echo ""
    # fall through to default body below
    ;;
  default)
    # fall through to default body below
    ;;
  *)
    echo "Unknown suite: $SUITE (use default|fixtures|hmac|bash-portability|conformance|all)" >&2
    exit 1
    ;;
esac

# ---------------------------------------------------------------------------
# Isolated workspace
# ---------------------------------------------------------------------------
TMPDIR=$(mktemp -d -t task-spec-test-XXXXXX)
export TMPDIR
trap 'rm -rf "$TMPDIR"' EXIT

cd "$TMPDIR"
git init --quiet

# Dummy file for touches_paths validation
mkdir -p tasks
touch tasks/dummy.txt

# ---------------------------------------------------------------------------
# 1. generate-task-spec.sh
# ---------------------------------------------------------------------------
echo "=== 1. generate-task-spec.sh ==="
gen_out=$(bash "$SRC_AUTHOR/generate-task-spec.sh" test-self-test-suite S any "self-test" 2>&1)
TARGET=$(echo "$gen_out" | grep '^Spec written: ' | sed 's/^Spec written: //')
ID=$(basename "$TARGET" .md)

if [[ -f "$TARGET" ]]; then
  pass "generator created $TARGET"
else
  fail "generator did not create expected file (output: $gen_out)"
  exit 1
fi

FILE_ID=$(grep '^id:' "$TARGET" | head -1 | awk '{print $2}')
if [[ "$FILE_ID" == "$ID" ]]; then
  pass "id in frontmatter matches filename"
else
  fail "id mismatch: file=$FILE_ID, filename=$ID"
fi

# ---------------------------------------------------------------------------
# 2. Fill generated file with valid v2 content
# ---------------------------------------------------------------------------
echo "=== 2. Fill generated file with valid v2 content ==="
sed "s/__ID__/$ID/g" > "$TARGET" <<'TASKSPEC'
---
id: __ID__
title: Dummy self-test task
status: ready
format_version: 2
effort: S
budget_iterations: 15
agent: any
depends_on: []
touches_paths:
  - tasks/dummy.txt
source_note: self-test
created: 2026-05-27T00:00:00Z
tags: []
---

# Dummy self-test task

> **Why:** This is a dummy task for self-testing the task-spec skill.

---

## Goal

Verify the task-spec skill toolchain works end-to-end.

---

## Context

Minimal context for testing.

---

## Success Criteria

```bash
# eval-1: work product reaches the authorized value
eval_1() {
  grep -qx 'complete' tasks/dummy.txt
}

# eval-2: dummy passes
eval_2() {
  echo "PASS: dummy eval 2"
}

# eval-3: dummy passes
eval_3() {
  echo "PASS: dummy eval 3"
}
```

---

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: dummy work product is complete
    runnable: bash
    terminal: true
    expected_duration_sec: 10
  - id: eval_2
    description: dummy passes
    runnable: bash
    terminal: true
    expected_duration_sec: 10
  - id: eval_3
    description: dummy passes
    runnable: bash
    terminal: true
    expected_duration_sec: 10

retry_policy:
  max_iterations: 15
  circuit_breaker_no_progress: 3
  on_terminal_failure: park_with_context

agent_contract:
  version: 2
  read: [intent, contract, guardrails, operations]
  produce:
    - tests
  required_tools: [git, bash]
  timeout_minutes: 30
  sandbox_type: host
  output_artifacts: []
  mcp_dependencies: []
  emit:
    - pass
    - fail
    - retry_with_reason
    - parked_with_context
  backend_metadata: {}
```

---

## Exit Check

```bash
eval_1 && eval_2 && eval_3
```

---

## Rollback Plan

(none — this task is append-only)

---

## Observability Hooks

(none — no runtime observability required)

---

## Anti-Patterns

- Don't skip cleanup — tests must clean up after themselves.

---

## Do-Not-Touch

(none)

---

## Open Questions

(none — this task is fully specified)
TASKSPEC

pass "wrote valid v2 task spec"

# ---------------------------------------------------------------------------
# 3. validate-task-spec.sh — expect PASS
# ---------------------------------------------------------------------------
echo "=== 3. validate-task-spec.sh (expect PASS) ==="
val_out=$(bash "$SRC_GATE/validate-task-spec.sh" "$TARGET" 2>&1) && val_rc=0 || val_rc=$?
if [[ $val_rc -eq 0 ]] && echo "$val_out" | grep -q "OK:"; then
  pass "validator passes on valid task"
else
  fail "validator did not pass on valid task (rc=$val_rc, out=$val_out)"
fi

# ---------------------------------------------------------------------------
# 4. Controlled error — expect FAIL
# ---------------------------------------------------------------------------
echo "=== 4. validate-task-spec.sh with controlled error (expect FAIL) ==="
echo "{{TODO: this should fail}}" >> "$TARGET"
val_out=$(bash "$SRC_GATE/validate-task-spec.sh" "$TARGET" 2>&1) && val_rc=0 || val_rc=$?
if [[ $val_rc -ne 0 ]] && echo "$val_out" | grep -qi "placeholder"; then
  pass "validator catches placeholder regression"
else
  fail "validator did not catch placeholder (rc=$val_rc, out=$val_out)"
fi
# Restore valid file (portable sed — no -i flag)
sed '/{{TODO: this should fail}}/d' "$TARGET" > "${TARGET}.tmp" && mv "${TARGET}.tmp" "$TARGET"

# Authorize while the assertion still fails on the pre-work baseline.
gate_out=$(bash "$SRC_GATE/safe-to-delegate.sh" --stamp "$TARGET" 2>&1) && gate_rc=0 || gate_rc=$?
if [[ $gate_rc -eq 0 ]] && echo "$gate_out" | grep -q 'DELEGATE'; then
  pass "pre-gate authorizes the unbuilt task"
else
  fail "pre-gate did not authorize the task (rc=$gate_rc)"
fi

# ---------------------------------------------------------------------------
# 5. transition-status.sh — ready → in-progress
# ---------------------------------------------------------------------------
echo "=== 5. transition-status.sh: ready → in-progress ==="
bash "$SRC_BACKLOG/transition-status.sh" "$ID" in-progress "self-test" >/dev/null 2>&1 && trans_rc=0 || trans_rc=$?
if [[ $trans_rc -eq 0 ]]; then
  pass "transition to in-progress succeeds"
else
  fail "transition to in-progress failed (rc=$trans_rc)"
fi

if grep -q "^status: in-progress" "$TARGET"; then
  pass "status updated to in-progress"
else
  fail "status not updated to in-progress"
fi

if [[ -f "tasks/${ID}.md" ]]; then
  pass "file remains in tasks/ for active status"
else
  fail "file missing from tasks/ after transition to in-progress"
fi

# A task cannot settle merely because an executor claims success.
bash "$SRC_BACKLOG/transition-status.sh" "$ID" done "premature" >/dev/null 2>&1 && premature_rc=0 || premature_rc=$?
if [[ $premature_rc -ne 0 ]]; then
  pass "transition to done is blocked before acceptance"
else
  fail "transition to done bypassed acceptance"
fi

# Produce the declared work, then independently accept it.
printf 'complete\n' > tasks/dummy.txt
accept_out=$(bash "$SRC_ACCEPT/accept-task.sh" --stamp --no-blast-radius --allow-tier2 --supervised-by self-test --reason "legacy fixture has no handoff" --accepted-by self-test "$TARGET" 2>&1) && accept_rc=0 || accept_rc=$?
if [[ $accept_rc -eq 0 ]] && echo "$accept_out" | grep -q 'ACCEPTED=1'; then
  pass "post-gate accepts and stamps the completed task"
else
  fail "post-gate did not accept completed work (rc=$accept_rc)"
fi

# ---------------------------------------------------------------------------
# 6. transition-status.sh — in-progress → done
# ---------------------------------------------------------------------------
echo "=== 6. transition-status.sh: in-progress → done ==="
bash "$SRC_BACKLOG/transition-status.sh" "$ID" done "self-test" >/dev/null 2>&1 && trans_rc=0 || trans_rc=$?
if [[ $trans_rc -eq 0 ]]; then
  pass "transition to done succeeds"
else
  fail "transition to done failed (rc=$trans_rc)"
fi

if [[ -f "tasks/done/${ID}.md" ]]; then
  pass "file moved to tasks/done/"
else
  fail "file not moved to tasks/done/"
fi

if [[ ! -f "tasks/${ID}.md" ]]; then
  pass "file no longer in tasks/"
else
  fail "file still in tasks/ after done transition"
fi

# ---------------------------------------------------------------------------
# 7. rebuild-state.sh
# ---------------------------------------------------------------------------
echo "=== 7. rebuild-state.sh ==="
bash "$SRC_BACKLOG/rebuild-state.sh" >/dev/null 2>&1 && rebuild_rc=0 || rebuild_rc=$?
if [[ $rebuild_rc -eq 0 ]]; then
  pass "rebuild-state succeeds"
else
  fail "rebuild-state failed (rc=$rebuild_rc)"
fi

if [[ -f "tasks/_state.yaml" ]]; then
  pass "_state.yaml created"
else
  fail "_state.yaml not created"
fi

if grep -q "id: ${ID}" "tasks/_state.yaml"; then
  pass "_state.yaml contains test task"
else
  fail "_state.yaml missing test task"
fi

if grep -A5 "id: ${ID}" "tasks/_state.yaml" | grep -q "status: done"; then
  pass "_state.yaml reflects done status"
else
  fail "_state.yaml does not reflect done status"
fi
cp tasks/_state.yaml "$TMPDIR/state-first.yaml"
if bash "$SRC_BACKLOG/rebuild-state.sh" >/dev/null 2>&1 && cmp -s "$TMPDIR/state-first.yaml" tasks/_state.yaml; then
  pass "rebuild-state is byte-deterministic"
else
  fail "rebuild-state changed bytes without canonical task changes"
fi

# ---------------------------------------------------------------------------
# 8. list-ready.sh
# ---------------------------------------------------------------------------
echo "=== 8. list-ready.sh ==="
list_out=$(bash "$SRC_BACKLOG/list-ready.sh" 2>&1 || true)
if ! echo "$list_out" | grep -q "$ID"; then
  pass "list-ready excludes done task"
else
  fail "list-ready incorrectly shows done task"
fi

# ---------------------------------------------------------------------------
# 9. archive.sh
# ---------------------------------------------------------------------------
echo "=== 9. archive.sh ==="
archive_out=$(bash "$SRC_BACKLOG/archive.sh" 2>&1 || true)
if echo "$archive_out" | grep -q "Archived: 0 done"; then
  pass "archive is no-op for already-archived task"
else
  fail "archive did not report 0 done moves"
fi

# ---------------------------------------------------------------------------
# 10. backup-backlog.sh
# ---------------------------------------------------------------------------
echo "=== 10. backup-backlog.sh ==="
bash "$SRC_BACKLOG/backup-backlog.sh" "$TMPDIR/backups" >/dev/null 2>&1 && backup_rc=0 || backup_rc=$?
if [[ $backup_rc -eq 0 ]]; then
  pass "backup-backlog succeeds"
else
  fail "backup-backlog failed (rc=$backup_rc)"
fi

found_backup=$(find "$TMPDIR/backups" -name "backlog-*.tar.gz" | head -1)
if [[ -n "$found_backup" ]]; then
  pass "backup archive created"
else
  fail "backup archive not created"
fi

echo "=== 11. safe-to-delegate.sh (pre-delegation gate) ==="
# $TARGET was moved to tasks/done/ in step 6, so generate a fresh fixture here.
# A valid (well-formed, unbuilt) spec should get VERDICT: DELEGATE (exit 0).
# A spec with a broken eval body should get DO NOT DELEGATE (exit non-zero).
gate_ok="tasks/T-20990910-gate-ok.md"
sed 's/^id:.*/id: T-20990910-gate-ok/' "tasks/done/${ID}.md" > "$gate_ok" 2>/dev/null \
  || sed 's/^id:.*/id: T-20990910-gate-ok/' "$TARGET" > "$gate_ok" 2>/dev/null
bash -c "source '$REPO_ROOT/src/lib/_lib.sh'; \
  ts_set_frontmatter_field '$gate_ok' status ready; \
  ts_set_frontmatter_field '$gate_ok' signed_off false; \
  ts_set_frontmatter_field '$gate_ok' accepted false; \
  ts_set_frontmatter_field '$gate_ok' accepted_by '(none)'; \
  ts_set_frontmatter_field '$gate_ok' accepted_at '(none)'"
printf 'incomplete\n' > tasks/dummy.txt

sd_out=$(bash "$SRC_GATE/safe-to-delegate.sh" "$gate_ok" 2>&1) && sd_rc=0 || sd_rc=$?
if [[ $sd_rc -eq 0 ]] && echo "$sd_out" | grep -q "DELEGATE"; then
  pass "safe-to-delegate clears a valid spec"
else
  fail "safe-to-delegate blocked a valid spec (rc=$sd_rc)"
fi

gate_broken="tasks/T-20990911-gate-broken.md"
awk '/grep -qx.*complete/ { print "  if [ -z \"$x\" ; then return 1 fi"; next } { print }' \
  "$gate_ok" > "$gate_broken"
bash "$SRC_GATE/safe-to-delegate.sh" "$gate_broken" >/dev/null 2>&1 && sdb_rc=0 || sdb_rc=$?
if [[ $sdb_rc -ne 0 ]]; then
  pass "safe-to-delegate blocks a broken-eval spec"
else
  fail "safe-to-delegate failed to block a broken-eval spec"
fi
rm -f "$gate_ok" "$gate_broken"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "========================================"
printf "Results: %d passed, %d failed\n" "$PASS" "$FAIL"
echo "========================================"

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
