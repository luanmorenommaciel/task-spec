#!/usr/bin/env bash
# Print a compact readiness board and one exact next action.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
TASKS="$ROOT/${TASKSPEC_BACKLOG_DIR:-tasks}"
COMMON="$(git -C "$ROOT" rev-parse --git-common-dir 2>/dev/null || true)"
if [[ -n "$COMMON" && "$COMMON" != /* ]]; then COMMON="$(cd "$ROOT/$COMMON" && pwd)"; fi
KEY="${COMMON:+$COMMON/info/taskspec-signing-key}"

echo "Task-Spec readiness"
if [[ -d "$TASKS" ]]; then echo "PASS  workspace  $TASKS"; workspace=1; else echo "MISS  workspace  $TASKS"; workspace=0; fi
if command -v git >/dev/null 2>&1; then echo "PASS  git        $(git --version)"; else echo "MISS  git"; fi
if command -v shellcheck >/dev/null 2>&1; then echo "PASS  shellcheck $(shellcheck --version | awk '/^version:/{print $2}')"; else echo "MISS  shellcheck (required by PRE-gate)"; fi
if [[ -n "${TASKSPEC_SIGNING_KEY:-}" || ( -n "$KEY" && -r "$KEY" ) ]]; then echo "PASS  signing    repository key available"; signing=1; else echo "MISS  signing    no repository key"; signing=0; fi

if [[ "$workspace" -eq 0 ]]; then
  echo "NEXT: taskspec init"
elif [[ "$signing" -eq 0 ]]; then
  echo "NEXT: taskspec setup signing"
elif ! find "$TASKS" -type f -name 'T-*.md' -print -quit 2>/dev/null | grep -q .; then
  echo "NEXT: ask the installed Task-Spec skill to compose a TaskPlan v1 manifest"
else
  first="$(find "$TASKS" -type f -name 'T-*.md' | sort | head -1)"
  echo "NEXT: taskspec validate $first"
fi
echo "SETUP=READY"
