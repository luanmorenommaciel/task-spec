#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import json,re,sys
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'tests/evals/toolkit'))
from chat_score import score,CASES
assert (root/'SKILL.md').read_bytes()==(root/'skills/task-spec/SKILL.md').read_bytes()
claude=json.loads((root/'harness/mesh-adapters/claude-native.json').read_text());assert '--verbose' in claude['command']
for parent in [root,root/'skills/task-spec']:
 for link in re.findall(r'\]\(([^)]+)\)',(parent/'SKILL.md').read_text()):assert (parent/link).is_file(),link
for case in CASES.values():
 trace={'case':case['id'],'actions':case['required'],'evidence_refs':['synthetic-test-only']};assert score(trace)['passed']
 assert not score({**trace,'actions':trace['actions'][1:]})['passed']
 assert not score({**trace,'false_completion':True})['passed']
 if case['forbidden']:assert not score({**trace,'actions':trace['actions']+case['forbidden']})['passed']
from pilot import evaluate
assert evaluate({'runs':[]})['qualified'] is False
from pilot import SCENARIOS,WORKFLOWS,HARNESS
rows=[]
for scenario in SCENARIOS:
 for workflow in WORKFLOWS:
  for harness in HARNESS:
   for repeat in (1,2):
    rows.append(dict(scenario=scenario,workflow=workflow,harness=harness,repeat=repeat,model='synthetic',provider='fixture',harness_version='test',strategy_version='test',failed_attempts_retained=True,repository_snapshot='fixture',budget=10,permissions_digest='fixture',evaluator_digest='fixture',engineer_active_seconds=1 if workflow=='integrated' else 2,accepted_capability_seconds=2,elapsed_seconds=2,accepted=True,gold_passed=True,censored=False,cost_including_failures=0,integration_failures=0,replanning_churn=0,false_acceptances=0,acceptance_correctness=1,evidence_refs=['synthetic-only']))
assert evaluate({'runs':rows})['qualified']
import copy
bad=copy.deepcopy(rows);bad.append(bad[0]);assert not evaluate({'runs':bad})['qualified']
bad=copy.deepcopy(rows);bad[0]['engineer_active_seconds']=float('nan');assert not evaluate({'runs':bad})['qualified']
bad=copy.deepcopy(rows);next(r for r in bad if r['workflow']=='integrated')['acceptance_correctness']=0;assert not evaluate({'runs':bad})['qualified']
bad=copy.deepcopy(rows)
for row in bad:
 if row['workflow']=='integrated': row.update(accepted=False,gold_passed=False,censored=True,accepted_capability_seconds=None)
result=evaluate({'runs':bad});assert not result['qualified'] and result['state']=='evaluated'
assert result['medians']['integrated']['accepted_capability_seconds'] is None
from pilot import verify_evidence
assert verify_evidence({'runs':rows},root), 'arithmetic-only synthetic rows were treated as release evidence'
bad=copy.deepcopy(rows);bad[0]['failed_attempts_retained']='yes';assert not evaluate({'runs':bad})['qualified']
print('TOOLKIT_EXPERIENCE=PASS static resources and trace-oracle negatives; live chat quality not inferred')
PY
