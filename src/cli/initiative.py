"""Derived initiative views: canonical acceptance, topology, and explicit proof gaps."""
from pathlib import Path
import json
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'src/lib'),str(ROOT/'src/security')]
from provenance import verify_bundle
from backlog.status import status as task_status, resolve
from task_graph import task_files


def view(root: Path, initiative: str, mode: str='status') -> dict:
    folder=root/'tasks/.plans'/initiative
    plan=verify_bundle(root,folder/'task-plan.json')
    lineage=json.loads((folder/'task-plan-lineage.json').read_text())['units']
    tasks=[]
    existing = {p.stem for p in task_files(root / "tasks")}
    for unit in plan['units']:
        try:
            if unit["id"] not in existing: raise FileNotFoundError(unit["id"])
            state=task_status(root/'tasks',resolve(root/'tasks',unit['id']))
            tasks.append({'id':unit['id'],'depends_on':unit['depends_on'],'lineage':lineage[unit['id']],'sdlc_stages':unit.get('sdlc_stages',[]),**state})
        except FileNotFoundError:
            tasks.append({'id':unit['id'],'depends_on':unit['depends_on'],'lineage':lineage[unit['id']],'lifecycle':'not_materialized','acceptance':{'accepted':False,'record_matches':False}})
    accepted={t['id'] for t in tasks if t['acceptance'].get('record_matches') and t['acceptance'].get('accepted')}
    capabilities=[]
    for leg in sorted({v['leg'] for v in lineage.values()}):
        children=sorted(k for k,v in lineage.items() if v['leg']==leg)
        proofs=sorted(u['id'] for u in plan['units'] if leg in u.get('proves_capabilities',[]))
        proven=bool(proofs) and set(proofs+children)<=accepted
        capabilities.append({'leg':leg,'seam':lineage[children[0]]['seam'],'swimlane':lineage[children[0]]['swimlane'],'tasks':children,'proof_tasks':proofs,'state':'proven' if proven else 'unproven','gap':None if proven else ('integration proof task missing' if not proofs else 'required task acceptance is missing')})
    attempts=[]
    database=root/'.taskspec/mesh/mesh.db'
    if database.is_file():
        connection=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)
        try:
            connection.row_factory=sqlite3.Row
            attempts=[dict(row) for row in connection.execute('SELECT task_id,attempt_id,state,fencing_token FROM leases ORDER BY issued_at') if row['task_id'] in lineage]
        finally: connection.close()
    if any(t['lifecycle']=='not_materialized' for t in tasks):
        next_actions=[f'taskspec batch --plan tasks/.plans/{initiative}/task-plan.json']
    elif any(a['state'] in ('leased','preparing','running','verifying','awaiting_supervision') for a in attempts):
        next_actions=[f'taskspec mesh status {a["attempt_id"]}' for a in attempts if a['state'] in ('leased','preparing','running','verifying','awaiting_supervision')]
    elif any(t['authorization']['tier']!=1 or t['authorization']['stale'] for t in tasks if t['id'] not in accepted):
        next_actions=[t['next_command'] for t in tasks if t['id'] not in accepted and (t['authorization']['tier']!=1 or t['authorization']['stale'])]
    elif len(accepted)<len(tasks):
        stopped=[a for a in attempts if a['state'] in ('parked','cancelled','expired') and a['task_id'] not in accepted]
        next_actions=[f'taskspec mesh status {a["attempt_id"]}' for a in stopped] or [f'taskspec mesh run --initiative {initiative}']
    elif any(c['state']!='proven' for c in capabilities):
        next_actions=['taskspec guide acceptance']
    else:
        next_actions=['taskspec guide sdlc']
    return {'contract':'TaskInitiativeGraph/v1' if mode!='status' else 'TaskInitiativeStatus/v1','initiative':initiative,'state':'compiled','view':mode,'tasks':tasks if mode!='capabilities' else [],'capabilities':capabilities,'accepted_tasks':sorted(accepted),'attempts':attempts,'proof_gaps':[c['leg'] for c in capabilities if c['state']!='proven'],'next':next_actions}

if __name__ == '__main__':
    import re
    try:
        root=Path(sys.argv[1]).resolve(); initiative=sys.argv[2]
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}',initiative): raise ValueError('invalid initiative')
        plan=verify_bundle(root,root/'tasks/.plans'/initiative/'task-plan.json')
        print(json.dumps([unit['id'] for unit in plan['units']]))
    except (OSError,ValueError) as error:
        print(str(error),file=sys.stderr);raise SystemExit(1)
