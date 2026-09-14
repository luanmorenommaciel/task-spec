#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import json,sys,tempfile
sys.path.insert(0,str(Path(sys.argv[1])/'tests/evals/toolkit'))
from record import append_event,read_events,measurement,run_command
from unittest.mock import patch
import run_schedule
with tempfile.TemporaryDirectory(prefix='pilot journal ') as temp:
 root=Path(temp);journal=root/'events.jsonl'
 append_event(journal,'run','run_started',{'intervention_recording_enabled':True})
 append_event(journal,'run','intervention_started',{'intervention_id':'decision','actor_kind':'human'})
 try:measurement(read_events(journal),'run')
 except ValueError:pass
 else:raise AssertionError('unfinished run measured')
 append_event(journal,'run','intervention_finished',{'intervention_id':'decision'})
 result=run_command(journal,'run','failing-tool',[sys.executable,'-c','print("retained failure"); raise SystemExit(3)'],root,root/'evidence',10)
 assert result['data']['exit_code']==3
 assert (root/'evidence/failing-tool.stdout').read_text()=='retained failure\n'
 append_event(journal,'run','run_finished',{'accepted':False})
 result=measurement(read_events(journal),'run')
 assert result['censored'] and result['accepted_capability_seconds'] is None and result['intervention_count']==1
 assert result['engineer_active_seconds']>=0 and result['elapsed_seconds']>0
 raw=journal.read_bytes();journal.write_bytes(raw.replace(b'retained failure',b'changed failure'))
 # A real retained event change, not an unchanged search/replace, must fail.
 changed=raw.replace(b'"exit_code":3',b'"exit_code":0');assert changed!=raw;journal.write_bytes(changed)
 try:read_events(journal)
 except ValueError:pass
 else:raise AssertionError('tampered journal verified')
 # A recovery cohort must stop before dispatch when the operator records PAUSE.
 # Retained evidence from a different cohort must remain untouched.
 cohort=root/'corrected cohort';cohort.mkdir()
 previous=root/'initial';previous.mkdir();(previous/'result.json').write_text('{"accepted":false}')
 schedule={'status':'frozen','tooling_directory':'unused','controller_digests':{},
           'runs':[{'id':'not-dispatched','block':1}],'seamwise_executable':'unused'}
 (cohort/'schedule.json').write_text(json.dumps(schedule));(cohort/'PAUSE').write_text('Review the observed permission denial.')
 with patch.object(sys,'argv',['run_schedule.py','--pilot-dir',str(cohort)]), patch.object(run_schedule.subprocess,'run') as dispatch:
  assert run_schedule.main()==2
  dispatch.assert_not_called()
 assert (previous/'result.json').read_text()=='{"accepted":false}'
 assert not (cohort/'results.json').exists(), 'paused work was presented as a completed cohort'
print('TOOLKIT_PILOT_RECORDING=PASS prospective intervals, censored failures, retained outputs, tamper detection, cohort pause')
PY
