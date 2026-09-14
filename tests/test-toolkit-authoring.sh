#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import copy,json,os,re,subprocess,sys,tempfile
root=Path(sys.argv[1]);sys.path[:0]=[str(root/'src/author'),str(root/'src/recipe'),str(root/'src/security'),str(root/'tests')]
from taskplan import render_spec
from recipes import resolve,validate,STRATEGIES,from_spec
from task_revision import revision
from schema_contracts import validate_instance
from taskspec_data import frontmatter
unit={'id':'T-20260914-recipe','title':'Bounded recipe','effort':'S','profile':'standard','agent':'any','execution_backend':'any','depends_on':[],'touches_paths':['src/file.py'],'creates_paths':[],'source_note':'fixture','why':'Correct one behavior','goal':'Return the expected result','evals':[{'id':'eval_1','description':'expected behavior','command':'test 1 = 1'}]}
legacy=render_spec(unit);assert from_spec(legacy)[0] is None
unit['execution_recipe']='test-first';text=render_spec(unit);recipe=from_spec(text)[0];assert not validate(recipe,['eval_1'],15)
validate_instance(recipe,'task-execution-recipe.schema.json')
# A resolved recipe remains byte-identical when installed strategy guidance changes.
unit['execution_recipe']=copy.deepcopy(recipe);STRATEGIES['test-first']=['changed guidance'];assert render_spec(unit)==text
for field,value in [('max_rounds',16),('no_progress_rounds',4),('runner','other'),('eval_ids',['eval_2']),('required_capabilities',[])]:
 bad=copy.deepcopy(recipe);bad[field]=value;assert validate(bad,['eval_1'],15),field
additional=copy.deepcopy(recipe);additional['required_capabilities'].append('hard_token_budget');assert not validate(additional,['eval_1'],15)
with tempfile.TemporaryDirectory() as tmp:
 spec=Path(tmp)/'task.md';spec.write_text(text);old=revision(spec)['task_revision_digest'];spec.write_text(text.replace('test-first','direct'));assert revision(spec)['task_revision_digest']!=old
 # Exercise the actual direct-authoring scaffold. Its explanatory comments must
 # not become a superseded task ID, an effort suffix, or truthy sign-off text.
 work=Path(tmp);subprocess.run(['git','init','-q',str(work)],check=True)
 env={k:v for k,v in os.environ.items() if k not in ('TASKSPEC_WORKSPACE_ROOT','TASKSPEC_BACKLOG_DIR','TASKSPEC_SIGNING_KEY')}
 for args in [('init',),('new','scaffold','S','any','fixture')]:
  subprocess.run(['bash',str(root/'bin/taskspec'),*args],cwd=work,env=env,check=True,capture_output=True)
 scaffold=next((work/'tasks').glob('T-*-scaffold.md')).read_text()
 parsed=frontmatter(re.sub(r'\{\{[^}]+\}\}','pending',scaffold))
 assert parsed['supersedes']=='(none)' and parsed['effort']=='S'
 assert parsed['profile']=='standard' and parsed['execution_backend']=='any'
 assert parsed['signed_off'] is False and parsed['accepted'] is False
print('TOOLKIT_AUTHORING=PASS')
PY

python3 "$ROOT/spec/conformance/toolkit/check.py"
