#!/usr/bin/env python3
"""Execute the frozen pilot order, retaining every observed cell.

Two harnesses share each block; workflow order is fixed before observation.
This drives experiments only. Managed scheduling and retries remain in TaskMesh.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
PILOT=ROOT/'release/3.10.0/pilot'

def main():
    schedule=json.loads((PILOT/'schedule.json').read_text())
    if schedule['status']!='frozen':raise SystemExit('Schedule is not frozen')
    tooling=ROOT/schedule['tooling_directory'];python=tooling/'.taskspec/runtime/decompose/bin/python'
    logs=PILOT/'controller-logs';logs.mkdir(exist_ok=True)
    def run(row):
        existing=[]
        for p in (PILOT/'runs').glob('*/result.json'):
            d=json.loads(p.read_text())
            if all(d[k]==row[k] for k in ['scenario','harness','workflow','repeat']):existing.append((p,d))
        if len(existing)>1:raise RuntimeError('Duplicate cell exists: '+row['id'])
        if existing:return {'id':row['id'],'retained':str(existing[0][0].relative_to(PILOT)),'already_observed':True,'accepted':existing[0][1]['accepted']}
        path=logs/(row['id']+'.json')
        if path.exists():raise RuntimeError('Interrupted cell needs explicit inspection before resume: '+row['id'])
        command=[str(python),str(ROOT/'tests/evals/toolkit/compare.py'),'--scenario',row['scenario'],'--harness',row['harness'],'--workflow',row['workflow'],'--repeat',str(row['repeat']),'--snapshot',str(PILOT/'inputs/task-spec-3.9.0.tar.gz'),'--tooling',str(tooling),'--python',str(python),'--helper',str(tooling/'libexec/taskspec-meshd'),'--adapters',str(PILOT/'inputs/adapters'),'--seamwise',schedule['seamwise_executable']]
        with path.open('x') as out:completed=subprocess.run(command,stdout=out,stderr=subprocess.STDOUT,cwd=ROOT)
        data=json.loads(path.read_text())
        result={'id':row['id'],'exit_code':completed.returncode,'run_id':data['run_id'],'accepted':data['accepted'],'error':data['error'],'elapsed_seconds':data['elapsed_seconds'],'cost_usd':data['cost_including_failures']}
        print(json.dumps(result),flush=True);return result
    observations=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for block in sorted({r['block'] for r in schedule['runs']}):
            for name,expected in schedule['controller_digests'].items():
                if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise RuntimeError('Frozen controller changed: '+name)
            rows=[r for r in schedule['runs'] if r['block']==block]
            observations.extend(pool.map(run,rows))
            progress={'contract':'TaskPilotScheduleProgress/v1','observed_at':datetime.now(timezone.utc).isoformat(),'completed_blocks':block,'planned_blocks':len({r['block'] for r in schedule['runs']}),'observations':observations}
            (PILOT/'progress.json').write_text(json.dumps(progress,indent=2)+'\n')
    runs=[json.loads(p.read_text()) for p in sorted((PILOT/'runs').glob('*/result.json'))]
    (PILOT/'results.json').write_text(json.dumps({'contract':'TaskToolkitPilotResults/v1','schedule_sha256':hashlib.sha256((PILOT/'schedule.json').read_bytes()).hexdigest(),'runs':runs},indent=2)+'\n')
    return subprocess.call([str(python),str(ROOT/'tests/evals/toolkit/pilot.py'),'validate',str(PILOT/'results.json')],cwd=ROOT)

if __name__=='__main__':raise SystemExit(main())
