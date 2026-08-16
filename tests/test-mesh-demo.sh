#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d -t taskspec-mesh-demo-XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

# The cockpit corridor is the executable demonstration: one harness starts a
# bounded attempt, another reconnects to the durable history, a third uses MCP
# to supervise acceptance, and finish leaves the target branch untouched.
bash "$ROOT/tests/test-mesh-cockpit.sh" | tee "$WORK/cockpit.log"
grep -q '^MESH_COCKPIT=READY$' "$WORK/cockpit.log"

echo "MESH_DEMO=READY"
