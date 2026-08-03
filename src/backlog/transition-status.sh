#!/usr/bin/env bash
# transition-status.sh — Atomically transition a task's status.
#
# Usage:
#   bash transition-status.sh <task-id> <new-status> [reason]
#
# Statuses: ready | in-progress | blocked | done | parked

set -euo pipefail

# shellcheck source=../lib/_lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/_lib.sh"
ts_version_flag "$@"

TASK_ID="${1:?Usage: transition-status.sh <task-id> <new-status> [reason]}"
NEW_STATUS="${2:?new-status required}"
REASON="${3:-}"

case "$NEW_STATUS" in
  ready|in-progress|blocked|done|parked) ;;
  *) echo "ERROR: invalid status '$NEW_STATUS'" >&2; exit 1 ;;
esac

TASK_FILE=""
for candidate in \
  "$TASKSPEC_BACKLOG_DIR/${TASK_ID}.md" \
  "$TASKSPEC_BACKLOG_DIR/done/${TASK_ID}.md" \
  "$TASKSPEC_BACKLOG_DIR/parked/${TASK_ID}.md"; do
  if [[ -f "$candidate" ]]; then
    TASK_FILE="$candidate"
    break
  fi
done

if [[ -z "$TASK_FILE" ]]; then
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

TMP="${TASK_FILE}.tmp.$$"
ts_prepare_tmp "$TMP"
awk -v new="$NEW_STATUS" '
  /^status:/ && !done { print "status: " new; done=1; next }
  { print }
' "$TASK_FILE" > "$TMP"
mv "$TMP" "$TASK_FILE"

TARGET_LOC="$TASK_FILE"
case "$NEW_STATUS" in
  done)
    mkdir -p "$TASKSPEC_BACKLOG_DIR/done"
    TARGET_LOC="$TASKSPEC_BACKLOG_DIR/done/${TASK_ID}.md"
    [[ "$TASK_FILE" != "$TARGET_LOC" ]] && mv "$TASK_FILE" "$TARGET_LOC"
    ;;
  parked)
    mkdir -p "$TASKSPEC_BACKLOG_DIR/parked"
    TARGET_LOC="$TASKSPEC_BACKLOG_DIR/parked/${TASK_ID}.md"
    [[ "$TASK_FILE" != "$TARGET_LOC" ]] && mv "$TASK_FILE" "$TARGET_LOC"
    ;;
  ready|in-progress|blocked)
    if [[ "$TASK_FILE" == "$TASKSPEC_BACKLOG_DIR/done"/* || "$TASK_FILE" == "$TASKSPEC_BACKLOG_DIR/parked"/* ]]; then
      TARGET_LOC="$TASKSPEC_BACKLOG_DIR/${TASK_ID}.md"
      mv "$TASK_FILE" "$TARGET_LOC"
    fi
    ;;
esac

TS="$(date -u +%FT%TZ)"
LEDGER_LINE="{\"ts\":\"$TS\",\"task\":\"$TASK_ID\",\"event\":\"status_change\",\"from\":\"$CURRENT\",\"to\":\"$NEW_STATUS\""
if [[ -n "$REASON" ]]; then
  LEDGER_LINE="$LEDGER_LINE,\"reason\":\"$REASON\""
fi
LEDGER_LINE="$LEDGER_LINE}"
echo "$LEDGER_LINE" >> "$TASKSPEC_BACKLOG_DIR/_metrics.jsonl"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -x "$SCRIPT_DIR/rebuild-state.sh" ]]; then
  bash "$SCRIPT_DIR/rebuild-state.sh" >/dev/null 2>&1 || true
fi

echo ">>> $TASK_ID: $CURRENT -> $NEW_STATUS"
echo "    file: $TARGET_LOC"
[[ -n "$REASON" ]] && echo "    reason: $REASON"
