#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile
root=Path(sys.argv[1]);sys.path[:0]=[str(root/'src/evidence'),str(root/'tests')]
from operational import validate
from schema_contracts import validate_instance
listing=subprocess.run(['bash',str(root/'bin/taskspec'),'mcp'],input=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/list','params':{}})+'\n',text=True,capture_output=True,check=True)
tools=json.loads(listing.stdout)['result']['tools'];names={tool['name'] for tool in tools}
assert names=={'taskspec_handoff','taskspec_validate','taskspec_initiative_status','taskspec_initiative_graph'}
assert all(tool['annotations']['readOnlyHint'] for tool in tools)
for kind in ('incident','release-evidence'):
 value=json.loads((root/'docs/examples'/f'{kind}.json').read_text());validate(value);validate_instance(value,'task-operational-evidence.schema.json')
 bad=dict(value,claim='verified')
 try:validate(bad);raise AssertionError('self-reported health accepted')
 except ValueError:pass
with tempfile.TemporaryDirectory(prefix='operational paths ') as tmp:
 work=Path(tmp);data=json.loads((root/'docs/examples/release-evidence.json').read_text());source=work/'pipeline.json';source.write_text('pipeline reported success');data['attachments']=[{'path':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}];file=work/'input.json';file.write_text(json.dumps(data));out=work/'receipt.json'
 def run(*args):return subprocess.run(['bash',str(root/'bin/taskspec'),'--json',*args],cwd=work,text=True,capture_output=True)
 p=run('--dry-run','receipt','operational','import',str(file),'--out',str(out),'--verify-local');assert p.returncode==0 and not out.exists(),p.stdout
 p=run('receipt','operational','import',str(file),'--out',str(out),'--verify-local');assert p.returncode==0,p.stdout
 receipt=json.loads(out.read_text());assert receipt['target_health_verified'] is False and receipt['acceptance_granted'] is False;assert receipt['attachments'][0]['verification']=='local_digest_verified'
 assert run('receipt','operational','validate',str(out)).returncode==0
 assert run('receipt','operational','import',str(file),'--out',str(out)).returncode!=0
 source.write_text('changed');assert run('receipt','operational','validate',str(file),'--verify-local').returncode!=0
print('TOOLKIT_SDLC=PASS')
PY
