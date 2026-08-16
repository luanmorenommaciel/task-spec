#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "$ROOT/tests/schema_contracts.py" | grep -q '^SCHEMAS=READY'
(cd "$ROOT" && go test ./... && go vet ./...)

for suite in \
  test-mesh-contracts.sh \
  test-mesh-daemon.sh \
  test-mesh-leases.sh \
  test-mesh-routing-integration.sh \
  test-mesh-adapters.sh \
  test-mesh-cockpit.sh; do
  bash "$ROOT/tests/$suite"
done

echo "MESH_RECOVERY=READY"
echo "MESH_CONFORMANCE=READY"
