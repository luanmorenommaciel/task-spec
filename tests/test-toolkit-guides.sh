#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import json,subprocess,sys
root=Path(sys.argv[1]);cli=root/'bin/taskspec'
for topic in ['intent','decomposition','recipes','mesh','acceptance','release','maintenance','migration','install','cli']:
 data=json.loads(subprocess.check_output(['bash',str(cli),'--json','guide',topic],text=True))['data']
 assert data['version']==(root/'VERSION').read_text().strip() and len(data['content'])>100
source=subprocess.check_output([sys.executable,str(root/'src/cli/registry.py'),'reference'],text=True)
assert source==(root/'docs/guides/toolkit/cli.md').read_text()
print('TOOLKIT_GUIDES=PASS')
PY
