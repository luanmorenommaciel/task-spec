#!/usr/bin/env bash
# JSON Schema reference integrity and checked-in artifact conformance.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$ROOT/tests/schema_contracts.py"
