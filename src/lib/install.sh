#!/usr/bin/env bash
# Backward-compatible entrypoint. The canonical installer lives at repo root.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ "${1:-}" == "--version" ]]; then
  printf 'task-spec v%s\n' "$(tr -d '[:space:]' < "$ROOT/VERSION")"
  exit 0
fi
exec bash "$ROOT/install.sh" "$@"
