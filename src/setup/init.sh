#!/usr/bin/env bash
# Create a non-clobbering Task-Spec workspace in the current repository.
set -euo pipefail

DRY_RUN="${TASKSPEC_DRY_RUN:-0}"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
TASKS="$ROOT/tasks"
CONFIG_DIR="$ROOT/.taskspec"
CONFIG="$CONFIG_DIR/config"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "DRY_RUN: create $TASKS/ and $CONFIG if absent"
  echo "INIT=DRY_RUN"
  exit 0
fi

mkdir -p "$TASKS" "$CONFIG_DIR"
if [[ ! -f "$CONFIG" ]]; then
  umask 077
  printf '%s\n' \
    '# Task-Spec repository configuration (no credentials)' \
    'backlog_dir=tasks' \
    'research_provider=none' \
    > "$CONFIG"
  echo "created: $CONFIG"
else
  echo "kept:    $CONFIG"
fi
if [[ ! -f "$TASKS/.gitkeep" && -z "$(find "$TASKS" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  : > "$TASKS/.gitkeep"
  echo "created: $TASKS/.gitkeep"
else
  echo "kept:    $TASKS/"
fi
echo "INIT=OK"
