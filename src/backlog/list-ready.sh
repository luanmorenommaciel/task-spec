#!/usr/bin/env bash
# Compatibility wrapper. TaskGraphView/v1 is the one readiness resolver.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == "--version" ]]; then source "$SCRIPT_DIR/../lib/_lib.sh"; ts_version_flag --version; exit 0; fi
exec python3 "$SCRIPT_DIR/ready.py" "$@"
