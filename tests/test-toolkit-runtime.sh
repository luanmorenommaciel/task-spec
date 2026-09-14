#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import os,subprocess,sys,tempfile
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'src/security'))
from task_revision import revision
from verify_authorization import verify
with tempfile.TemporaryDirectory() as tmp:
 work=Path(tmp);spec=work/'task.md';spec.write_text((root/'tests/fixtures/T-20260603-stamp-then-verify.md').read_text())
 env={**os.environ,'TASKSPEC_SIGNING_KEY':'toolkit-authorization-fixture'};os.environ['TASKSPEC_SIGNING_KEY']=env['TASKSPEC_SIGNING_KEY']
 rev=revision(spec)['task_revision_digest']
 try:verify(spec,rev);raise AssertionError('unsigned work verified')
 except ValueError:pass
 subprocess.run([sys.executable,str(root/'src/security/stamp.py'),str(spec),'--by','fixture','--at','2026-09-14T00:00:00Z','--backlog',str(work)],env=env,check=True,capture_output=True)
 verify(spec,rev);saved=spec.read_text();spec.write_text(saved.replace('signed_off_by: fixture','signed_off_by: forged'))
 try:verify(spec,rev);raise AssertionError('forged signer verified')
 except ValueError:pass
 spec.write_text(saved+'\nUnapproved scope\n')
 try:verify(spec,rev);raise AssertionError('modified contract verified')
 except ValueError:pass
print('TOOLKIT_RUNTIME=PASS')
PY
