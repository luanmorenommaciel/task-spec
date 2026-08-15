#!/usr/bin/env bash
# Usage failures are caller errors (2), never contract failures (1).
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI="$ROOT/bin/taskspec"
PASS=0
FAIL=0

check_usage() {
  label="$1"
  shift
  out="$($CLI --json "$@" 2>/dev/null)"
  rc=$?
  if [ "$rc" -eq 2 ] && printf '%s' "$out" | python3 -c '
import json, sys
value = json.load(sys.stdin)
assert value["contract"] == "TaskSpecCLIResult/v1"
assert value["ok"] is False
assert value["exit_code"] == 2
' 2>/dev/null; then
    PASS=$((PASS + 1))
    printf 'ok    %s\n' "$label"
  else
    FAIL=$((FAIL + 1))
    printf 'FAIL  %s rc=%s output=%s\n' "$label" "$rc" "$out" >&2
  fi
}

check_usage "new requires slug and effort" new
check_usage "new rejects an unknown option" new --not-a-real-option
check_usage "new requires --format value" new --format
check_usage "metrics rejects an unknown option" metrics --not-a-real-option
check_usage "metrics requires --since value" metrics --since

if [ "$FAIL" -eq 0 ]; then
  printf 'CLI_USAGE=PASS checks=%s\n' "$PASS"
  exit 0
fi
printf 'CLI_USAGE=FAIL failures=%s\n' "$FAIL" >&2
exit 1
