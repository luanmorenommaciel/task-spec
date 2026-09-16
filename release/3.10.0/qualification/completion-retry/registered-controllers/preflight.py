#!/usr/bin/env python3
"""Preflight a pinned harness on a real, isolated, HMAC-authorized repository issue.

This establishes instrumentation and provider readiness. It is explicitly outside
comparative cells: the full corpus/evaluators/order must be frozen before those run.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import tempfile
import time
from record import append_event,measurement,read_events,run_command

ROOT=Path(__file__).resolve().parents[3]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harness',choices=['codex','claude'],required=True)
    args=parser.parse_args()
    issue='small-fix';stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run_id=f'preflight-{args.harness}-{stamp}'
    retained=ROOT/'release/3.10.0/pilot/preflight'/run_id;retained.mkdir(parents=True)
    journal=retained/'events.jsonl'
    snapshot=ROOT/'.taskspec/pilot/snapshot/task-spec-3.9.0.tar.gz'
    workspace=Path(tempfile.mkdtemp(prefix='taskspec-real-issue-')).resolve()
    with tarfile.open(snapshot) as archive:archive.extractall(workspace,filter='data')
    work=workspace/'task-spec-3.9.0'
    reproduction=work/'tests/fixtures/toolkit/pilot-reproduction.json'
    reproduction.write_bytes((ROOT/'release/3.10.0/pilot/reproductions.json').read_bytes())
    cli=ROOT/'bin/taskspec';evaluator=ROOT/'tests/evals/toolkit/evaluate_issue.py'
    model='gpt-6-astra' if args.harness=='codex' else 'claude-opus-5'
    registration={'run_id':run_id,'qualification':'instrumentation_preflight_only','scenario':issue,'harness':args.harness,
                  'model':model,'provider':'openai' if args.harness=='codex' else 'anthropic','workspace':str(work),
                  'repository_snapshot':hashlib.sha256(snapshot.read_bytes()).hexdigest(),
                  'write_scope':['src/recipe/recipes.py'],'evaluator_sha256':hashlib.sha256(evaluator.read_bytes()).hexdigest(),
                  'budget':{'provider_invocations':1,'provider_timeout_seconds':360},
                  'intervention_recording_enabled':True,'setup_outside_comparative_cells':True}
    (retained/'registration.json').write_text(json.dumps(registration,indent=2)+'\n')
    append_event(journal,run_id,'run_started',registration)
    sequence=0;accepted=False;error=None
    def command(argv,phase=None,timeout=120,prompt=None,required=True):
        nonlocal sequence
        sequence+=1;phase=phase or f'setup-{sequence:02d}'
        row=run_command(journal,run_id,phase,argv,work,retained,timeout,prompt)
        if required and row['data']['exit_code']!=0:raise RuntimeError(f'{phase} failed; retained command output contains details')
        return row
    try:
        for argv in [['git','init','-q','-b','main'],['git','config','user.name','TaskSpec pilot supervisor'],['git','config','user.email','pilot@taskspec.invalid'],['git','add','.'],['git','commit','-qm','Register fixed repository issue snapshot']]:command(argv)
        command(['bash',str(cli),'init']);command(['bash',str(cli),'setup','signing'])
        unit=copy.deepcopy(json.loads((ROOT/'tasks/.plans/toolkit-release.json').read_text())['units'][0])
        unit.update(id='T-20260914-pilot-stdin',title='Validate resolved recipes from standard input',effort='S',agent=args.harness,
                    execution_backend=args.harness,depends_on=[],touches_paths=['src/recipe/recipes.py'],creates_paths=[],
                    why='A valid recipe piped to the documented CLI workflow is currently treated as a filename named dash.',
                    goal='Support recipe validate - for valid standard-input JSON while preserving file validation and rejecting malformed or invalid input.',
                    context='The user authorized a prospective real-repository-issue pilot. This isolated preflight uses one pinned provider invocation and does not count as a comparative run. The supervisor authorized only the declared Python file. Preserve all existing validation rules. Do not alter tests, specs, authorization, or signing material.',
                    source_note='Registered reproduction: tests/fixtures/toolkit/pilot-reproduction.json recipe-stdin',
                    do_not_touch=['spec','tests','tasks'])
        unit['behaviors']=[{'id':'B-1','given':'a valid recipe on stdin or in a file','when':'recipe validate is invoked','then':'validation succeeds, while malformed and invalid documents fail with actionable diagnostics'}]
        unit['evals']=[{'id':'eval_1','description':'Independent stdin, file, malformed-input, and validation-rule regressions',
                        'command':shlex.join([sys.executable,str(evaluator),issue,'--root','.']),'verifies':['B-1'],'terminal':True,'expected_duration_sec':30}]
        plan=work/'tasks/.plans/pilot.json';plan.parent.mkdir(parents=True,exist_ok=True)
        plan.write_text(json.dumps({'api_version':'taskspec.dev/v1','kind':'TaskPlan','metadata':{'name':'pilot-preflight'},'approved':True,'units':[unit]},indent=2)+'\n')
        command(['bash',str(cli),'batch','--plan',str(plan)])
        spec=work/'tasks/T-20260914-pilot-stdin.md'
        command(['bash',str(cli),'gate','--stamp',str(spec),'--stamp-by','pilot-supervisor'])
        command(['git','add','tasks','.taskspec/config']);command(['git','commit','-qm','Authorize one bounded pilot task'])
        handoff=work/'.taskspec/handoffs/pilot.json'
        command(['bash',str(cli),'handoff',str(spec),'--backend',args.harness,'--out',str(handoff)])
        prompt=f'''Implement only the HMAC-authorized task at {spec}. Read {handoff} first and verify its scope. This is an isolated real-repository-issue pilot. The task is already authorized by the pilot supervisor; do not ask to authorize it again. Modify only src/recipe/recipes.py. Run the declared evaluator; do not change tests or suppress validation errors. Do not commit, self-accept, or spawn agents. Stop with the actual result and any unresolved blocker. Use the task contract and source evidence, not unrelated global workflows.'''
        if args.harness=='codex':
            argv=['codex','exec','--ignore-user-config','--ephemeral','--sandbox','workspace-write','--cd',str(work),'--json','--color','never','--model',model,'-c','model_reasoning_effort="high"','-c','model_context_window=262144','-c','model_auto_compact_token_limit=196608','-c','service_tier="default"','-']
            command(argv,phase='provider-1',timeout=360,prompt=prompt,required=False)
        else:
            argv=['claude','-p',prompt,'--model',model,'--output-format','stream-json','--verbose','--no-session-persistence','--permission-mode','acceptEdits','--permission-prompts','none','--allowedTools','Read,Edit,Write,Bash','--restricted','--tools','Read,Edit,Write,Bash','--strict-mcp-config','--mcp-config','{"mcpServers":{}}']
            command(argv,phase='provider-1',timeout=360,required=False)
        result=command([sys.executable,str(evaluator),issue,'--root',str(work)],phase='independent-evaluation',required=False)
        if result['data']['exit_code']==0:
            command(['bash',str(cli),'accept','--stamp','--handoff',str(handoff),'--accepted-by','pilot-supervisor',str(spec)],phase='canonical-acceptance',timeout=120)
            accepted=True
    except Exception as exc:
        error=str(exc)
    command(['git','diff','--','src/recipe/recipes.py'],phase='candidate-patch',required=False)
    command(['git','status','--short'],phase='workspace-status',required=False)
    append_event(journal,run_id,'run_finished',{'accepted':accepted,'error':error,'comparative_qualified':False})
    result={**registration,'accepted':accepted,'error':error,'measurement':measurement(read_events(journal),run_id),
            'retained_evidence':str(retained),'raw_provider_output_retained':(retained/'provider-1.stdout').is_file()}
    (retained/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if accepted else 1

if __name__=='__main__':raise SystemExit(main())
