#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--version" ]]; then
  echo "taskmesh-fake/1.0.0"
  exit 0
fi

[[ -n "${TASKMESH_HANDOFF:-}" && -f "$TASKMESH_HANDOFF" ]]
[[ -n "${TASKMESH_ATTEMPT_ID:-}" ]]
[[ -z "${TASKSPEC_SIGNING_KEY:-}" ]]
if [[ "${1:-}" == "--sleep" ]]; then
  sleep "${TASKMESH_FAKE_SLEEP_SEC:-30}"
fi
target="${TASKMESH_FAKE_WRITE_PATH:-a.txt}"
printf 'completed by %s\n' "$TASKMESH_ATTEMPT_ID" >"$target"
printf '%s\n' '{"type":"assistant","message":"fake execution complete","credential":"sk-taskmesh-should-be-redacted"}'
