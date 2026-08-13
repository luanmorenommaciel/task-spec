#!/usr/bin/env bash
# archive.sh — Move done/parked tasks out of active backlog into subdirs.
#
# Idempotent. Safe to run anytime. Updates _state.yaml after moves.
#
# Usage:
#   taskspec archive

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/_lib.sh
source "$SCRIPT_DIR/../lib/_lib.sh"
ts_version_flag "$@"
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: taskspec archive"
  exit 0
fi
if [[ $# -ne 0 ]]; then
  echo "taskspec archive: no arguments are accepted" >&2
  exit 2
fi

if [[ ! -d "$TASKSPEC_BACKLOG_DIR" ]]; then
  exit 0
fi

mkdir -p "$TASKSPEC_BACKLOG_DIR/done" "$TASKSPEC_BACKLOG_DIR/parked"
LOCK_FILE="$TASKSPEC_BACKLOG_DIR/.state.lock"
if ! ts_lock_acquire "$LOCK_FILE"; then
  echo "taskspec archive: another process holds the task-state lock" >&2
  exit 1
fi
trap 'ts_lock_release "$LOCK_FILE"' EXIT

MOVED_DONE=0
MOVED_PARKED=0

for FILE in "$TASKSPEC_BACKLOG_DIR"/T-*.md; do
  [[ -f "$FILE" ]] || continue

  STATUS=$(grep '^status:' "$FILE" | head -1 | awk '{print $2}')
  ID=$(grep '^id:' "$FILE" | head -1 | awk '{print $2}')

  case "$STATUS" in
    done)
      mv "$FILE" "$TASKSPEC_BACKLOG_DIR/done/${ID}.md"
      MOVED_DONE=$((MOVED_DONE + 1))
      ;;
    parked)
      mv "$FILE" "$TASKSPEC_BACKLOG_DIR/parked/${ID}.md"
      MOVED_PARKED=$((MOVED_PARKED + 1))
      ;;
  esac
done

# Rebuild state after moves
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ -x "$SKILL_DIR/src/backlog/rebuild-state.sh" ]]; then
  TASKSPEC_STATE_LOCK_HELD=1 bash "$SKILL_DIR/src/backlog/rebuild-state.sh" >/dev/null 2>&1 || true
fi

echo ">>> Archived: $MOVED_DONE done, $MOVED_PARKED parked"
