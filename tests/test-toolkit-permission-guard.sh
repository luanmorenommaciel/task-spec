#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import json,subprocess,sys,tempfile
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'tests/evals/toolkit'))
from claude_permission_guard import denied,decision
def error(message):return {'type':'user','message':{'content':[{'type':'tool_result','is_error':True,'content':message}]}}
assert denied([error('/fixture/outside is outside /fixture/work; --restricted confines the file tools to the working directory.')])
assert denied([{'type':'result','permission_denials':[{'tool_name':'Read'}]}])
assert not denied([error('Exit code 1\nAssertionError: expected completion artifact')])
assert not denied([error('DECOMPOSE=INVALID owner missing')])
assert not denied([{'type':'user','message':{'content':[{'type':'tool_result','content':'Documentation mentions permission denied.'}]}}])
with tempfile.TemporaryDirectory() as temporary:
 events=Path(temporary)/'events.jsonl'
 events.write_text(json.dumps(error('Permission was denied to use Read'))+'\n{"type":')
 assert decision(events)['continue'] is False
 assert decision(events)['hookSpecificOutput']['permissionDecision'] == 'deny'
 result=subprocess.run([sys.executable,str(root/'tests/evals/toolkit/claude_permission_guard.py'),'--events',str(events)],input=json.dumps({'hook_event_name':'PreToolUse'}),text=True,capture_output=True,check=True)
 assert json.loads(result.stdout)['continue'] is False
 assert json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'] == 'deny'
 events.unlink()
 result=subprocess.run([sys.executable,str(root/'tests/evals/toolkit/claude_permission_guard.py'),'--events',str(events)],input='{}',text=True,capture_output=True,check=True)
 assert json.loads(result.stdout)['continue'] is False
print('TOOLKIT_PERMISSION_GUARD=PASS recorded denial stops continuation; ordinary eval and validation failures remain distinct')
PY
