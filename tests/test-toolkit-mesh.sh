#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
(cd "$ROOT" && go test ./mesh/internal/mesh)
"${TASKSPEC_DECOMPOSE_PYTHON:-$ROOT/.taskspec/runtime/decompose/bin/python}" - "$ROOT" <<'PY'
from pathlib import Path
import json,os,signal,subprocess,sys,tempfile,time,yaml,shutil
root=Path(sys.argv[1]);sys.path[:0]=[str(root/'src/author'),str(root/'src/recipe'),str(root/'src/graph')]
from recipes import resolve
from task_graph import build
with tempfile.TemporaryDirectory(prefix='toolkit mesh ') as temporary:
 base=Path(temporary).resolve();work=base/'repo';work.mkdir();cli=root/'bin/taskspec';helper=base/'mesh-helper';adapters=base/'adapters';adapters.mkdir()
 env={**os.environ,'TASKSPEC_MESH_HELPER':str(helper),'TASKSPEC_MESH_ADAPTER_DIR':str(adapters)}
 env.pop('TASKSPEC_WORKSPACE_ROOT',None);env.pop('TASKSPEC_BACKLOG_DIR',None);env.pop('TASKSPEC_SIGNING_KEY',None)
 def cmd(*args,ok=True):
  p=subprocess.run(list(args),cwd=work,env=env,text=True,capture_output=True,timeout=90)
  assert (p.returncode==0)==ok,(args,p.stdout,p.stderr)
  return p.stdout
 def ts(*args,ok=True):return json.loads(cmd('bash',str(cli),'--json',*args,ok=ok))
 for args in [('init','-q','-b','main'),('config','user.name','fixture'),('config','user.email','fixture@example.invalid')]:cmd('git',*args)
 (work/'a.txt').write_text('');(work/'b.txt').write_text('');cmd('git','add','.');cmd('git','commit','-qm','fixture')
 ts('init');ts('setup','signing')
 original=(root/'tests/fixtures/T-20260603-stamp-then-verify.md').read_text()
 for slug,file in [('contender','b.txt')]:
  text=original.replace('T-20260603-stamp-then-verify','T-20260914-'+slug).replace('  - README.md','  - '+file).replace("  ! grep -q 'NEVERMATCH' README.md",'  test "$(cat '+file+')" = completed')
  text=text.replace('depends_on: []','depends_on: []\nshared_resources: [test-database]')
  if slug=='recipe':text=text.replace('  version: 2','  version: 2\n  execution_recipe: '+json.dumps(resolve('diagnose-repair-verify',['eval_1'])))
  spec=work/'tasks'/('T-20260914-'+slug+'.md');spec.write_text(text);ts('gate','--stamp',str(spec))
 # Native intent -> reviewed bundle -> materialized leaf -> managed attempt.
 evidence=work/'tests/fixtures/toolkit/blueprint.md';evidence.parent.mkdir(parents=True);shutil.copyfile(root/'tests/fixtures/toolkit/blueprint.md',evidence)
 recipe=yaml.safe_load((root/'tests/fixtures/toolkit/rate-limiting-recipe.yaml').read_text());recipe['seams']=recipe['seams'][:1];recipe['steel_thread']=recipe['steel_thread'][:1]
 recipe['intent']['summary']='Complete a bounded output artifact while preserving the existing file boundary.';recipe['intent']['success']=['a.txt contains completed and b.txt remains unchanged']
 seam=recipe['seams'][0];seam['responsibility']='Own the completion artifact';seam['produces']=['completed artifact'];seam['independent_proof']='Read the artifact and verify its exact bytes.'
 leg=seam['swimlane']['legs'][0];leg['observable_state']='The completion artifact contains its accepted value';leg['proof']='Exact output and untouched sibling checks pass.';leg['produces']=['completed artifact']
 leaf=leg['tasks'][0];leaf.update(id='T-20260914-recipe',title='Complete the output artifact',goal='Write the accepted completion value inside one file.',done_condition='a.txt contains completed and b.txt is unchanged.',required_tools=['bash'],touches_paths=['a.txt'],creates_paths=[],execution_recipe='diagnose-repair-verify',shared_resources=['test-database'])
 checks=['test "$(cat a.txt)" = completed','test "$(wc -c < a.txt | tr -d \' \')" = 9','test ! -s b.txt']
 for item,check in zip(leaf['evals'],checks):item['bash']=check
 authored=work/'authored.yaml';authored.write_text(yaml.safe_dump(recipe,sort_keys=False))
 ts('decompose','prepare','managed','--recipe',str(authored));ts('decompose','review','managed','--accept','--reviewer','fixture-human','--reason','Explicit synthetic contract review');ts('decompose','compile','managed')
 ts('batch','--plan',str(work/'tasks/.plans/managed/task-plan.json'));ts('gate','--stamp',str(work/'tasks/T-20260914-recipe.md'))
 graph=build(work/'tasks');assert any(e['overlaps']==[{'left':'resource:test-database','right':'resource:test-database'}] for e in graph['write_conflicts'])
 assert all(len(g)<=1 for g in graph['concurrency_groups'])
 cmd('git','add','tasks','tests');cmd('git','commit','-qm','authorize fixture');head=cmd('git','rev-parse','HEAD')
 fake=base/'fake.sh';fake.write_text('''#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == --version ]]; then echo fake/1; exit 0; fi
[[ -z "${TASKSPEC_SIGNING_KEY:-}" ]]
if [[ ! -s a.txt ]]; then printf 'repairing' > a.txt; else printf 'completed' > a.txt; fi
''');fake.chmod(0o755)
 (adapters/'fake.json').write_text(json.dumps({'contract':'TaskMeshAdapter/v1','name':'fake','harness':'custom','executable':str(fake),'version_args':['--version'],'prompt_mode':'argument','event_format':'text','assurance_modes':['supervised'],'command':['run']}))
 subprocess.run(['go','build','-o',str(helper),'./mesh/cmd/taskspec-meshd'],cwd=root,check=True)
 try:
  started=ts('mesh','run','--initiative','managed','--adapter','fake','--execute')['data']['data']
  attempt=started['attempts'][0]['lease']['attempt_id']
  state=''
  for _ in range(100):
   value=ts('mesh','status',attempt)['data']['data'];state=next(a['state'] for a in value['attempts'] if a['attempt_id']==attempt)
   if state in ('parked','awaiting_supervision','cancelled'):break
   time.sleep(.15)
  if state!='awaiting_supervision':
   print(ts('mesh','watch',started['run']['run_id']),file=sys.stderr)
  assert state=='awaiting_supervision',state
  import sqlite3
  with sqlite3.connect(work/'.taskspec/mesh/mesh.db') as con: assert con.execute('SELECT used FROM recipe_budgets').fetchone()[0]==2
  artifacts=list((work/'.taskspec/mesh/artifacts').glob('*.round-*.evals.json'));assert len(artifacts)==2
  assert (work/'a.txt').read_text()=='' and cmd('git','rev-parse','HEAD')==head
  assert 'accepted: true' not in (work/'tasks/T-20260914-recipe.md').read_text()
  ts('mesh','accept',attempt,'--supervised-by','fixture-human','--reason','verified two-round repair fixture')
  assert ts('mesh','status',attempt)['data']['data']['attempts'][0]['state']=='integrated'
 finally:
  try:
   pid=ts('mesh','doctor')['data']['data']['daemon_pid'];os.kill(pid,signal.SIGTERM)
  except Exception:pass
print('TOOLKIT_MESH=PASS')
PY
