#!/usr/bin/env python3
"""Read an installed, version-matched guide without consulting conversation history."""
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
TOPICS={'intent':'intent.md','decomposition':'decomposition.md','recipes':'recipes.md','mesh':'execution.md','acceptance':'acceptance.md','release':'sdlc.md','maintenance':'sdlc.md','migration':'migration.md','install':'install.md','cli':'cli.md'}
if len(sys.argv)!=2 or sys.argv[1] not in TOPICS:
    print('GUIDE=TOPICS '+', '.join(TOPICS)); raise SystemExit(0 if len(sys.argv)==1 else 2)
path=ROOT/'docs/guides/toolkit'/TOPICS[sys.argv[1]]
if not path.is_file():
    print('GUIDE=UNAVAILABLE reinstall matching toolkit resources',file=sys.stderr);raise SystemExit(3)
data={'contract':'TaskGuide/v1','topic':sys.argv[1],'version':(ROOT/'VERSION').read_text().strip(),'path':str(path),'content':path.read_text()}
print(json.dumps(data,indent=2) if os.environ.get('TASKSPEC_JSON_MODE')=='1' else data['content'])
