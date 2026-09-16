#!/usr/bin/env python3
"""Compare measured pilot runs and refuse missing or unmatched evidence."""
import json
import hashlib
import math
from pathlib import Path
import statistics
import sys

SCENARIOS={'small-fix','cross-seam','investigation','contention','incident','release-evidence'}
WORKFLOWS={'separate-engine','integrated','native-harness'}
HARNESS={'codex','claude'}
def evaluate(data):
    rows=data.get('runs',[]);gaps=[]
    if not isinstance(rows,list):return {'contract':'TaskToolkitPilot/v1','qualified':False,'state':'incomplete','gaps':['runs must be a list']}
    identities=set()
    for index,row in enumerate(rows):
        if not isinstance(row,dict):
            return {'contract':'TaskToolkitPilot/v1','qualified':False,'state':'incomplete','gaps':[f'run {index}: must be an object']}
        if row.get('scenario') not in SCENARIOS or row.get('workflow') not in WORKFLOWS or row.get('harness') not in HARNESS:gaps.append(f'run {index}: unknown comparison dimension')
        identity=(row.get('scenario'),row.get('harness'),row.get('workflow'),str(row.get('repeat')))
        if type(row.get('repeat')) is not int or row['repeat']<1 or identity in identities:gaps.append(f'run {index}: missing or duplicate positive repeat identifier')
        identities.add(identity)
        for field in ('model','provider','harness_version','strategy_version'):
            if not isinstance(row.get(field),str) or not row[field].strip():gaps.append(f'run {index}: missing {field}')
        if row.get('failed_attempts_retained') is not True:gaps.append(f'run {index}: failed-attempt retention is not established')
    for scenario in sorted(SCENARIOS):
        for harness in sorted(HARNESS):
            group=[r for r in rows if r.get('scenario')==scenario and r.get('harness')==harness]
            for workflow in sorted(WORKFLOWS):
                subset=[r for r in group if r.get('workflow')==workflow]
                if len(subset)<2:gaps.append(f'{scenario}/{harness}/{workflow}: needs at least two repeats')
            repeats=[{r.get('repeat') for r in group if r.get('workflow')==w and type(r.get('repeat')) is int} for w in sorted(WORKFLOWS)]
            if any(value!=repeats[0] for value in repeats[1:]):gaps.append(f'{scenario}/{harness}: unmatched repeats')
            for field in ['repository_snapshot','budget','permissions_digest','evaluator_digest']:
                if not group or any(r.get(field) is None for r in group) or len({json.dumps(r.get(field),sort_keys=True) for r in group})!=1:gaps.append(f'{scenario}/{harness}: unmatched {field}')
    metrics=['engineer_active_seconds','cost_including_failures','integration_failures','replanning_churn','false_acceptances','acceptance_correctness']
    for index,row in enumerate(rows):
        for field in metrics:
            if type(row.get(field)) not in (int,float) or not math.isfinite(row[field]) or row[field]<0:gaps.append(f'run {index}: missing measured {field}')
        if type(row.get('accepted')) is not bool or type(row.get('gold_passed')) is not bool:
            gaps.append(f'run {index}: explicit acceptance and independent evaluation verdicts required')
        elif row.get('false_acceptances') != int(row['accepted'] and not row['gold_passed']):
            gaps.append(f'run {index}: false-acceptance count contradicts verdicts')
        if type(row.get('elapsed_seconds')) not in (int,float) or not math.isfinite(row['elapsed_seconds']) or row['elapsed_seconds'] < 0:
            gaps.append(f'run {index}: missing observed elapsed duration')
        duration=row.get('accepted_capability_seconds')
        if row.get('accepted') is True:
            if type(duration) not in (int,float) or not math.isfinite(duration) or duration < 0:
                gaps.append(f'run {index}: accepted delivery lacks observed completion duration')
        elif duration is not None or row.get('censored') is not True:
            gaps.append(f'run {index}: unsuccessful delivery must retain censored elapsed time')
        if isinstance(row.get('acceptance_correctness'),(int,float)) and row['acceptance_correctness']>1:gaps.append(f'run {index}: acceptance correctness must be in [0,1]')
        if not row.get('evidence_refs'):gaps.append(f'run {index}: missing raw evidence')
    if gaps:return {'contract':'TaskToolkitPilot/v1','qualified':False,'state':'incomplete','gaps':gaps}
    summary={w:{m:statistics.median([r[m] for r in rows if r['workflow']==w]) for m in metrics} for w in WORKFLOWS}
    # Conservative completion medians include failed delivery as unbounded.
    # Never silently discard failures or substitute their shorter timeout.
    for workflow in WORKFLOWS:
        group=[r for r in rows if r['workflow']==workflow]
        median=statistics.median(r['accepted_capability_seconds'] if r['accepted'] else math.inf for r in group)
        summary[workflow]['accepted_capability_seconds']=median if math.isfinite(median) else None
        summary[workflow]['delivery_success_rate']=statistics.mean(r['accepted'] and r['gold_passed'] for r in group)
    integrated=summary['integrated'];separate=summary['separate-engine']
    times=['engineer_active_seconds','accepted_capability_seconds']
    identifiable=all(integrated[t] is not None and separate[t] is not None for t in times)
    improves=identifiable and all(integrated[t]<=separate[t] for t in times) and any(integrated[t]<separate[t] for t in times)
    no_false=all(r['false_acceptances']==0 for r in rows)
    quality=all(statistics.mean(r['acceptance_correctness'] for r in rows if r['scenario']==s and r['harness']==h and r['workflow']=='integrated')>=statistics.mean(r['acceptance_correctness'] for r in rows if r['scenario']==s and r['harness']==h and r['workflow']=='separate-engine') for s in SCENARIOS for h in HARNESS)
    quality=quality and all(statistics.mean(r['accepted'] and r['gold_passed'] for r in rows if r['scenario']==s and r['harness']==h and r['workflow']=='integrated')>=statistics.mean(r['accepted'] and r['gold_passed'] for r in rows if r['scenario']==s and r['harness']==h and r['workflow']=='separate-engine') for s in SCENARIOS for h in HARNESS)
    return {'contract':'TaskToolkitPilot/v1','qualified':no_false and quality and improves,'state':'evaluated','no_false_acceptance':no_false,'quality_nonregression':quality,'productivity_improved':improves,'medians':summary,'gaps':[]}
def verify_evidence(data, root):
    """The public scorer verifies retained artifacts and prospective timing.

    Pure evaluate() remains a metric-only unit-test surface. Its arithmetic is
    never sufficient release evidence on its own.
    """
    from record import read_events,measurement
    gaps=[]
    for index,row in enumerate(data.get('runs',[])):
        refs=row.get('evidence_refs',[])
        if not refs:gaps.append(f'run {index}: no evidence references');continue
        for ref in refs:
            if not isinstance(ref,dict) or set(ref)!={'path','sha256'}:
                gaps.append(f'run {index}: evidence requires exact path and sha256');continue
            try:
                path=Path(ref['path'])
                if path.is_absolute() or '..' in path.parts:raise ValueError('evidence path must be portable and relative')
                resolved=(root/path).resolve()
                if not resolved.is_relative_to(root.resolve()):raise ValueError('evidence escapes retained release directory')
                if hashlib.sha256(resolved.read_bytes()).hexdigest()!=ref['sha256']:raise ValueError('evidence bytes changed')
            except (OSError,ValueError,TypeError) as error:gaps.append(f'run {index}: {error}')
        try:
            journal=row['journal']
            if not any(isinstance(ref,dict) and ref.get('path')==journal for ref in refs):raise ValueError('journal is not digest-bound evidence')
            observed=measurement(read_events(root/journal),row['run_id'])
            for key in ('engineer_active_seconds','accepted_capability_seconds','elapsed_seconds'):
                if observed[key] is None:
                    if row.get(key) is not None:raise ValueError('failed delivery was presented as accepted time')
                elif type(row.get(key)) not in (int,float) or abs(observed[key]-row[key])>0.000001:raise ValueError('reported timing differs from prospective journal: '+key)
            if observed['censored'] != row.get('censored'):raise ValueError('censoring differs from prospective journal')
            if row.get('cost_basis') not in ('harness_reported','api_equivalent_estimate'):raise ValueError('cost basis is not explicit')
            if not row.get('cost_evidence'):raise ValueError('cost including failures lacks measured usage evidence')
            if row['scenario']=='investigation' and not row.get('semantic_review_ref'):raise ValueError('investigation requires retained review of its actual claims')
        except (OSError,ValueError,TypeError,KeyError) as error:gaps.append(f'run {index}: {error}')
    return gaps

if __name__=='__main__':
    if len(sys.argv)!=3 or sys.argv[1]!='validate':raise SystemExit('Usage: pilot.py validate <results.json>')
    path=Path(sys.argv[2]);data=json.loads(path.read_text());result=evaluate(data)
    if not result['gaps']:
        gaps=verify_evidence(data,path.parent)
        if gaps:result.update(qualified=False,state='unverified',gaps=gaps)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['qualified'] else 1)
