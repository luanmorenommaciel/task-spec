#!/usr/bin/env bash
# archive.sh — Move done/parked tasks out of active backlog into subdirs.
#
# Idempotent. Safe to run anytime. Updates _state.yaml after moves.
#
# Usage:
#   bash archive.sh

set -euo pipefail

# shellcheck source=../lib/_lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/_lib.sh"
ts_version_flag "$@"

if [[ ! -d "$TASKSPEC_BACKLOG_DIR" ]]; then
  exit 0
fi

mkdir -p "$TASKSPEC_BACKLOG_DIR/done" "$TASKSPEC_BACKLOG_DIR/parked"

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

# Rebuild state after moves (rebuild-state.sh sits beside this script in src/backlog/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -x "$SCRIPT_DIR/rebuild-state.sh" ]]; then
  bash "$SCRIPT_DIR/rebuild-state.sh" >/dev/null 2>&1 || true
fi

echo ">>> Archived: $MOVED_DONE done, $MOVED_PARKED parked"
