#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import subprocess,sys,tempfile
root=Path(sys.argv[1])
sys.path.insert(0,str(root/'tests/evals/toolkit'))
from public_evaluator import DIRECTORY,SCRIPT,INPUTS,install,verify,command
with tempfile.TemporaryDirectory(prefix='public evaluator ') as temp:
 workspace=Path(temp)/'workspace with spaces';workspace.mkdir()
 manifest=install(root,workspace);verify(workspace,manifest)
 for relative in INPUTS:
  assert (workspace/DIRECTORY/relative).read_bytes()==(root/relative).read_bytes()
 # The copied evaluator resolves its own registered input root, without relying
 # on an external source path. Keep a linked target repo only for this unit test.
 for name in ('bin','src','VERSION'):
  (workspace/name).symlink_to(root/name)
 # Load registered recipe inputs from the copied bundle and execute real checks.
 result=subprocess.run(command(manifest,'small-fix'),shell=True,cwd=workspace,text=True,capture_output=True)
 assert result.returncode==0 and '"passed": true' in result.stdout,result
 # An unrecognized scenario fails normally, rather than failing to load inputs.
 result=subprocess.run(command(manifest,'unknown-case'),shell=True,cwd=workspace,text=True,capture_output=True)
 assert result.returncode!=0 and 'invalid choice' in result.stderr,result
 script=workspace/DIRECTORY/SCRIPT
 original=script.read_bytes();script.write_text('raise SystemExit(0)\n')
 result=subprocess.run(command(manifest,'small-fix'),shell=True,cwd=workspace,text=True,capture_output=True)
 assert result.returncode!=0 and 'integrity check failed' in result.stderr,result
 try:verify(workspace,manifest)
 except ValueError:pass
 else:raise AssertionError('controller accepted a substituted evaluator')
 script.write_bytes(original)
 fixture=workspace/DIRECTORY/INPUTS[1];fixture.write_text('{}')
 result=subprocess.run(command(manifest,'small-fix'),shell=True,cwd=workspace,text=True,capture_output=True)
 assert result.returncode!=0 and 'integrity check failed' in result.stderr,result
print('TOOLKIT_PUBLIC_EVALUATOR=PASS exact local resources; script and fixture substitution refused')
PY
