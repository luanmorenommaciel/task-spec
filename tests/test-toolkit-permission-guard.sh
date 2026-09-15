#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import json,subprocess,sys,tempfile,socket,tomllib
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'tests/evals/toolkit'))
from claude_permission_guard import denied,decision
from codex_mesh_permissions import config_args,apply
from providers import permission_denials
assert permission_denials(json.dumps({'type':'result','permission_denials':[{'tool_name':'Write'}]}))
assert permission_denials(json.dumps({'type':'item.completed','item':{'type':'command_execution','exit_code':1,'aggregated_output':'Operation not permitted'}}))
assert not permission_denials(json.dumps({'type':'item.completed','item':{'type':'command_execution','exit_code':0,'aggregated_output':'Documentation: permission denied'}}))
assert not permission_denials(json.dumps({'type':'item.completed','item':{'type':'command_execution','exit_code':1,'aggregated_output':'AssertionError: expected behavior'}}))
assert not permission_denials('{"type":"item.completed","item":null}\ninvalid json')
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
with tempfile.TemporaryDirectory() as temporary:
 work=Path(temporary).resolve(); endpoint=work/'control.sock'
 with socket.socket(socket.AF_UNIX) as server:
  server.bind(str(endpoint))
  args=config_args(work,endpoint)
  policy=tomllib.loads(args[3])['permissions']['taskspec_chat']
  assert policy['extends']==':workspace'
  assert policy['network']['unix_sockets']=={str(endpoint):'allow'}
  assert policy['network']['domains']=={}
  assert policy['network']['dangerously_allow_all_unix_sockets'] is False
  assert policy['filesystem'][str(work/'.git')]=='read'
  configured=apply(['codex','exec','--sandbox','workspace-write','-'],work,endpoint)
  assert '--sandbox' not in configured and configured[-1]=='-'
 regular=work/'regular';regular.write_text('not a socket')
 try:config_args(work,regular)
 except ValueError:pass
 else:raise AssertionError('Regular file cannot grant socket permission')
print('TOOLKIT_PERMISSION_GUARD=PASS recorded denial stops continuation; ordinary eval and validation failures remain distinct')
PY
