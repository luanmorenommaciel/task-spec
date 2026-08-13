#!/usr/bin/env bash
# transition-status.sh — Atomically transition a task's status.
#
# Usage:
#   taskspec transition <task-id> <new-status> [reason]
#
# Statuses: ready | in-progress | blocked | done | parked

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/_lib.sh
source "$SCRIPT_DIR/../lib/_lib.sh"
ts_version_flag "$@"

if [[ $# -lt 2 ]]; then
  echo "Usage: taskspec transition <task-id> <new-status> [reason]" >&2
  exit 2
fi
TASK_ID="$1"
NEW_STATUS="$2"
REASON="${3:-}"

case "$NEW_STATUS" in
  ready|in-progress|blocked|done|parked) ;;
  *) echo "ERROR: invalid status '$NEW_STATUS'" >&2; exit 2 ;;
esac

set +e
TASK_FILE="$(python3 "$SCRIPT_DIR/../graph/resolve_task.py" --backlog "$TASKSPEC_BACKLOG_DIR" "$TASK_ID" 2>/dev/null)"
resolve_rc=$?
set -e
if [[ $resolve_rc -ne 0 || -z "$TASK_FILE" ]]; then
  echo "ERROR: task ${TASK_ID} not found" >&2
  exit 1
fi

mkdir -p "$TASKSPEC_BACKLOG_DIR"
LOCK_FILE="$TASKSPEC_BACKLOG_DIR/.state.lock"
# Portable advisory lock (ts_lock_* uses an atomic mkdir — works on macOS, which
# ships no `flock`). Released on every exit path via the trap below.
if ! ts_lock_acquire "$LOCK_FILE"; then
  echo "ERROR: another process holds the state lock" >&2
  exit 1
fi
trap 'ts_lock_release "$LOCK_FILE"' EXIT

CURRENT=$(grep '^status:' "$TASK_FILE" | head -1 | awk '{print $2}')

if [[ "$CURRENT" == "$NEW_STATUS" ]]; then
  echo "NOOP: $TASK_ID already at status '$NEW_STATUS'"
  exit 0
fi

if [[ "$NEW_STATUS" == "done" ]]; then
  ACCEPTED=$(grep -m1 '^accepted:' "$TASK_FILE" 2>/dev/null | awk -F: '{print $2}' | xargs || true)
  ACCEPTED_BY=$(grep -m1 '^accepted_by:' "$TASK_FILE" 2>/dev/null | sed -E 's/^accepted_by:[[:space:]]*//' || true)
  ACCEPTED_AT=$(grep -m1 '^accepted_at:' "$TASK_FILE" 2>/dev/null | sed -E 's/^accepted_at:[[:space:]]*//' || true)
  if [[ "$ACCEPTED" != "true" || -z "$ACCEPTED_BY" || "$ACCEPTED_BY" == "(none)" \
    || -z "$ACCEPTED_AT" || "$ACCEPTED_AT" == "(none)" ]]; then
    echo "ERROR: $TASK_ID cannot enter done until taskspec accept --stamp records accepted:true, accepted_by, and accepted_at" >&2
    exit 1
  fi
  SIGNED_SIG=$(grep -m1 '^signed_off_sig:' "$TASK_FILE" 2>/dev/null | sed -E 's/^signed_off_sig:[[:space:]]*//' || true)
  if [[ "$SIGNED_SIG" == hmac-sha256-v3:* ]]; then
    ACCEPTED_TIER=$(grep -m1 '^accepted_tier:' "$TASK_FILE" 2>/dev/null | awk -F: '{print $2}' | xargs || true)
    ACCEPTED_ATTEMPT=$(grep -m1 '^accepted_attempt_id:' "$TASK_FILE" 2>/dev/null | sed -E 's/^accepted_attempt_id:[[:space:]]*//' | tr -d '"' || true)
    ACCEPTED_AUTH=$(grep -m1 '^accepted_authorization_ref:' "$TASK_FILE" 2>/dev/null | sed -E 's/^accepted_authorization_ref:[[:space:]]*//' | tr -d '"' || true)
    RECORD_DIGEST=$(grep -m1 '^acceptance_record_digest:' "$TASK_FILE" 2>/dev/null | sed -E 's/^acceptance_record_digest:[[:space:]]*//' | tr -d '"' || true)
    if [[ ! "$ACCEPTED_TIER" =~ ^[12]$ || -z "$ACCEPTED_ATTEMPT" || "$ACCEPTED_AUTH" != "$SIGNED_SIG" || "$RECORD_DIGEST" != sha256:* ]]; then
      echo "ERROR: $TASK_ID has HMAC v3 and needs the complete acceptance envelope before done" >&2
      exit 1
    fi
    if ! python3 "$SCRIPT_DIR/../accept/record.py" "$TASK_FILE" --backlog "$TASKSPEC_BACKLOG_DIR" >/dev/null; then
      echo "ERROR: $TASK_ID acceptance record does not match the accepted task revision" >&2
      exit 1
    fi
  fi
fi

MUTATION_JSON="$(python3 - "$NEW_STATUS" "$REASON" <<'PY'
import json,sys
value={"status":sys.argv[1]}
if sys.argv[2] and sys.argv[1] in {"blocked","parked"}: value["blocked_reason"]=sys.argv[2]
elif sys.argv[1] in {"ready","in-progress","done"}: value["blocked_reason"]="(none)"
print(json.dumps(value))
PY
)"
python3 "$SCRIPT_DIR/../lib/update_frontmatter.py" "$TASK_FILE" --set-json "$MUTATION_JSON"

TARGET_LOC="$TASK_FILE"
TASK_BASENAME="$(basename "$TASK_FILE")"
case "$NEW_STATUS" in
  done)
    mkdir -p "$TASKSPEC_BACKLOG_DIR/done"
    TARGET_LOC="$TASKSPEC_BACKLOG_DIR/done/$TASK_BASENAME"
    [[ "$TASK_FILE" != "$TARGET_LOC" ]] && mv "$TASK_FILE" "$TARGET_LOC"
    ;;
  parked)
    mkdir -p "$TASKSPEC_BACKLOG_DIR/parked"
    TARGET_LOC="$TASKSPEC_BACKLOG_DIR/parked/$TASK_BASENAME"
    [[ "$TASK_FILE" != "$TARGET_LOC" ]] && mv "$TASK_FILE" "$TARGET_LOC"
    ;;
  ready|in-progress|blocked)
    if [[ "$(dirname "$TASK_FILE")" != "$(cd "$TASKSPEC_BACKLOG_DIR" && pwd)" ]]; then
      TARGET_LOC="$TASKSPEC_BACKLOG_DIR/$TASK_BASENAME"
      mv "$TASK_FILE" "$TARGET_LOC"
    fi
    ;;
esac

TS="$(date -u +%FT%TZ)"
METRIC_ARGS=(schema_version 1 ts "$TS" task "$TASK_ID" event status_change from "$CURRENT" to "$NEW_STATUS")
if [[ -n "$REASON" ]]; then
  METRIC_ARGS+=(reason "$REASON")
fi
ts_append_metric "$TASKSPEC_BACKLOG_DIR/_metrics.jsonl" "${METRIC_ARGS[@]}"

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ -x "$SKILL_DIR/src/backlog/rebuild-state.sh" ]]; then
  TASKSPEC_STATE_LOCK_HELD=1 bash "$SKILL_DIR/src/backlog/rebuild-state.sh" >/dev/null 2>&1 || true
fi

echo ">>> $TASK_ID: $CURRENT -> $NEW_STATUS"
echo "    file: $TARGET_LOC"
if [[ -n "$REASON" ]]; then
  echo "    reason: $REASON"
fi
