#!/usr/bin/env python3
"""Verify the completed toolkit release against files, Git, and GitHub state.

This is the publication task's terminal check. Local test output or a Boolean
checklist flag alone cannot establish release completion.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def command(*args):
    return subprocess.check_output(args,cwd=ROOT,text=True,stderr=subprocess.PIPE).strip()


def require(condition,message):
    if not condition:raise ValueError(message)


def document(path):
    value=json.loads(path.read_text())
    require(isinstance(value,dict),f'{path}: expected an object')
    return value


def evidence(folder,ref):
    require(isinstance(ref,dict) and {'path','sha256'}<=set(ref),'evidence needs path and sha256')
    relative=Path(ref['path'])
    require(not relative.is_absolute() and '..' not in relative.parts,'evidence must use a portable relative path')
    path=(folder/relative).resolve()
    require(path.is_relative_to(folder.resolve()),'evidence escapes its release directory')
    require(hashlib.sha256(path.read_bytes()).hexdigest()==ref['sha256'],f'evidence changed: {relative}')
    return path


def same_shipped_source(left,right):
    command('git','merge-base','--is-ancestor',left,right)
    changed=command('git','diff','--name-only',left,right).splitlines()
    # Task/acceptance/release records are excluded from the source distribution.
    # Runtime image inputs are shipped and must remain exactly the tested bytes.
    allowed=lambda p:p.startswith(('tasks/','.taskspec/')) or (p.startswith('release/') and not p.startswith('release/mesh/'))
    require(all(allowed(p) for p in changed),f'shipped source changed after tested commit {left}')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--version',required=True)
    args=parser.parse_args();version=args.version;tag='v'+version;folder=ROOT/'release'/version
    try:
        require((ROOT/'VERSION').read_text().strip()==version,'VERSION is not the requested release')
        require(command('git','branch','--show-current')=='main','release verification requires main')
        require(not command('git','status','--porcelain'),'commit the reviewed release and acceptance evidence first')
        head=command('git','rev-parse','HEAD');tag_commit=command('git','rev-parse',tag+'^{commit}')
        command('git','merge-base','--is-ancestor',tag_commit,head)
        remote=command('git','ls-remote','origin','refs/heads/main','refs/tags/'+tag,'refs/tags/'+tag+'^{}')
        refs={line.split()[1]:line.split()[0] for line in remote.splitlines()}
        require(refs.get('refs/heads/main')==head,'remote main does not contain the current release evidence')
        require(refs.get('refs/tags/'+tag+'^{}',refs.get('refs/tags/'+tag))==tag_commit,'remote release tag differs from local tag')
        archive=folder/'artifacts'/f'task-spec-{version}.tar.gz'
        command('git','ls-files','--error-unmatch',str(archive.relative_to(ROOT)))
        digest=hashlib.sha256(archive.read_bytes()).hexdigest()
        require(archive.with_name(archive.name+'.sha256').read_text().split()[0]==digest,'source archive checksum differs')
        local=document(folder/'qualification/final-check.json')
        require(local.get('command')=='make check' and local.get('exit_code')==0,'final make check did not pass')
        log=evidence(folder,local['evidence']).read_text()
        require('CHECK=READY' in log and 'CONFORMANCE=L2' in log,'final gate log lacks required completion markers')
        same_shipped_source(local['source_commit'],tag_commit)
        pilot=json.loads(command(sys.executable,str(ROOT/'tests/evals/toolkit/pilot.py'),'validate',str(folder/'pilot/results.json')))
        require(pilot.get('qualified') is True,'comparative pilot is not qualified')
        chat=document(folder/'qualification/chat-results.json')
        expected={row['id'] for row in json.loads((ROOT/'tests/evals/toolkit/chat-cases.json').read_text())}
        for harness in ('codex','claude'):
            rows=[r for r in chat.get('runs',[]) if r.get('harness')==harness]
            require({r.get('case') for r in rows}==expected,f'{harness}: chat corpus is incomplete')
            for row in rows:
                require(row.get('passed') is True and row.get('false_completion') is False,f'{harness}/{row.get("case")}: behavioral qualification failed')
                for ref in row.get('evidence',[]):evidence(folder,ref)
                require(row.get('evidence') and row.get('behavior_review'), 'chat trace lacks retained evidence and review of actual behavior')
                evidence(folder,row['behavior_review'])
        hosted=document(folder/'qualification/hosted.json')
        checked=set()
        for recorded in hosted['runs']:
            observed=json.loads(command('gh','run','view',str(recorded['id']),'--json','conclusion,status,headSha,url,jobs'))
            require(observed.get('status')=='completed' and observed.get('conclusion')=='success',f'hosted run {recorded["id"]} has not passed')
            same_shipped_source(observed['headSha'],tag_commit)
            for job in observed.get('jobs',[]):
                if job.get('conclusion')=='success':checked.add(job['name'])
        for name in ('make check (ubuntu-latest)','make check (macos-latest)','TaskMesh autonomous isolation (ubuntu)'):
            require(name in checked,'missing hosted proof: '+name)
        release=json.loads(command('gh','release','view',tag,'--json','tagName,isDraft,publishedAt,url,assets'))
        require(release['tagName']==tag and not release['isDraft'] and release['publishedAt'],'release is not published')
        names={asset['name'] for asset in release['assets']}
        require(archive.name in names and archive.name+'.sha256' in names,'published source assets are missing')
        distribution=document(folder/'qualification/distribution.json')
        require(distribution.get('verified') is True and distribution.get('source_archive_sha256')==digest,'published download/install verification is missing')
        for ref in distribution.get('evidence',[]):evidence(folder,ref)
        require(distribution.get('evidence'),'distribution verification has no retained output')
        print(json.dumps({'contract':'TaskToolkitPublishedRelease/v1','verified':True,'version':version,'main_commit':head,'tag_commit':tag_commit,'release_url':release['url'],'source_archive_sha256':digest},indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError) as error:
        print(json.dumps({'contract':'TaskToolkitPublishedRelease/v1','verified':False,'code':'RELEASE_INCOMPLETE','message':str(error),'next':'Complete the missing source, pilot, chat, hosted, publication, or download evidence before finalizing the release.'},indent=2))
        return 1

if __name__=='__main__':raise SystemExit(main())
