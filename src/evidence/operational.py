#!/usr/bin/env python3
"""Import reported CI/CD and incident evidence without promoting it to acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/author'))
from examples import write_atomic


def validate(data):
    if not isinstance(data,dict) or data.get('contract')!='TaskOperationalEvidence/v1': raise ValueError('expected TaskOperationalEvidence/v1')
    kind=data.get('kind')
    if kind not in ('deployment','incident'): raise ValueError('kind must be deployment or incident')
    required=['id','observed_at','source','observation','revision','environment']
    if kind=='deployment': required+=['artifact','pipeline_run','observed_result']
    else: required+=['impact','disposition']
    for key in required:
        if not isinstance(data.get(key),str) or not data[key].strip(): raise ValueError('nonblank '+key+' required')
    if data.get('claim')!='reported': raise ValueError('external operational claims must be reported; local import cannot certify target health')
    if kind=='incident' and data['disposition']!='candidate_intent': raise ValueError('incident import creates candidate_intent only')
    allowed=set(required+['contract','kind','claim','attachments'])
    if set(data)-allowed: raise ValueError('unknown operational fields: '+', '.join(sorted(set(data)-allowed)))
    attachments=data.get('attachments',[])
    if not isinstance(attachments,list): raise ValueError('attachments must be a list')
    for ref in attachments:
        if not isinstance(ref,dict) or set(ref)!={'path','sha256'} or not all(isinstance(ref[k],str) for k in ref): raise ValueError('attachment requires path and sha256')
        if len(ref['sha256'])!=64 or any(c not in '0123456789abcdef' for c in ref['sha256']): raise ValueError('attachment sha256 must be 64 lowercase hex characters')
    return data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['validate','import']);parser.add_argument('file');parser.add_argument('--out');parser.add_argument('--verify-local',action='store_true')
    args=parser.parse_args()
    try:
        raw=sys.stdin.read() if args.file=='-' else Path(args.file).read_text()
        document=json.loads(raw)
        if isinstance(document,dict) and document.get('contract')=='TaskOperationalImport/v1':
            if document.get('target_health_verified') is not False or document.get('acceptance_granted') is not False:
                raise ValueError('operational imports cannot grant health verification or acceptance')
            source=document.get('source_content')
            if not isinstance(source,str) or hashlib.sha256(source.encode()).hexdigest()!=document.get('source_digest'):
                raise ValueError('operational source digest mismatch')
            data=validate(json.loads(source))
            if document.get('evidence')!=data: raise ValueError('imported payload differs from its original source')
            refs=[{k:v for k,v in row.items() if k!='verification'} for row in document.get('attachments',[])]
            if refs!=data.get('attachments',[]):raise ValueError('imported attachment mapping changed')
            if any(row.get('verification') not in ('reported','local_digest_verified') for row in document.get('attachments',[])):raise ValueError('invalid attachment verification claim')
        else: data=validate(document)
        observations=[]
        for ref in data.get('attachments',[]):
            if args.verify_local:
                path=Path(ref['path']); root=Path.cwd().resolve()
                if path.is_absolute() or '..' in path.parts or not (root/path).resolve().is_relative_to(root) or (root/path).is_symlink(): raise ValueError('local evidence path escapes workspace')
                if hashlib.sha256((root/path).read_bytes()).hexdigest()!=ref['sha256']: raise ValueError('attachment bytes do not match: '+ref['path'])
            observations.append({**ref,'verification':'local_digest_verified' if args.verify_local else 'reported'})
        receipt={'contract':'TaskOperationalImport/v1','source_digest':hashlib.sha256(raw.encode()).hexdigest(),'source_content':raw,'evidence':data,'attachments':observations,'target_health_verified':False,'acceptance_granted':False}
        if isinstance(document,dict) and document.get('contract')=='TaskOperationalImport/v1':
            if args.action=='import': raise ValueError('receipt is already imported; validate it or import original evidence')
            receipt=document
        dry=os.environ.get('TASKSPEC_DRY_RUN')=='1'
        if args.action=='import':
            if not args.out: raise ValueError('import requires explicit --out path')
            target=Path(args.out).absolute()
            if target.exists() or target.is_symlink(): raise ValueError('output already exists; choose a new receipt path')
            if not dry: write_atomic(target,(json.dumps(receipt,indent=2)+'\n').encode(),False)
        result={'contract':'TaskOperationalResult/v1','valid':True,'dry_run':dry,'written':args.action=='import' and not dry,'output':args.out,'receipt':receipt}
        print(json.dumps(result,indent=2) if os.environ.get('TASKSPEC_JSON_MODE')=='1' else 'OPERATIONAL=VALID claim=reported target_health_verified=false'+(' out='+args.out if args.out else ''))
        return 0
    except (ValueError,OSError) as error:
        print(json.dumps({'contract':'TaskOperationalResult/v1','code':'OPERATIONAL_INVALID','message':str(error),'next':'taskspec example release-evidence --out example.json'}) if os.environ.get('TASKSPEC_JSON_MODE')=='1' else 'OPERATIONAL=INVALID '+str(error),file=sys.stdout if os.environ.get('TASKSPEC_JSON_MODE')=='1' else sys.stderr)
        return 1

if __name__=='__main__':raise SystemExit(main())
