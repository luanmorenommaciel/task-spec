#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime="${TASKSPEC_DECOMPOSE_PYTHON:-$ROOT/.taskspec/runtime/decompose/bin/python}"
[[ -x "$runtime" ]] || { echo 'Toolkit tests require taskspec setup decompose' >&2; exit 3; }
"$runtime" - "$ROOT" <<'PY'
from pathlib import Path
import copy,hashlib,json,os,shutil,subprocess,sys,tempfile,yaml
root=Path(sys.argv[1]);cli=Path(os.environ.get('TASKSPEC_TEST_CLI',str(root/'bin/taskspec')))
with tempfile.TemporaryDirectory(prefix='task toolkit ') as temp:
 work=Path(temp).resolve();subprocess.run(['git','init','-q',str(work)],check=True)
 evidence=work/'tests/fixtures/toolkit/blueprint.md';evidence.parent.mkdir(parents=True);shutil.copyfile(root/'tests/fixtures/toolkit/blueprint.md',evidence)
 recipe=yaml.safe_load((root/'tests/fixtures/toolkit/rate-limiting-recipe.yaml').read_text())
 first=recipe['seams'][0]['swimlane']['legs'][0]['tasks'][0];first['execution_recipe']='test-first';first['shared_resources']=['staging-db']
 first['sdlc_stages']=['design','build','test']
 authored=work/'authored.yaml';authored.write_text(yaml.safe_dump(recipe,sort_keys=False))
 env={**os.environ,'TASKSPEC_WORKSPACE_ROOT':str(work),'TASKSPEC_BACKLOG_DIR':str(work/'tasks'),'TASKSPEC_SIGNING_KEY':'isolated-decomposition-test-key'}
 def run(*args,ok=True):
  p=subprocess.run(['bash',str(cli),'--json',*args],env=env,cwd=work,text=True,capture_output=True,timeout=40)
  assert (p.returncode==0)==ok,(args,p.stdout,p.stderr)
  data=json.loads(p.stdout);assert '\x1b' not in p.stdout
  return data['data']
 def digest_tree():return {str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest() for p in work.rglob('*') if p.is_file() and '.git' not in p.parts}
 before=digest_tree();run('--dry-run','decompose','prepare','sample','--recipe',str(authored));assert before==digest_tree()
 # Human-input blockers preserve authored state and do not suggest fabricating
 # decisions to get past an earlier validation stage. Check both public outputs.
 blockers={}
 bad=copy.deepcopy(recipe);bad['decisions'][0]['status']='proposed';blockers['unaccepted_decision']=bad
 bad=copy.deepcopy(recipe);bad['seams'][0]['owner']=' ';blockers['missing_owner']=bad
 bad=copy.deepcopy(recipe);bad['system_map']['unknowns']=['Window semantics require the product owner.'];blockers['architecture_unknown_open']=bad
 for code,bad in blockers.items():
  authored.write_text(yaml.safe_dump(bad,sort_keys=False));before=digest_tree()
  data=run('--dry-run','decompose','prepare','blocked-proposal','--recipe',str(authored),ok=False)
  assert data['code']=='DECOMPOSE_INVALID' and code in data['message'],data
  assert 'responsible human' in data['next'][0] and 'remain unproven' in data['next'][0],data
  assert before==digest_tree()
  human=subprocess.run(['bash',str(cli),'--dry-run','decompose','prepare','blocked-proposal','--recipe',str(authored)],env=env,cwd=work,text=True,capture_output=True,timeout=40)
  assert human.returncode==1 and 'NEXT: Preserve the unresolved' in human.stderr,(human.stdout,human.stderr)
  assert before==digest_tree()
 # Syntax errors still have repair guidance; neither route persists a proposal.
 authored.write_text('schema_version: [');before=digest_tree()
 invalid=run('--dry-run','decompose','prepare','malformed','--recipe',str(authored),ok=False)
 assert 'Correct the reported recipe' in invalid['next'][0] and before==digest_tree()
 authored.write_text(yaml.safe_dump(recipe,sort_keys=False))
 intake=work/'intake.md';intake.write_text('Keep all authentication checks and existing public APIs.')
 run('decompose','init','sample','--intent-file',str(intake))
 assert run('decompose','status','sample')['state']=='intent'
 run('decompose','prepare','sample','--recipe',str(authored))
 pending=run('decompose','status','sample')
 assert pending['state']=='needs_review' and 'decompose review sample' in pending['next'][0]
 folder=work/'tasks/.plans/sample'
 run('decompose','compile','sample',ok=False)
 run('decompose','review','sample','--accept','--reviewer','test-human','--reason','explicit fixture approval')
 review=folder/'reviews/delivery-plan-review.json';saved=review.read_bytes();r=json.loads(saved);r['reviewer']='forged';review.write_text(json.dumps(r));run('decompose','compile','sample',ok=False)
 blocked=run('decompose','status','sample');assert blocked['state']=='blocked' and blocked['diagnostics']
 review.write_bytes(saved)
 reviewed=run('decompose','status','sample');assert reviewed['state']=='reviewed' and reviewed['next']==['taskspec decompose compile sample']
 topology=folder/'proposed-graph.json';old_topology=topology.read_bytes();topology.write_text('{}');run('decompose','compile','sample',ok=False);topology.write_bytes(old_topology)
 intake=folder/'intake.md';old_intake=intake.read_bytes();intake.write_text('Drop the authentication checks.');run('decompose','compile','sample',ok=False);intake.write_bytes(old_intake)
 run('decompose','compile','sample')
 planpath=folder/'task-plan.json';plan=json.loads(planpath.read_text());assert all(u.get('provenance') for u in plan['units'])
 parity=json.loads((root/'tests/fixtures/toolkit/seamwise-parity.json').read_text())
 assert [{key:u[key] for key in parity['fields'] if key in u} for u in plan['units']]==parity['units']
 sys.path.insert(0,str(root/'tests'));from schema_contracts import validate_instance
 validate_instance(json.loads((folder/'bundle.json').read_text()),'task-plan-bundle.schema.json')
 snapshot=json.loads((work/plan['units'][0]['provenance']['snapshot']).read_text());validate_instance(snapshot,'task-plan-snapshot.schema.json');assert 'source-recipe.yaml' in snapshot['reviewed_artifacts']
 validate_instance(plan['units'][0]['provenance'],'task-plan-provenance.schema.json')
 run('plan','--manifest',str(planpath))
 status=run('status','--initiative','sample');assert all(t['lifecycle']=='not_materialized' for t in status['tasks'])
 saved=planpath.read_bytes();plan['units'][0]['goal']='Substituted unit';planpath.write_text(json.dumps(plan));run('plan','--manifest',str(planpath),ok=False);planpath.write_bytes(saved)
 run('batch','--plan',str(planpath))
 spec=work/'tasks'/f'{first["id"]}.md';assert 'execution_recipe:' in spec.read_text();assert 'signed_off: false' in spec.read_text();assert 'Applicable intent' in spec.read_text();assert 'Keep all authentication checks' in spec.read_text()
 result=run('status','--initiative','sample');assert result['accepted_tasks']==[] and len(result['proof_gaps'])==4
 assert result['next'] and all('gate --stamp' in command for command in result['next'])
 assert next(t for t in result['tasks'] if t['id']==first['id'])['sdlc_stages']==['design','build','test']
 # The source bytes and original recipe remain required at their own boundaries.
 source_saved=evidence.read_bytes();evidence.write_text('tampered');run('plan','--manifest',str(planpath),ok=False);evidence.write_bytes(source_saved)
 raw=(folder/'source-recipe.yaml').read_bytes();(folder/'source-recipe.yaml').write_bytes(raw+b'\n# changed\n');run('decompose','compile','sample',ok=False);(folder/'source-recipe.yaml').write_bytes(raw)
 # An unrelated sibling revision preserves the first leaf's authorized projection.
 sys.path.insert(0,str(root/'src/security'));from provenance import verify_task
 prior=json.loads(planpath.read_text());old_unit=next(u for u in prior['units'] if u['id']==first['id']);saved_snapshot=old_unit['provenance']['snapshot']
 previous=work/'previous-bundle.json';previous.write_bytes((folder/'bundle.json').read_bytes())
 recipe['seams'][1]['swimlane']['legs'][0]['tasks'][0]['title']='Resolve one effective policy with explicit evidence'
 authored.write_text(yaml.safe_dump(recipe,sort_keys=False));run('decompose','prepare','sample','--recipe',str(authored),'--replace');run('decompose','review','sample','--accept','--reviewer','test-human','--reason','sibling revision');run('decompose','compile','sample')
 os.environ['TASKSPEC_SIGNING_KEY']=env['TASKSPEC_SIGNING_KEY'];verify_task(work,first['id'],old_unit['provenance']);assert (work/saved_snapshot).exists()
 impact=run('decompose','impact','sample','--against',str(previous));assert first['id'] in impact['unchanged'] and len(impact['changed'])==1
 old_previous=previous.read_bytes();forged=json.loads(old_previous);forged['units']={};previous.write_text(json.dumps(forged));run('decompose','impact','sample','--against',str(previous),ok=False);previous.write_bytes(old_previous)
 # Missing evidence and ownership refuse without a partially created initiative.
 broken=json.loads(json.dumps(recipe));broken['seams'][0]['owner']='';authored.write_text(yaml.safe_dump(broken));run('decompose','prepare','bad','--recipe',str(authored),ok=False);assert not (work/'tasks/.plans/bad').exists()
 # Deterministic rejection of architecture and evidence contradictions.
 cases={}
 bad=copy.deepcopy(recipe);bad['evidence']=[];cases['no-evidence']=bad
 bad=copy.deepcopy(recipe);bad['seams'][0]['swimlane']['id']=bad['seams'][1]['swimlane']['id'];cases['duplicate-lane']=bad
 bad=copy.deepcopy(recipe);bad['seams'][0]['swimlane']['legs'][0]['tasks'][0]['depends_on']=['T-20260802-missing'];cases['missing-dep']=bad
 bad=copy.deepcopy(recipe);bad['seams'][0]['swimlane']['legs'][0]['tasks'][0]['depends_on']=['T-20260802-request-101'];cases['cycle']=bad
 bad=copy.deepcopy(recipe);bad['seams'][1]['swimlane']['legs'][0]['tasks'][0]['depends_on']=[];cases['undeclared-causality']=bad
 bad=copy.deepcopy(recipe);bad['seams'][1]['swimlane']['legs'][0]['tasks'][0]['creates_paths'][0]=first['creates_paths'][0];cases['collision']=bad
 for name,bad in cases.items():
  authored.write_text(yaml.safe_dump(bad,sort_keys=False));run('decompose','prepare',name,'--recipe',str(authored),ok=False);assert not (work/'tasks/.plans'/name).exists()
 # Explicit migration preserves originals, but never copies approval.
 legacy=work/'legacy';legacy.mkdir();(legacy/'source-recipe.yaml').write_text(yaml.safe_dump(recipe,sort_keys=False))
 run('--dry-run','decompose','import','imported','--source',str(legacy));assert not (work/'tasks/.plans/imported').exists()
 run('decompose','import','imported','--source',str(legacy));assert (work/'tasks/.plans/imported/migration/receipt.json').exists();run('decompose','compile','imported',ok=False)
 imported=work/'tasks/.plans/imported';originals={str(p.relative_to(legacy)):p.read_bytes() for p in legacy.rglob('*') if p.is_file()};materialized=spec.read_bytes()
 shutil.rmtree(imported)
 assert {str(p.relative_to(legacy)):p.read_bytes() for p in legacy.rglob('*') if p.is_file()}==originals and spec.read_bytes()==materialized
 unsafe=work/'unsafe';unsafe.mkdir();(unsafe/'source-recipe.yaml').write_text(yaml.safe_dump(recipe));(unsafe/'link').symlink_to(evidence)
 run('decompose','import','unsafe','--source',str(unsafe),ok=False);assert not (work/'tasks/.plans/unsafe').exists()
print('TOOLKIT_DECOMPOSE=PASS')
PY
