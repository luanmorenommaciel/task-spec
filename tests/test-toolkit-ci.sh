#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1]);ci=(root/'.github/workflows/ci.yml').read_text()
assert 'os: [ubuntu-latest, macos-latest]' in ci
assert ci.index('run: bash bin/taskspec setup decompose')<ci.index('run: make check')
assert 'brew install shellcheck' in ci
print('TOOLKIT_CI=CONFIGURED hosted execution not inferred')
PY
