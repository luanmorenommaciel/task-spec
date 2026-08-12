#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
output=$(bash "$ROOT/bin/taskspec" demo)
grep -q '^DEMO=READY$' <<< "$output"
grep -q '^  PLAN=VALID$' <<< "$output"
grep -q '^  DOD=COMPLETE$' <<< "$output"
grep -q '^  VERDICT=DELEGATE TIER=1$' <<< "$output"
grep -q '^  HANDOFF=TaskHandoff/v1$' <<< "$output"
grep -q '^  EVAL=PASS$' <<< "$output"
grep -q '^  ACCEPTED=1$' <<< "$output"

dry_output=$(bash "$ROOT/bin/taskspec" --dry-run demo)
grep -q '^DEMO=DRY_RUN ' <<< "$dry_output"

json_output=$(bash "$ROOT/bin/taskspec" --json demo)
python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["ok"] and d["command"] == "demo" and "DEMO=READY" in d["stdout"]' <<< "$json_output"

echo "PASS — isolated demo reaches independent acceptance"
