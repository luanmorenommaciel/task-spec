#!/usr/bin/env bash
# list-ready.sh — Show all tasks ready for pickup.
#
# Usage:
#   bash list-ready.sh                # all ready tasks
#   bash list-ready.sh --effort=S     # only S-effort
#   bash list-ready.sh --agent=any    # only agent-agnostic tasks

set -euo pipefail

# shellcheck source=../lib/_lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/_lib.sh"
ts_version_flag "$@"

FILTER_EFFORT=""
FILTER_AGENT=""

for arg in "$@"; do
  case "$arg" in
    --effort=*) FILTER_EFFORT="${arg#--effort=}" ;;
    --agent=*) FILTER_AGENT="${arg#--agent=}" ;;
  esac
done

if [[ ! -d "$TASKSPEC_BACKLOG_DIR" ]]; then
  echo "(no $TASKSPEC_BACKLOG_DIR/ directory in $(pwd))"
  exit 0
fi

printf "%-32s %-7s %-12s %s\n" "ID" "EFFORT" "AGENT" "TITLE"
printf "%-32s %-7s %-12s %s\n" "$(printf '=%.0s' {1..32})" "======" "============" "$(printf '=%.0s' {1..50})"

for FILE in "$TASKSPEC_BACKLOG_DIR"/T-*.md; do
  [[ -f "$FILE" ]] || continue

  STATUS=$(grep '^status:' "$FILE" | head -1 | awk '{print $2}')
  [[ "$STATUS" == "ready" ]] || continue

  EFFORT=$(grep '^effort:' "$FILE" | head -1 | awk '{print $2}')
  AGENT=$(grep '^agent:' "$FILE" | head -1 | awk '{print $2}')
  ID=$(grep '^id:' "$FILE" | head -1 | awk '{print $2}')
  TITLE=$(grep '^title:' "$FILE" | head -1 | sed 's/^title: *//')

  [[ -n "$FILTER_EFFORT" && "$EFFORT" != "$FILTER_EFFORT" ]] && continue
  [[ -n "$FILTER_AGENT" && "$AGENT" != "$FILTER_AGENT" ]] && continue

  printf "%-32s %-7s %-12s %s\n" "$ID" "$EFFORT" "$AGENT" "${TITLE:0:60}"
done
