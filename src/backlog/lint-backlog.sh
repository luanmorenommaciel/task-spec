#!/usr/bin/env bash
# Compatibility wrapper. TaskGraphView/v1 is the one backlog linter.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set +e
python3 "$SCRIPT_DIR/../graph/task_graph.py" --backlog "${TASKSPEC_BACKLOG_DIR:-tasks}" --check "$@"
rc=$?
set -e
if [[ $rc -eq 0 ]]; then echo "LINT=OK"; else echo "LINT=ISSUES"; fi
exit "$rc"
