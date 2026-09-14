#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASKSPEC_ISOLATION_RECIPE=1 bash "$ROOT/tests/test-mesh-isolation.sh"
