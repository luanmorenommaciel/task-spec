#!/usr/bin/env bash
# backup-backlog.sh — Snapshot tasks/ folder for paranoia (beyond git).
#
# Usage:
#   bash backup-backlog.sh                  # default: ~/Backups/backlog-YYYYMMDD.tar.gz
#   bash backup-backlog.sh /custom/path     # specify destination

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/_lib.sh
source "$SCRIPT_DIR/../lib/_lib.sh"
ts_version_flag "$@"

DEFAULT_DIR="${HOME}/Backups"
DEST_DIR="${1:-$DEFAULT_DIR}"

if [[ ! -d "$TASKSPEC_BACKLOG_DIR" ]]; then
  echo "(no $TASKSPEC_BACKLOG_DIR/ directory in $(pwd); nothing to back up)"
  exit 0
fi

mkdir -p "$DEST_DIR"

DATE="$(date +%Y%m%d-%H%M%S)"
REPO_NAME="$(basename "$(pwd)")"
ARCHIVE="${DEST_DIR}/backlog-${REPO_NAME}-${DATE}.tar.gz"

BACKLOG_PARENT="$(cd "$(dirname "$TASKSPEC_BACKLOG_DIR")" && pwd)"
BACKLOG_NAME="$(basename "$TASKSPEC_BACKLOG_DIR")"
tar -C "$BACKLOG_PARENT" -czf "$ARCHIVE" "$BACKLOG_NAME"

# Cleanup: keep last 30 days
find "$DEST_DIR" -name "backlog-${REPO_NAME}-*.tar.gz" -mtime +30 -delete 2>/dev/null || true

echo ">>> Backup written: $ARCHIVE"
echo "    size: $(du -h "$ARCHIVE" | cut -f1)"
echo "    retention: 30 days"
