#!/usr/bin/env bash
# Select only the TaskSpec-owned runtime or an explicit operator override.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
runtime="${TASKSPEC_DECOMPOSE_PYTHON:-$ROOT/.taskspec/runtime/decompose/bin/python}"
if [[ ! -x "$runtime" ]]; then runtime="$(command -v python3 || true)"; fi
if [[ -z "$runtime" ]] || ! "$runtime" -c 'import sys, yaml, jsonschema; assert sys.version_info >= (3, 11)' >/dev/null 2>&1; then
  echo 'DECOMPOSE=UNAVAILABLE Python >= 3.11, PyYAML and jsonschema required. NEXT: taskspec setup decompose' >&2
  exit 3
fi
exec "$runtime" "$ROOT/src/decompose/cli.py" "$@"
