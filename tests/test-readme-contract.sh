#!/usr/bin/env bash
# README command coverage and generated status/reference reconciliation.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$ROOT/tests/readme_contract.py"
python3 "$ROOT/tools/render-status.py" --check "$ROOT/README.md"
python3 "$ROOT/tools/render-cli-reference.py" --check "$ROOT/docs/reference/cli.md"
