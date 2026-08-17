#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
output=$(bash "$ROOT/bin/taskspec" demo)
grep -q '^DEMO=READY$' <<< "$output"
grep -q '^  PLAN=VALID$' <<< "$output"
grep -q '^  DOD=COMPLETE$' <<< "$output"
grep -q '^  VERDICT=DELEGATE TIER=1$' <<< "$output"
grep -q '^  HANDOFF=TaskHandoff/v3$' <<< "$output"
grep -q '^  EVAL=PASS$' <<< "$output"
grep -q '^  ACCEPTED=1$' <<< "$output"

dry_output=$(bash "$ROOT/bin/taskspec" --dry-run demo)
grep -q '^DEMO=DRY_RUN ' <<< "$dry_output"

json_output=$(bash "$ROOT/bin/taskspec" --json demo)
python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["ok"] and d["command"] == "demo" and "DEMO=READY" in d["stdout"]' <<< "$json_output"

# Missing shellcheck is a demo-blocking host floor. Fail loudly with a blocker
# and next action; do not exit 1 on empty stdout/stderr (plain or --json).
_hide_shellcheck_path() {
  local parent="$1"
  local out="" dir shadow exe base
  local IFS=:
  for dir in $PATH; do
    if [[ -x "${dir}/shellcheck" ]]; then
      shadow="$parent/$(printf '%s' "$dir" | tr '/ ' '__')"
      mkdir -p "$shadow"
      for exe in "$dir"/*; do
        base="${exe##*/}"
        [[ "$base" == "shellcheck" ]] && continue
        [[ -x "$exe" ]] || continue
        ln -s "$exe" "$shadow/$base"
      done
      out="${out:+$out:}$shadow"
    elif [[ -n "$dir" ]]; then
      out="${out:+$out:}$dir"
    fi
  done
  printf '%s' "$out"
}

HIDE_DIR="$(mktemp -d -t taskspec-hide-shellcheck-XXXXXX)"
trap 'rm -rf "$HIDE_DIR"' EXIT
HIDDEN_PATH="$(_hide_shellcheck_path "$HIDE_DIR")"
[[ -z "$(PATH="$HIDDEN_PATH" command -v shellcheck || true)" ]]

set +e
blocked=$(PATH="$HIDDEN_PATH" bash "$ROOT/bin/taskspec" demo 2>"$HIDE_DIR/demo.err")
blocked_rc=$?
set -e
[[ "$blocked_rc" -ne 0 ]]
[[ -n "$blocked" ]]
grep -q '^DEMO=BLOCKED' <<< "$blocked"
grep -q 'BLOCKER:' <<< "$blocked"
grep -q '^NEXT:' <<< "$blocked"

set +e
json_blocked=$(PATH="$HIDDEN_PATH" bash "$ROOT/bin/taskspec" --json demo)
json_blocked_rc=$?
set -e
[[ "$json_blocked_rc" -ne 0 ]]
python3 -c 'import json,sys
d=json.load(sys.stdin)
assert d["ok"] is False and d["command"] == "demo" and d["exit_code"] != 0
text = d["stdout"] + d["stderr"]
assert text.strip(), "json demo fail path must not be empty"
assert "DEMO=BLOCKED" in text and "BLOCKER:" in text and "NEXT:" in text
' <<< "$json_blocked"

set +e
doc=$(PATH="$HIDDEN_PATH" bash "$ROOT/bin/taskspec" doctor)
doc_rc=$?
set -e
[[ "$doc_rc" -ne 0 ]]
grep -q '^FAIL  shellcheck' <<< "$doc"
grep -q '^DOCTOR=BLOCKED$' <<< "$doc"
grep -q '^NEXT:' <<< "$doc"
if grep -q '^DOCTOR=READY$' <<< "$doc"; then
  echo "doctor printed DOCTOR=READY on a blocked host floor" >&2
  exit 1
fi

doc_ok=$(bash "$ROOT/bin/taskspec" doctor)
grep -q '^DOCTOR=READY$' <<< "$doc_ok"

echo "PASS — isolated demo reaches independent acceptance"
