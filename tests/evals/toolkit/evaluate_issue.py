#!/usr/bin/env python3
"""Independent behavioral checks for the registered repository-issue corpus."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def call(root,*args,input=None,expect=0,timeout=120,env=None):
    result=subprocess.run(list(args),cwd=root,input=input,text=True,capture_output=True,timeout=timeout,env=env)
    if (result.returncode==0)!=(expect==0):
        raise AssertionError(f'command {args}: exit {result.returncode}\n{result.stdout}\n{result.stderr}')
    return result


def ts(root,*args,input=None,expect=0):
    result=call(root,'bash',str(root/'bin/taskspec'),'--json',*args,input=input,expect=expect)
    value=json.loads(result.stdout)
    assert value['ok']==(expect==0),value
    assert '\x1b' not in result.stdout and 'Traceback (most recent call last)' not in result.stdout+result.stderr
    return value


def recipe_stdin(root):
    recipe=json.loads((ROOT/'spec/conformance/toolkit/execution-recipe.json').read_text())
    with tempfile.TemporaryDirectory(prefix='recipe evaluator ') as temp:
        file=Path(temp)/'valid recipe.json';file.write_text(json.dumps(recipe))
        ts(root,'recipe','validate',str(file))
        ts(root,'recipe','validate','-',input=json.dumps(recipe))
        invalid=[None,[],{},dict(recipe,max_rounds=True),dict(recipe,max_rounds=100),dict(recipe,runner='other'),dict(recipe,required_capabilities=[])]
        for document in invalid:
            ts(root,'recipe','validate','-',input=json.dumps(document),expect=1)
        ts(root,'recipe','validate','-',input='{broken',expect=1)
        ts(root,'recipe','validate','-',input='',expect=1)


def overview_route(root):
    content=(root/'docs/guides/toolkit/index.md').read_text()
    data=ts(root,'guide','overview')['data']
    assert data['content']==content and data['version']==(root/'VERSION').read_text().strip()
    assert data['contract']=='TaskGuide/v1'
    result=call(root,'bash',str(root/'bin/taskspec'),'guide','overview')
    assert result.stdout.strip()==content.strip()


def overview_skill(root):
    canonical=(root/'SKILL.md').read_bytes()
    assert canonical==(root/'skills/task-spec/SKILL.md').read_bytes()
    assert b'guide overview' in canonical, 'skill must route initial orientation to CLI state and installed overview'
    for parent in [root,root/'skills/task-spec']:
        for link in re.findall(r'\]\(([^)]+)\)',(parent/'SKILL.md').read_text()):
            assert (parent/link).is_file(),link
    for topic in ('intent','decomposition','recipes','mesh','acceptance','release','maintenance','migration','install','cli'):
        assert ts(root,'guide',topic)['data']['content']


def overview(root):
    overview_route(root)
    overview_skill(root)


def incident(root):
    source=json.loads((ROOT/'docs/examples/incident.json').read_text())
    with tempfile.TemporaryDirectory(prefix='incident evaluator ') as temp:
        folder=Path(temp);original=folder/'incident.json';original.write_text(json.dumps(source));receipt=folder/'receipt.json'
        ts(root,'receipt','operational','import',str(original),'--out',str(receipt))
        ts(root,'receipt','operational','validate',str(receipt))
        valid=json.loads(receipt.read_text())
        patches=[{'attachments':None},{'attachments':{}},{'attachments':['bad']},{'attachments':[None]}, {'unexpected':True},{'target_health_verified':True},{'acceptance_granted':True},{'source_content':17}]
        for patch in patches:
            bad=folder/'bad.json';bad.write_text(json.dumps({**valid,**patch}))
            result=ts(root,'receipt','operational','validate',str(bad),expect=1)
            assert result['data']['code']=='OPERATIONAL_INVALID',result
        assert json.loads(receipt.read_text())==valid,'validation rewrote its input'


def investigation(root):
    report=root/'docs/maintainers/recipe-assurance-investigation.md'
    text=report.read_text();lower=text.lower()
    assert len(text)>=800,'investigation must explain and substantiate its conclusion'
    for symbol in ('executeRecipe','runSandbox','finalizeSandboxEvidenceIn','verifyAcceptCommitAndIntegrate'):
        assert symbol in text,'missing inspected execution boundary: '+symbol
    assert 'host' in lower and 'sanitized' in lower and 'attest' in lower
    assert 'required' in lower and 'environment' in lower and 'token' in lower
    assert 'not' in lower and ('isolat' in lower or 'sandbox' in lower)
    for path in ('mesh/internal/mesh/recipe.go','mesh/internal/mesh/sandbox.go','mesh/internal/mesh/process.go'):
        assert path in text and (root/path).is_file()
    # This check establishes structural sufficiency only. The release scorer must
    # retain a separate review of the actual claims before crediting acceptance.
    return {'semantic_review_required':True}


def contention(root):
    script=root/'tests/test-toolkit-resource-contention.sh'
    worker=root/'tests/fixtures/toolkit/resource-worker.sh'
    assert script.is_file() and worker.is_file()
    result=call(root,'bash',str(script),timeout=240)
    assert 'TOOLKIT_RESOURCE_CONTENTION=PASS' in result.stdout
    # Falsify the proposed regression: a runtime with resource checks disabled
    # must fail it. Compile that runtime first so a build failure cannot count.
    with tempfile.TemporaryDirectory(prefix='contention mutation ') as temp:
        clone=Path(temp)
        for name in ('src','bin','mesh','spec','harness','tests'):
            shutil.copytree(root/name,clone/name,ignore=shutil.ignore_patterns('__pycache__','evidence','_workdir'))
        for name in ('go.mod','go.sum','VERSION'):
            shutil.copy2(root/name,clone/name)
        # Establish that this copied environment can execute the regression.
        # Otherwise a missing runtime could masquerade as a killed mutant.
        call(clone,'go','build','./mesh/cmd/taskspec-meshd',timeout=120)
        control=call(clone,'bash',str(clone/'tests/test-toolkit-resource-contention.sh'),timeout=240)
        assert 'TOOLKIT_RESOURCE_CONTENTION=PASS' in control.stdout
        source=clone/'mesh/internal/mesh/lease.go';original=source.read_text()
        mutant,count=re.subn(r'if kind == "resource" && contains\(task.ClaimedResources, value\)', 'if false && kind == "resource" && contains(task.ClaimedResources, value)',original,count=1)
        assert count==1,'resource guard mutation target changed'
        source.write_text(mutant)
        call(clone,'go','build','./mesh/cmd/taskspec-meshd',timeout=120)
        result=call(clone,'bash',str(clone/'tests/test-toolkit-resource-contention.sh'),expect=1,timeout=240)
        assert 'TOOLKIT_RESOURCE_CONTENTION=PASS' not in result.stdout


def contention_worker(root):
    worker=root/'tests/fixtures/toolkit/resource-worker.sh'
    call(root,'bash','-n',str(worker))
    assert 'resource-worker/' in call(root,'bash',str(worker),'--version').stdout
    process=subprocess.Popen(['bash',str(worker)],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        try:
            process.wait(timeout=0.3)
            raise AssertionError('resource worker must hold the attempt until cancelled')
        except subprocess.TimeoutExpired:
            pass
    finally:
        process.terminate()
        try:process.communicate(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.communicate()


def release_evidence(root):
    with tempfile.TemporaryDirectory(prefix='release evaluator ') as temp:
        fixture=Path(temp);(fixture/'tools').mkdir();shutil.copy2(root/'tools/build-release-archive.py',fixture/'tools/build-release-archive.py')
        (fixture/'VERSION').write_text('3.9.0\n');(fixture/'WATCHDOG.yml').write_text('local_only: true\n')
        for relative in ('spec/conformance/results.json','spec/conformance/_state.yaml','spec/conformance/_workdir/generated.txt'):
            path=fixture/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('generated\n')
        (fixture/'source.txt').write_text('real archive content\n')
        call(fixture,'git','init','-q');call(fixture,'git','add','.')
        call(fixture,'python3',str(fixture/'tools/build-release-archive.py'),'--out-dir',str(fixture/'artifacts'))
        archive=fixture/'artifacts/task-spec-3.9.0.tar.gz'
        actual=hashlib.sha256(archive.read_bytes()).hexdigest()
        assert (fixture/'artifacts/task-spec-3.9.0.tar.gz.sha256').read_text().split()[0]==actual
        with tarfile.open(archive) as bundle:
            names=[m.name for m in bundle.getmembers()]
            assert any(n.endswith('/source.txt') for n in names)
            assert not any(n.endswith('/WATCHDOG.yml') or '/spec/conformance/_workdir/' in n or n.endswith('/spec/conformance/results.json') or n.endswith('/spec/conformance/_state.yaml') for n in names),names
    document=root/'docs/examples/pilot-release-evidence.json'
    ts(root,'receipt','operational','validate',str(document))
    data=json.loads(document.read_text())
    assert data['kind']=='deployment' and data['claim']=='reported'
    assert data.get('attachments'),'release report needs an actual artifact digest'
    for ref in data['attachments']:
        file=root/ref['path'];assert file.is_file() and hashlib.sha256(file.read_bytes()).hexdigest()==ref['sha256']
    call(root,'git','merge-base','--is-ancestor',data['revision'],'HEAD')
    assert 'candidate' in data['observation'].lower() and 'uncommitted' in data['observation'].lower()


CHECKS={'small-fix':recipe_stdin,'cross-seam':overview,'overview-route':overview_route,'overview-skill':overview_skill,'incident':incident,'investigation':investigation,'contention':contention,'contention-worker':contention_worker,'release-evidence':release_evidence}


def write_boundary(root):
    issue=json.loads((root/'tests/fixtures/toolkit/pilot-issue.json').read_text())
    changed=call(root,'git','diff','--name-only','HEAD').stdout.splitlines()
    changed+=call(root,'git','ls-files','--others','--exclude-standard').stdout.splitlines()
    for path in changed:
        if path.startswith(('tasks/','.taskspec/','seamwise/')):continue
        assert any(path==scope or path.startswith(scope.rstrip('/')+'/') for scope in issue['write_scope']), 'undeclared write: '+path


def source_integrity(root):
    path='tests/fixtures/toolkit/pilot-issue.json'
    assert call(root,'git','show','HEAD:'+path).stdout==(root/path).read_text(), 'registered source evidence was modified'


CHECKS.update({'write-boundary':write_boundary,'source-integrity':source_integrity})
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('scenario',choices=CHECKS);parser.add_argument('--root',required=True,type=Path)
    args=parser.parse_args()
    try:
        details=CHECKS[args.scenario](args.root.resolve()) or {}
        print(json.dumps({'contract':'TaskPilotIssueEvaluation/v1','scenario':args.scenario,'passed':True,**details}))
    except (AssertionError,ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
        print(json.dumps({'contract':'TaskPilotIssueEvaluation/v1','scenario':args.scenario,'passed':False,'error':str(error)}))
        raise SystemExit(1)
