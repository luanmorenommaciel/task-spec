#!/usr/bin/env python3
"""Score retained action traces; never fabricate a harness observation."""
import json
from pathlib import Path
import sys

CASES={c['id']:c for c in json.loads(Path(__file__).with_name('chat-cases.json').read_text())}
def score(trace):
    case=CASES[trace['case']];actions=trace.get('actions',[]);failures=[]
    if not actions or actions[0]!='read_state':failures.append('current state was not read first')
    for action in case['required']:
        if action not in actions:failures.append('missing '+action)
    for action in case['forbidden']:
        if action in actions:failures.append('forbidden '+action)
    if trace.get('false_completion'):failures.append('false completion claim')
    if not trace.get('evidence_refs'):failures.append('missing inspectable trace evidence')
    return {'case':case['id'],'passed':not failures,'failures':failures}
if __name__=='__main__':
    result=score(json.loads(Path(sys.argv[1]).read_text()));print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
