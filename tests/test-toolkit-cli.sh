#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
import json,os,re,subprocess,sys,tempfile
from pathlib import Path
root=Path(sys.argv[1]);cli=root/'bin/taskspec';registry=json.loads((root/'src/cli/commands.json').read_text())
context=json.loads(subprocess.check_output(['bash',str(cli),'agent-context'],text=True));assert context['commands']==registry;assert {'task_plan_snapshot','task_execution_recipe','task_operational_evidence'} <= context['contracts'].keys()
source=cli.read_text()
for command in {key.split()[0] for key in registry}:
 assert re.search(r'\b'+re.escape(command)+r'(?:\||\))',source),command
 for args in [['help',command],['--json','help',command]]:
  p=subprocess.run(['bash',str(cli),*args],capture_output=True,text=True,timeout=5);assert p.returncode==0,(args,p.stderr)
  if '--json' in args:assert json.loads(p.stdout)['ok'] and '\x1b' not in p.stdout
for shell in ['bash','zsh','fish']:
 completion=subprocess.check_output(['bash',str(cli),'completion',shell],text=True)
 assert all(word in completion for word in ['decompose','recipe','--initiative' if shell!='fish' else 'initiative','review','prepare'])
 if shell=='bash':
  subprocess.run(['/bin/bash','-n'],input=completion,text=True,check=True)
  script=completion+'\nCOMP_WORDS=(taskspec --json decompose prepare sample --r); COMP_CWORD=5; _taskspec_complete; printf "%s\\n" "${COMPREPLY[@]}"\n'
  result=subprocess.check_output(['/bin/bash'],input=script,text=True);assert '--recipe' in result and '--replace' in result,result
for args in [['decompose','review','example'],['decompose','init','../bad','--intent-file','-'],['recipe','validate','/does-not-exist']]:
 p=subprocess.run(['bash',str(cli),'--json',*args],input='',text=True,capture_output=True,timeout=5);assert p.returncode!=0;assert json.loads(p.stdout)['ok'] is False
with tempfile.TemporaryDirectory(prefix='CLI output ') as temp:
 path=Path(temp)/'recipe file.json'
 subprocess.run(['bash',str(cli),'example','recipe','--out',str(path)],check=True,capture_output=True)
 assert subprocess.run(['bash',str(cli),'recipe','validate',str(path)],capture_output=True).returncode==0
recipe=json.loads(subprocess.check_output(['bash',str(cli),'recipe','show','direct'],text=True))
for content in (json.dumps(recipe),):
 result=subprocess.run(['bash',str(cli),'--json','recipe','validate','-'],input=content,text=True,capture_output=True)
 assert result.returncode==0 and json.loads(result.stdout)['ok'],result.stdout
for content in ('', '{broken', '{"strategy":"direct","strategy":"other"}', 'NaN', 'null'):
 result=subprocess.run(['bash',str(cli),'--json','recipe','validate','-'],input=content,text=True,capture_output=True)
 assert result.returncode!=0 and not json.loads(result.stdout)['ok']
 assert 'Traceback' not in result.stdout+result.stderr
with tempfile.TemporaryDirectory(prefix='CLI dry run ') as temp:
 work=Path(temp);spec=work/'T-20260602-golden.md'
 spec.write_text((root/'tests/fixtures/T-20260602-golden.md').read_text().replace('eval_1() {','eval_1() {\n  printf observed > eval-was-run.txt'))
 (work/'README.md').write_text('Synthetic eval fixture\n')
 before={p.name:p.read_bytes() for p in work.iterdir()}
 for verb in ('gate','accept'):
  result=subprocess.run(['bash',str(cli),'--dry-run',verb,str(spec)],cwd=work,text=True,capture_output=True)
  assert result.returncode==0 and 'DRY_RUN' in result.stdout,(verb,result.stdout,result.stderr)
  assert {p.name:p.read_bytes() for p in work.iterdir()}==before,verb+' dry-run executed an eval or wrote state'
 for verb in ('doctor','frontier','status','watch','explain','adapters'):
  result=subprocess.run(['bash',str(cli),'--json','--dry-run','mesh',verb],cwd=work,text=True,capture_output=True)
  assert result.returncode==0,(verb,result.stdout,result.stderr)
  data=json.loads(result.stdout)['data'];assert data['contract']=='TaskMeshDryRun/v1'
  assert data['would_mutate'] is None and data['may_initialize_runtime'] is True
  assert {p.name:p.read_bytes() for p in work.iterdir()}==before,verb+' dry-run initialized runtime state'
 # Positive control: the fixture really has an executable side effect.
 subprocess.run(['git','init','-q',str(work)],check=True,capture_output=True)
 result=subprocess.run(['bash',str(cli),'run','--ci',str(spec)],cwd=work,text=True,capture_output=True)
 assert (work/'eval-was-run.txt').exists(),(result.stdout,result.stderr)
 assert (work/'eval-was-run.txt').read_text()=='observed'
print('TOOLKIT_CLI=PASS')
PY
