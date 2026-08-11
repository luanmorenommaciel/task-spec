#!/usr/bin/env bash
# install-hooks.sh — Install git hooks for the task-spec skill.
#
# Usage:
#   bash install-hooks.sh
#
# This installs a pre-commit hook that runs rebuild-state.sh whenever
# tasks/T-*.md files are staged, ensuring _state.yaml stays in sync.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/_lib.sh
source "$SCRIPT_DIR/../lib/_lib.sh"
ts_version_flag "$@"

REPO_ROOT="$(cd "$SCRIPT_DIR" && git rev-parse --show-toplevel 2>/dev/null || echo "")"

if [[ -z "$REPO_ROOT" ]]; then
  echo "ERROR: not inside a git repository" >&2
  exit 1
fi

HOOK_DIR="$REPO_ROOT/.git/hooks"
PRE_COMMIT="$HOOK_DIR/pre-commit"

mkdir -p "$HOOK_DIR"

# Write the pre-commit hook
cat > "$PRE_COMMIT" << 'HOOK'
#!/usr/bin/env bash
# pre-commit hook — task-spec state enforcement
# Auto-installed by taskspec.

set -euo pipefail

# Only run if task files are being committed
# Match Task-Spec files at any repository depth.
if git diff --cached --name-only | grep -qE '(^|/)tasks/(queue/|done/|parked/)?T-.*\.md$'; then
  REPO_ROOT="$(git rev-parse --show-toplevel)"
  if command -v taskspec >/dev/null 2>&1; then
    TASKSPEC_BACKLOG_DIR="$REPO_ROOT/tasks"
    export TASKSPEC_BACKLOG_DIR
    taskspec rebuild-state
    if [[ -f "$TASKSPEC_BACKLOG_DIR/_state.yaml" ]]; then
      git add "$TASKSPEC_BACKLOG_DIR/_state.yaml"
    fi
  else
    echo "task-spec: taskspec is not on PATH; derived state was not refreshed" >&2
    exit 1
  fi
fi
HOOK

chmod +x "$PRE_COMMIT"

echo ">>> Installed pre-commit hook to $PRE_COMMIT"
echo "    It will run rebuild-state.sh whenever task files are staged."
