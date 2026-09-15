#!/usr/bin/env python3
"""Run registered delivery comparisons; TaskMesh remains the managed executor.

No run is replaced on failure. Setup checks are explicitly outside comparison.
Controller acceptance is exercised under the user's fixed pilot authorization;
its time is never reported as a human engineer's active time.
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
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import yaml
from corpus import recipe,leaves,direct_plan
from providers import argv as provider_argv, usage, permission_denials
from record import append_event,measurement,read_events,run_command
from public_evaluator import install as install_evaluator, verify as verify_evaluator

ROOT=Path(__file__).resolve().parents[3]
PILOT=ROOT/'release/3.10.0/pilot'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')


def setup(args):
    identity=f'{args.scenario}-{args.harness}-{args.workflow}-r{args.repeat}'
    run_id=('setup-' if args.setup_only else 'smoke-' if args.smoke else '')+identity+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    retained=PILOT/('setup-checks' if args.setup_only else 'instrumentation-smoke' if args.smoke else 'runs')/run_id
    retained.mkdir(parents=True,exist_ok=False);journal=retained/'events.jsonl'
    bundle=args.snapshot.resolve();tooling=args.tooling.resolve()
    evaluator=tooling/'tests/evals/toolkit/evaluate_issue.py';cli=tooling/'bin/taskspec'
    temp=Path(tempfile.mkdtemp(prefix='taskspec-pilot-')).resolve()
    with tarfile.open(bundle) as archive:archive.extractall(temp,filter='data')
    work=temp/'task-spec-3.9.0'
    document=json.loads((PILOT/'issues.json').read_text())
    issue=copy.deepcopy(next(i for i in document['issues'] if i['id']==args.scenario));issue['registered_at']=document['registered_at']
    write(work/'tests/fixtures/toolkit/pilot-issue.json',issue)
    evaluator_manifest=install_evaluator(tooling,work)
    model='gpt-6-astra' if args.harness=='codex' else 'claude-opus-5'
    registration={'contract':'TaskToolkitComparisonRun/v1','run_id':run_id,'scenario':args.scenario,'harness':args.harness,'workflow':args.workflow,'repeat':args.repeat,'model':model,'provider':'openai' if args.harness=='codex' else 'anthropic','workspace':str(work),'repository_snapshot':digest(bundle),'tooling':str(tooling),'evaluator_digest':digest(evaluator),'public_evaluator_manifest':evaluator_manifest,'write_scope':issue['write_scope'],'budget':{'max_provider_invocations_per_leaf':3,'total_execution_seconds_per_leaf':600,'no_progress_rounds':2},'intervention_recording_enabled':True,'comparative':not (args.setup_only or args.smoke),'review_authority':'Standing user pilot authorization for the registered fixed scope; controller review is automated and is not a newly observed human intervention.'}
    write(retained/'registration.json',registration);append_event(journal,run_id,'run_started',registration)
    seq=0;denial_evidence=[]
    env=['env','-u','TASKSPEC_WORKSPACE_ROOT','-u','TASKSPEC_BACKLOG_DIR','-u','TASKSPEC_SIGNING_KEY','TASKSPEC_HOME='+str(tooling),'TASKSPEC_DECOMPOSE_PYTHON='+str(args.python.absolute()),'TASKSPEC_MESH_HELPER='+str(args.helper.resolve()),'TASKSPEC_MESH_ADAPTER_DIR='+str(args.adapters.resolve())]
    def command(argv,phase=None,timeout=120,prompt=None,required=True,stop_on_denial=False):
        nonlocal seq
        seq+=1;phase=phase or f'command-{seq:03d}'
        row=run_command(journal,run_id,phase,argv,work,retained,timeout,prompt,stop_on_denial=stop_on_denial)
        if row['data'].get('reported_permission_denial'):
            denial_evidence.append({'source':'command stream observer','phase':phase})
        if required and row['data']['exit_code']!=0:raise RuntimeError(f'{phase} failed; inspect its retained stdout/stderr')
        return row
    def ts(*argv,phase=None,required=True,timeout=180):
        row=command(env+['bash',str(cli),'--json',*map(str,argv)],phase=phase,required=required,timeout=timeout)
        raw=(retained/(row['data']['phase']+'.stdout')).read_text()
        try:return json.loads(raw)
        except ValueError:
            if required:raise
            return {'ok':False,'raw':raw}
    def git(*argv,**kwargs):return command(['git',*argv],**kwargs)
    accepted=False;gold_passed=False;candidate=work;error=None;daemon_pid=None;attempts=[];provider_outputs=[];integration_failures=0
    semantic_ref=None
    try:
        for argv in [('init','-q','-b','main'),('config','user.name','TaskSpec pilot controller'),('config','user.email','pilot@taskspec.invalid'),('add','.'),('commit','-qm','Fixed repository issue snapshot')]:git(*argv)
        ts('init');ts('setup','signing')
        authored=recipe(issue,work,evaluator_manifest,'any' if args.smoke else args.harness)
        if args.workflow=='integrated':
            for seam in authored['seams']:
                for leg in seam['swimlane']['legs']:
                    for unit in leg['tasks']:unit['execution_recipe']='research-synthesize-verify' if args.scenario=='investigation' else 'diagnose-repair-verify'
            authored['seams'][-1]['swimlane']['legs'][-1]['tasks'][-1]['proves_capabilities']=[leg['id'] for seam in authored['seams'] for leg in seam['swimlane']['legs']]
        recipe_path=work/'tasks/.plans/pilot-input.yaml';recipe_path.parent.mkdir(parents=True,exist_ok=True);recipe_path.write_text(yaml.safe_dump(authored,sort_keys=False))
        if args.workflow=='integrated':
            ts('decompose','prepare','pilot','--recipe',recipe_path)
            ts('decompose','review','pilot','--accept','--reviewer','pilot-controller','--reason',registration['review_authority'])
            ts('decompose','compile','pilot');plan=work/'tasks/.plans/pilot/task-plan.json'
        elif args.workflow=='separate-engine':
            if not args.seamwise:raise ValueError('separate-engine requires an explicit pinned Seamwise executable')
            prefix=[str(args.seamwise.resolve()),'--workspace',str(work),'--json']
            for tail in [['init'],['map','--source',str(recipe_path)],['plan'],['review','--accept','--reviewer','pilot-controller','--reason',registration['review_authority']],['compile']]:
                row=command(prefix+tail,required=tail!=['plan'])
                if tail==['plan']:
                    result=json.loads((retained/(row['data']['phase']+'.stdout')).read_text())
                    if result.get('token')!='DELIVERY_PLAN=NEEDS_REVIEW' or result.get('exit_code')!=2:raise ValueError('unexpected separate-engine planning result')
            plan=work/'seamwise/task-plan.json'
        else:
            plan=work/'tasks/.plans/native.json';write(plan,direct_plan(authored))
        ts('plan','--manifest',plan);ts('batch','--plan',plan)
        specs=[]
        for leaf in leaves(issue):
            spec=work/'tasks'/('T-20260914-pilot-'+leaf['slug']+'.md');body=spec.read_text().replace('  timeout_minutes: 30','  timeout_minutes: 10')
            # Old Seamwise has no recipe field. Its existing direct-authoring
            # handoff resolves the same strategy before HMAC, preserving originals.
            if args.workflow=='separate-engine':
                sys.path.insert(0,str(tooling/'src/recipe'));from recipes import resolve
                strategy='research-synthesize-verify' if args.scenario=='investigation' else 'diagnose-repair-verify'
                body=body.replace('  version: 2','  version: 2\n  execution_recipe: '+json.dumps(resolve(strategy,['eval_1','eval_2','eval_3'])))
            spec.write_text(body);ts('gate','--stamp',spec,'--stamp-by','pilot-controller');specs.append(spec)
        git('add','tasks','.taskspec/config')
        if (work/'seamwise').exists():git('add','seamwise','telemetry')
        git('commit','-qm','Authorize fixed pilot contracts before dispatch')
        source_base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=work,text=True).strip()
        registration['authorization_base']=source_base
        write(retained/'prepared.json',{'workspace':str(work),'specs':[str(p.relative_to(work)) for p in specs],'plan':str(plan.relative_to(work)),'leaves':len(specs),'setup_passed':True})
        if not args.setup_only:
            if not args.smoke:
                schedule=json.loads((PILOT/'schedule.json').read_text())
                if schedule.get('status')!='frozen' or identity not in [r['id'] for r in schedule['runs']]:raise ValueError('run is not in the frozen schedule')
                for name,expected in schedule['controller_digests'].items():
                    if digest(ROOT/name)!=expected:raise ValueError('registered controller changed: '+name)
                if any(json.loads(p.read_text()).get('scenario')==args.scenario and json.loads(p.read_text()).get('harness')==args.harness and json.loads(p.read_text()).get('workflow')==args.workflow and json.loads(p.read_text()).get('repeat')==args.repeat for p in (PILOT/'runs').glob('*/result.json')):raise ValueError('comparison cell already observed; retain it instead of replacing it')
            for spec in specs:
                slug=spec.stem.removeprefix('T-20260914-pilot-')
                if args.workflow=='native-harness':
                    handoff=work/'.taskspec/handoffs'/f'{slug}.json'
                    ts('handoff',spec,'--backend',args.harness,'--out',handoff)
                    deadline=time.monotonic()+600;feedback='';previous=None;stalled=0;leaf_pass=False
                    for round_number in range(1,4):
                        prompt=f'Implement the already HMAC-authorized atomic task at {spec}. Read {handoff} and the registered issue evidence first. Modify only the declared write surface. Do not modify contracts, authorize work, commit, self-accept, or spawn agents. Use evidence-based diagnosis, implement, and run all declared evals. Report actual failures. This is invocation {round_number} of at most 3 within one 10-minute task budget. '+feedback
                        if args.smoke:invocation=command([str(args.smoke.absolute())],phase=f'{slug}-provider-{round_number}',timeout=max(1,deadline-time.monotonic()),required=False)
                        else:
                            argv,prompt_stdin=provider_argv(args.harness,work,prompt)
                            invocation=command(argv,phase=f'{slug}-provider-{round_number}',timeout=max(1,deadline-time.monotonic()),prompt=prompt_stdin,required=False,stop_on_denial=True)
                        path=retained/f'{slug}-provider-{round_number}.stdout';provider_outputs.append((str(path.relative_to(PILOT)),path.read_text()))
                        if invocation['data'].get('reported_permission_denial') or permission_denials(path.read_text()):
                            raise RuntimeError('harness permission denial; no repair retry is authorized')
                        verdict=ts('run',spec,phase=f'{slug}-eval-{round_number}',required=False,timeout=max(1,deadline-time.monotonic()))
                        if verdict.get('ok'):leaf_pass=True;break
                        diff=subprocess.check_output(['git','diff','HEAD'],cwd=work)
                        fingerprint=hashlib.sha256(diff+json.dumps(verdict,sort_keys=True).encode()).hexdigest();stalled=stalled+1 if fingerprint==previous else 0;previous=fingerprint
                        feedback='The supervisor evaluation failed: '+json.dumps(verdict)[-12000:]
                        if stalled>=2 or time.monotonic()>=deadline:break
                    if not leaf_pass:raise RuntimeError('native harness exhausted bounded execution before declared evals passed')
                    candidate=work
                else:
                    started=ts('mesh','run','--task',spec.stem,'--adapter','pilot-smoke' if args.smoke else args.harness+'-native','--model',model,'--execute')['data']['data']
                    attempt=started['attempts'][0]['lease']['attempt_id'];attempts.append(attempt)
                    candidate=Path(started['attempts'][0]['workspace'])
                    daemon_pid=ts('mesh','doctor')['data']['data']['daemon_pid']
                    deadline=time.monotonic()+660;prior_state=None;current={}
                    while time.monotonic()<deadline:
                        raw=subprocess.check_output(env+['bash',str(cli),'--json','mesh','status',attempt],cwd=work,text=True)
                        current=next(a for a in json.loads(raw)['data']['data']['attempts'] if a['attempt_id']==attempt)
                        if current['state']!=prior_state:
                            prior_state=current['state'];write(retained/f'{attempt}-{prior_state}.json',json.loads(raw));append_event(journal,run_id,'attempt_state',current)
                        if prior_state in ('awaiting_supervision','parked','cancelled','failed','lost'):break
                        time.sleep(1)
                    if prior_state!='awaiting_supervision':
                        ts('mesh','cancel',attempt,required=False)
                        raise RuntimeError('managed attempt stopped: '+str(prior_state))
                verify_evaluator(candidate,evaluator_manifest)
                if args.scenario=='investigation':
                    report=candidate/'docs/maintainers/recipe-assurance-investigation.md'
                    request={'document':str(report),'sha256':digest(report),'source_root':str(candidate),'required':'Review actual claims against recipe.go, sandbox.go and process.go; structural checks alone are insufficient.'}
                    write(retained/'semantic-review-request.json',request);append_event(journal,run_id,'semantic_review_requested',request)
                    review_path=retained/'semantic-review.json';review_deadline=time.monotonic()+1200
                    while not review_path.exists() and time.monotonic()<review_deadline:time.sleep(1)
                    if not review_path.exists():raise RuntimeError('independent semantic review remains pending')
                    review=json.loads(review_path.read_text())
                    if review.get('sha256')!=request['sha256'] or review.get('passed') is not True or not review.get('claims_checked'):raise RuntimeError('independent semantic review refused the report')
                    semantic_ref=str(review_path.relative_to(PILOT));append_event(journal,run_id,'semantic_review_observed',review)
                if args.workflow=='native-harness':
                    ts('accept','--stamp','--handoff',handoff,'--accepted-by','pilot-controller',spec,timeout=240)
                    git('add','-A');git('commit','-qm','Accept independently evaluated native pilot leaf')
                else:
                    ts('mesh','accept',attempt,'--supervised-by','pilot-controller','--reason','Declared evals passed; fixed pilot scope and independent evidence inspected.',timeout=240)
                    ts('mesh','finish',started['run']['run_id'])
                    # Canonical receipts were copied to the supervisor checkout.
                    # Retain them in Git before the explicit controller-owned merge;
                    # otherwise Git correctly protects the untracked evidence.
                    git('add','.taskspec/acceptance')
                    git('commit','-qm','Retain canonical pilot acceptance before explicit integration')
                    git('merge','--no-ff','--no-edit',started['run']['integration_branch'])
            accepted=True
            result=command([str(args.python.absolute()),str(evaluator),args.scenario,'--root',str(work)],phase='independent-composition-proof',timeout=480,required=False)
            gold_passed=result['data']['exit_code']==0
            if not gold_passed:integration_failures+=1;raise RuntimeError('independent composition proof failed after leaf acceptance')
            accepted=True
    except Exception as exc:
        error=str(exc)
        if not args.setup_only:
            try:
                result=command([str(args.python.absolute()),str(evaluator),args.scenario,'--root',str(candidate)],phase='independent-failure-assessment',timeout=480,required=False)
                gold_passed=result['data']['exit_code']==0
                if args.scenario=='investigation' and not semantic_ref:gold_passed=None
            except Exception as assessment_error:
                gold_passed=None;error+='; independent assessment unavailable: '+str(assessment_error)
    finally:
        if not accepted:
            for attempt in attempts:
                try:ts('mesh','cancel',attempt,required=False)
                except Exception:pass
        if not daemon_pid and (work/'.taskspec/mesh/mesh.db').exists():
            try:daemon_pid=ts('mesh','doctor')['data']['data']['daemon_pid']
            except Exception:pass
        if daemon_pid:
            try:os.kill(daemon_pid,signal.SIGTERM)
            except ProcessLookupError:pass
    artifacts=work/'.taskspec/mesh/artifacts'
    if artifacts.exists():
        shutil.copytree(artifacts,retained/'mesh-artifacts',dirs_exist_ok=True)
        for path in sorted((retained/'mesh-artifacts').glob('*.json')):
            item=json.loads(path.read_text())
            if item.get('error_code')=='EXECUTOR_PERMISSION_DENIED':
                denial_evidence.append({'source':'TaskMesh stream observer','artifact':str(path.relative_to(PILOT))})
            if item.get('contract')=='TaskMeshAdapterArtifact/v1' and '.round-' in path.name:provider_outputs.append((str(path.relative_to(PILOT)),item.get('output','')))
    for name in ['tasks','.taskspec/acceptance','.taskspec/handoffs']:
        if (work/name).exists():shutil.copytree(work/name,retained/'workspace-evidence'/name,dirs_exist_ok=True)
    command(['git','diff',registration.get('authorization_base','HEAD'),'--',*issue['write_scope']],phase='candidate-patch',required=False)
    command(['git','status','--short'],phase='final-workspace-status',required=False)
    append_event(journal,run_id,'run_finished',{'accepted':accepted,'gold_passed':gold_passed,'error':error,'setup_only':args.setup_only})
    result={**registration,'setup_passed':(retained/'prepared.json').is_file(),'accepted':accepted,'error':error,'measurement':measurement(read_events(journal),run_id)}
    observed=result['measurement'];cost=usage(args.harness,provider_outputs);write(retained/'cost.json',cost)
    result.update(observed);result.update(accepted=accepted,gold_passed=gold_passed,integration_failures=integration_failures,replanning_churn=0,false_acceptances=int(accepted and gold_passed is False),acceptance_correctness=int(accepted==gold_passed) if type(gold_passed) is bool else None,failed_attempts_retained=True,harness_version='0.154.0' if args.harness=='codex' else '2.1.270',strategy_version='1.0.0',permissions_digest=hashlib.sha256(json.dumps(issue['write_scope'],sort_keys=True).encode()).hexdigest(),cost_including_failures=cost['cost_including_failures'],cost_basis=cost['cost_basis'],cost_evidence=str((retained/'cost.json').relative_to(PILOT)),semantic_review_ref=semantic_ref,journal=str(journal.relative_to(PILOT)))
    result['reported_permission_denials']=denial_evidence+[denial for _,output in provider_outputs for denial in permission_denials(output)]
    result['evidence_refs']=[{'path':str(p.relative_to(PILOT)),'sha256':digest(p)} for p in sorted(retained.rglob('*')) if p.is_file() and p.name!='result.json']
    write(retained/'result.json',result);print(json.dumps(result,indent=2))
    return 0 if error is None else 1


def main():
    global PILOT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot-dir',type=Path,default=PILOT,
                        help='Explicit independent cohort directory; previous observations are never replaced')
    parser.add_argument('--scenario',required=True,choices=['small-fix','cross-seam','investigation','contention','incident','release-evidence'])
    parser.add_argument('--harness',required=True,choices=['codex','claude'])
    parser.add_argument('--workflow',required=True,choices=['integrated','separate-engine','native-harness'])
    parser.add_argument('--smoke',type=Path,help='Explicit synthetic worker; excluded from comparative cells');parser.add_argument('--repeat',type=int,default=1);parser.add_argument('--setup-only',action='store_true')
    parser.add_argument('--snapshot',type=Path,required=True);parser.add_argument('--tooling',type=Path,default=ROOT)
    parser.add_argument('--python',type=Path,default=ROOT/'.taskspec/runtime/decompose/bin/python')
    parser.add_argument('--helper',type=Path,default=ROOT/'.taskspec/pilot/bin/taskspec-meshd')
    parser.add_argument('--adapters',type=Path,default=ROOT/'.taskspec/pilot/adapters')
    parser.add_argument('--seamwise',type=Path)
    args=parser.parse_args();PILOT=args.pilot_dir.resolve()
    return setup(args)

if __name__=='__main__':raise SystemExit(main())
