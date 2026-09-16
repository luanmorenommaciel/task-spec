#!/usr/bin/env python3
"""Build the predeclared real-issue corpus without inventing model decisions.

Recipes are supervisor-authored fixed inputs, shared with every comparison arm.
This benchmark measures delivery of understood issues, not architectural discovery.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import yaml
from public_evaluator import DIRECTORY, command as evaluator_command

ROOT=Path(__file__).resolve().parents[3]


def leaves(issue):
    scenario=issue['id']
    if scenario=='cross-seam':
        return [dict(slug='overview-route',scope=['src/cli/guide.py'],goal='Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing guide routes.'),
                dict(slug='overview-skill',scope=['SKILL.md','skills/task-spec/SKILL.md'],goal='Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state. Preserve exact root and mirror parity and installed relative links.')]
    if scenario=='contention':
        return [dict(slug='contention-worker',scope=['tests/fixtures/toolkit/resource-worker.sh'],goal='Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.'),
                dict(slug='contention',scope=['tests/test-toolkit-resource-contention.sh'],goal=issue['expected']+' Use tests/fixtures/toolkit/resource-worker.sh for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal, cancellation/reuse, and unchanged target assertions pass. Compile the helper from this repository with its VERSION; do not use an installed helper from another checkout.')]
    return [dict(slug=scenario,scope=issue['write_scope'],goal=issue['expected'])]


def recipe(issue,work,evaluator,harness):
    base=yaml.safe_load((ROOT/'tests/fixtures/toolkit/rate-limiting-recipe.yaml').read_text())
    evidence_path='tests/fixtures/toolkit/pilot-issue.json'
    source={'uri':evidence_path,'captured_at':issue['registered_at'],'sha256':hashlib.sha256((work/evidence_path).read_bytes()).hexdigest()}
    scenario=issue['id'];upper=scenario.upper()
    base['intent']={'id':'DI-PILOT-'+upper,'title':issue['issue'],'summary':issue['expected'],'claim':'proposed','source':source,'success':[issue['expected']],'out_of_scope':['Changes outside the registered write surface.','Production deployment, policy changes, self-authorization, and independent agents.']}
    base['system_map']={'claim':'proposed','components':issue.get('seams',[scenario]),'external_dependencies':['TaskSpec CLI and the independently registered evaluator'],'unknowns':[]}
    base['evidence']=[{'id':'E-PILOT-ISSUE','claim':'current','source':source,'confidence':1.0,'summary':'A repository issue inspected before comparative execution; source digests and reproduction are retained.'}]
    base['decisions']=[{'id':'ADR-PILOT-SCOPE','status':'accepted','owner':'pilot-supervisor','rationale':'The user authorized real repository issues with prospective intervention recording. This fixed corpus defines the evaluated scope before execution; it does not claim a new human review occurred during each run.'}]
    template=copy.deepcopy(base['seams'][0]);base['seams']=[];base['steel_thread']=[];base['objections']=[];base['contentions']=[]
    previous=None
    for leaf in leaves(issue):
        slug=leaf['slug'];token=slug.upper();unit_id='T-20260914-pilot-'+slug
        seam=copy.deepcopy(template);leg=seam['swimlane']['legs'][0];task=leg['tasks'][0]
        seam.update(id='SEAM-'+token,name=slug,description=leaf['goal'],evidence=['E-PILOT-ISSUE'],responsibility=leaf['goal'],consumes=['registered issue'] if previous is None else [previous['output']],produces=[slug+' verified behavior'],owner='pilot-'+slug,independent_proof='Run the registered independent '+slug+' evaluator.',decision_ids=['ADR-PILOT-SCOPE'],rejected_alternatives=[{'alternative':'Merge this responsibility into an unrelated task','reason':'Its write surface and independently assessable outcome belong to this boundary.'}])
        lane=seam['swimlane'];lane.update(id='LANE-'+token,name=slug+' delivery',owner='pilot-'+slug)
        leg.update(id='LEG-'+token,observable_state=leaf['goal'],proof='The declared evaluator succeeds without widening the write surface.',requires=[] if previous is None else [previous['output']],produces=[slug+' verified behavior'])
        command=evaluator_command(evaluator,'cross-seam' if slug=='overview-skill' else slug)
        task.update(id=unit_id,title=leaf['goal'].split('.')[0],goal=leaf['goal'],done_condition=leaf['goal'],effort='M' if len(leaf['scope'])>2 else 'S',profile='standard',execution_backend=harness,required_tools=['git','bash','python3'],depends_on=[] if previous is None else [previous['id']],touches_paths=[p for p in leaf['scope'] if (work/p).exists()],creates_paths=[p for p in leaf['scope'] if not (work/p).exists()],behavior=[{'id':'B-1','given':'the registered repository issue and fixed authorized scope','when':'the bounded implementation is independently evaluated','then':'the declared behavior passes without modifying unrelated files or promoting reported evidence'}],evals=[{'id':'eval_1','description':'Independent behavioral proof for '+slug,'bash':command,'verifies':['B-1']}],anti_patterns=[{'action':'weaken the independent evaluator','reason':'it would invalidate the comparison','instead':'fix the behavior within the declared surface'}],do_not_touch=['tests/fixtures/toolkit/pilot-issue.json',str(DIRECTORY),'tasks'],rollback='Revert only this isolated candidate change.',observability='Retained provider output, evaluation result, and prospective event journal.')
        task['behavior'].append({'id':'B-2','given':'the recorded evidence and authorization boundary','when':'the candidate is checked','then':'source evidence is unchanged and no unrelated write is present'})
        task['evals'] += [{'id':'eval_2','description':'Declared write surface only','bash':evaluator_command(evaluator,'write-boundary'),'verifies':['B-2']},{'id':'eval_3','description':'Registered issue evidence is unchanged','bash':evaluator_command(evaluator,'source-integrity'),'verifies':['B-2']}]
        task['anti_patterns'] += [{'action':'expand the scope','reason':'it breaks matched permissions','instead':'report the missing work as a blocker'},{'action':'claim success without evidence','reason':'a plausible patch does not establish behavior','instead':'run the independent proof and report failures'}]
        base['seams'].append(seam);base['steel_thread'].append(leg['id']);previous={'id':unit_id,'output':slug+' verified behavior'}
    return base


def direct_plan(authored):
    """A minimal direct-task envelope for the native-harness comparison."""
    units=[]
    for seam in authored['seams']:
        for leg in seam['swimlane']['legs']:
            for task in leg['tasks']:
                unit={key:copy.deepcopy(task[key]) for key in ['id','title','goal','effort','profile','execution_backend','required_tools','depends_on','touches_paths','creates_paths','do_not_touch','rollback','observability']}
                unit.update(agent='any',why=authored['intent']['summary'],context=task['done_condition'],source_note='tests/fixtures/toolkit/pilot-issue.json',behaviors=task['behavior'],anti_patterns=['Do not modify the evaluator or authorize additional work.'],evals=[{'id':e['id'],'description':e['description'],'command':e['bash'],'verifies':e['verifies'],'terminal':True,'expected_duration_sec':120} for e in task['evals']])
                units.append(unit)
    return {'api_version':'taskspec.dev/v1','kind':'TaskPlan','approved':True,'metadata':{'name':'pilot-native-envelope'},'units':units}
