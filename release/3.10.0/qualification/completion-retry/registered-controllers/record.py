#!/usr/bin/env python3
"""Record prospective pilot events and commands; never synthesize elapsed work."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import threading

from providers import permission_denials


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def read_events(path):
    previous = None
    events = []
    for index, raw in enumerate(Path(path).read_bytes().splitlines(), 1):
        row = json.loads(raw)
        if row.get('contract') != 'TaskPilotEvent/v1' or row.get('sequence') != index or row.get('previous_sha256') != previous:
            raise ValueError('pilot journal sequence or chain changed')
        expected = hashlib.sha256(canonical({k:v for k,v in row.items() if k != 'sha256'})).hexdigest()
        if row.get('sha256') != expected:
            raise ValueError('pilot journal event digest changed')
        events.append(row)
        previous = expected
    return events


def append_event(path, run_id, event, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        rows = read_events(path)
        row = dict(contract='TaskPilotEvent/v1', sequence=len(rows)+1,
                   previous_sha256=rows[-1]['sha256'] if rows else None,
                   observed_at=datetime.now(timezone.utc).isoformat(),
                   monotonic_ns=time.monotonic_ns(), run_id=run_id, event=event, data=data)
        row['sha256'] = hashlib.sha256(canonical(row)).hexdigest()
        handle.write(canonical(row)+b'\n')
        handle.flush()
        os.fsync(handle.fileno())
        return row


def measurement(events, run_id):
    rows = [r for r in events if r['run_id'] == run_id]
    starts = [r for r in rows if r['event'] == 'run_started']
    ends = [r for r in rows if r['event'] == 'run_finished']
    if len(starts) != 1 or len(ends) != 1 or starts[0]['sequence'] >= ends[0]['sequence']:
        raise ValueError('run has no unique prospective start and finish')
    if not starts[0]['data'].get('intervention_recording_enabled'):
        raise ValueError('intervention recording was not enabled at run start')
    active = {}; human_seconds = 0.0
    for row in rows:
        if row['sequence'] < starts[0]['sequence'] or row['sequence'] > ends[0]['sequence']:
            raise ValueError('run event lies outside the recorded observation interval')
        data = row['data']; identity = data.get('intervention_id')
        if row['event'] == 'intervention_started':
            if identity in active or not identity or data.get('actor_kind') != 'human':
                raise ValueError('invalid or overlapping intervention identity')
            if active:
                raise ValueError('overlapping human intervals require separate engineer accounting')
            active[identity] = row['monotonic_ns']
        elif row['event'] == 'intervention_finished':
            if identity not in active:
                raise ValueError('intervention finish has no recorded start')
            elapsed = row['monotonic_ns']-active.pop(identity)
            if elapsed < 0: raise ValueError('intervention clock moved backwards')
            human_seconds += elapsed / 1e9
    if active: raise ValueError('unfinished intervention cannot be measured')
    duration = ends[0]['monotonic_ns']-starts[0]['monotonic_ns']
    if duration < 0: raise ValueError('run clock moved backwards')
    accepted = ends[0]['data'].get('accepted') is True
    return {'engineer_active_seconds':human_seconds,
            'elapsed_seconds':duration/1e9,
            'accepted_capability_seconds':duration/1e9 if accepted else None,
            'censored':not accepted,
            'intervention_count':sum(r['event']=='intervention_started' for r in rows),
            'source_events':[starts[0]['sha256'],ends[0]['sha256']]}


def run_command(journal, run_id, phase, command, cwd, output_dir, timeout, prompt=None, stop_on_denial=False):
    """Execute one observed command. Workflow scheduling remains in TaskMesh."""
    output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    stdout=output_dir/(phase+'.stdout');stderr=output_dir/(phase+'.stderr')
    if stdout.exists() or stderr.exists(): raise ValueError('command output already exists; assign a new phase identity')
    append_event(journal,run_id,'command_started',{'phase':phase,'command':command,'cwd':str(cwd),'timeout_seconds':timeout})
    started=time.monotonic_ns(); timed_out=False
    stop_observer=threading.Event(); observed_denial=threading.Event()
    with stdout.open('xb') as out, stderr.open('xb') as err:
        process=subprocess.Popen(command,cwd=cwd,stdin=subprocess.PIPE if prompt is not None else subprocess.DEVNULL,
                                 stdout=out,stderr=err,start_new_session=True)
        def observe():
            # This observes the existing invocation; it never schedules work.
            # Read each stream independently and bound a partial JSONL event.
            with stdout.open('rb') as output, stderr.open('rb') as errors:
                pending = [b'', b'']; discarding = [False, False]
                while True:
                    final = stop_observer.is_set()
                    for index, stream in enumerate((output, errors)):
                        while chunk := stream.read(65536):
                            pieces = chunk.split(b'\n')
                            for part_index, part in enumerate(pieces):
                                if len(pending[index]) + len(part) > 2 * 1024 * 1024:
                                    pending[index] = b''; discarding[index] = True
                                if not discarding[index]: pending[index] += part
                                if part_index < len(pieces) - 1:
                                    if not discarding[index] and permission_denials(pending[index].decode('utf-8', errors='replace')):
                                        observed_denial.set()
                                        try: os.killpg(process.pid, signal.SIGKILL)
                                        except ProcessLookupError: pass
                                        return
                                    pending[index] = b''; discarding[index] = False
                        if final and not discarding[index] and permission_denials(pending[index].decode('utf-8', errors='replace')):
                            observed_denial.set()
                    if observed_denial.is_set():
                        try: os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError: pass
                        return
                    if final: return
                    stop_observer.wait(0.01)
        observer = threading.Thread(target=observe, daemon=True) if stop_on_denial else None
        if observer: observer.start()
        try:
            process.communicate(prompt.encode() if prompt is not None else None,timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait()
        except BaseException:
            os.killpg(process.pid,signal.SIGTERM)
            process.wait(timeout=10)
            append_event(journal,run_id,'command_interrupted',{'phase':phase,'exit_code':process.returncode})
            raise
        finally:
            stop_observer.set()
            if observer: observer.join()
    duration=(time.monotonic_ns()-started)/1e9
    evidence=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (stdout,stderr)]
    row=append_event(journal,run_id,'command_finished',{'phase':phase,'exit_code':process.returncode,
                     'timed_out':timed_out,'reported_permission_denial':observed_denial.is_set(),'duration_seconds':duration,'evidence':evidence})
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    event=sub.add_parser('event');event.add_argument('--journal',required=True);event.add_argument('--run-id',required=True)
    event.add_argument('--event',required=True);event.add_argument('--data',required=True,help='JSON event data; record immediately when the event happens')
    verify=sub.add_parser('verify');verify.add_argument('journal');verify.add_argument('--run-id')
    args=parser.parse_args()
    if args.action=='event':
        print(json.dumps(append_event(args.journal,args.run_id,args.event,json.loads(args.data)),indent=2))
    else:
        events=read_events(args.journal)
        print(json.dumps(measurement(events,args.run_id) if args.run_id else {'valid':True,'events':len(events)},indent=2))

if __name__=='__main__':main()
