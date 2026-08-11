#!/usr/bin/env bash
# Six-tier effort contract: leaves are runnable; XL/XXL are composition nodes.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VALIDATE="$ROOT/src/gate/validate-task-spec.sh"
TOTAL=0
FAILED=0

pass() { printf 'ok    %-28s\n' "$1"; }
fail() { printf 'FAIL  %-28s %s\n' "$1" "$2" >&2; FAILED=$((FAILED + 1)); }

mkspec() {
  local file="$1" effort="$2" touches="$3" creates="$4" children="$5" backend="$6"
  local slug path child
  slug="$(printf '%s' "$effort" | tr '[:upper:]' '[:lower:]' | tr -cd '[:lower:]')"
  [ -n "$slug" ] || slug="unknown"
  {
    printf '%s\n' '---'
    printf 'id: T-20260811-size-%s\n' "$slug"
    printf 'title: Size fixture %s\n' "$effort"
    printf 'status: ready\nformat_version: 3\nprofile: lite\n'
    printf 'effort: %s\nbudget_iterations: 8\nagent: any\ndepends_on: []\n' "$effort"
    if [ -n "$touches" ]; then
      printf 'touches_paths:\n'
      old_ifs="$IFS"; IFS=','
      for path in $touches; do printf '  - %s\n' "$path"; done
      IFS="$old_ifs"
    else
      printf 'touches_paths: []\n'
    fi
    if [ -n "$creates" ]; then
      printf 'creates_paths:\n'
      old_ifs="$IFS"; IFS=','
      for path in $creates; do printf '  - %s\n' "$path"; done
      IFS="$old_ifs"
    else
      printf 'creates_paths: []\n'
    fi
    if [ -n "$children" ]; then
      printf 'children:\n'
      old_ifs="$IFS"; IFS=','
      for child in $children; do printf '  - %s\n' "$child"; done
      IFS="$old_ifs"
    fi
    printf 'source_note: sizing test\ncreated: 2026-08-11T00:00:00Z\n'
    printf 'execution_backend: %s\nsigned_off: false\nsigned_off_by: (none)\nsigned_off_at: (none)\n' "$backend"
    printf '%s\n' '---' '' '# Size fixture' '' '## Goal' 'Prove the sizing rule.' '' '## Success Criteria' '```bash' 'eval_1() { true; }' '```' '' '## Validation Card' '```yaml' 'success_criteria:' '  - id: eval_1' '    description: sizing' '    runnable: bash' '    check_type: deterministic' '    terminal: true' '    expected_duration_sec: 1' 'retry_policy:' '  max_iterations: 8' '  circuit_breaker_no_progress: 3' '  on_terminal_failure: park_with_context' 'agent_contract:' '  version: 2' '  read: [intent]' '  produce: [code]' '  required_tools: [bash]' '  timeout_minutes: 5' '  sandbox_type: host' '  emit: [pass, fail]' '```' '' '## Exit Check' '```bash' 'eval_1' '```'
  } > "$file"
}

run() {
  local name="$1" expected="$2" pattern="$3" effort="$4" touches="$5" creates="$6" children="$7" backend="$8"
  local tmp file out rc slug
  TOTAL=$((TOTAL + 1))
  tmp="$(mktemp -d -t taskspec-size-XXXXXX)"
  slug="$(printf '%s' "$effort" | tr '[:upper:]' '[:lower:]' | tr -cd '[:lower:]')"; [ -n "$slug" ] || slug="unknown"
  file="$tmp/T-20260811-size-$slug.md"
  mkspec "$file" "$effort" "$touches" "$creates" "$children" "$backend"
  out="$(bash "$VALIDATE" --no-state --skip-depends-on --skip-touches-paths "$file" 2>&1)"; rc=$?
  rm -rf "$tmp"
  if [ "$rc" -ne "$expected" ]; then fail "$name" "exit $rc, expected $expected"; return; fi
  if [ -n "$pattern" ] && ! printf '%s\n' "$out" | grep -qiE "$pattern"; then fail "$name" "missing /$pattern/"; return; fi
  pass "$name"
}

echo "== effort sizing and composition =="
run "XS leaf" 0 "" XS "README.md" "" "" any
run "S leaf union budget" 0 "" S "README.md" "new.md" "" any
run "M leaf" 0 "" M "a,b" "c" "" any
run "L long horizon" 0 "accepted.*long-horizon" L "a,b,c" "d,e" "" codex
run "L wrong backend" 1 "requires a LONG-HORIZON" L "a" "" "" any
run "S over budget warns" 0 "Mis-sized" S "a,b" "c" "" any
run "leaf cannot have children" 1 "only XL/XXL nodes" S "a" "" "T-20260811-child-one,T-20260811-child-two" any
run "XL needs children" 1 "MUST declare children" XL "" "" "" any
run "XXL needs three children" 1 "MUST declare children" XXL "" "" "T-20260811-child-one,T-20260811-child-two" any
run "XL composition node" 0 "composition unit" XL "" "" "T-20260811-child-one,T-20260811-child-two" any
run "XXL composition node" 0 "composition unit" XXL "" "" "T-20260811-child-one,T-20260811-child-two,T-20260811-child-three" any
run "node owns no writes" 1 "must own no write surface" XL "a" "" "T-20260811-child-one,T-20260811-child-two" any
run "invalid child id" 1 "invalid Task-Spec id" XL "" "" "T-a,T-b" any
run "unknown size" 1 "effort must be one of" ZZ "a" "" "" any

echo
if [ "$FAILED" -eq 0 ]; then
  echo "PASS — all $TOTAL sizing rows green."
  exit 0
fi
echo "FAIL — $FAILED of $TOTAL sizing rows red." >&2
exit 1
