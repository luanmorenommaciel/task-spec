#!/usr/bin/env python3
"""Run a fixed installed-chat corpus, retaining failures for independent review."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from chat_run import CASES

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--installed-skill', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--resume', action='store_true', help='Continue unobserved cases after explicit inspection; never rerun an observed case')
    args = parser.parse_args()
    engine, skill, folder = args.engine.resolve(), args.installed_skill.resolve(), args.out.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    registration = folder / 'schedule.json'
    if registration.exists() and not args.resume:
        raise SystemExit('This chat schedule already exists; inspect retained runs rather than replacing observations.')
    if args.resume and not registration.exists():
        raise SystemExit('No registered chat schedule exists to resume.')
    sources = [Path(__file__).resolve(), ROOT / 'tests/evals/toolkit/chat_run.py',
               ROOT / 'tests/evals/toolkit/providers.py', ROOT / 'tests/evals/toolkit/record.py']
    installation = json.loads(subprocess.check_output([sys.executable,
        str(engine/'tools/verify-toolkit.py'), '--engine', str(engine), '--runtime'], text=True))
    contract = {'contract':'TaskToolkitChatSchedule/v1', 'registered_at':datetime.now(timezone.utc).isoformat(),
                'cases':CASES, 'harnesses':['codex','claude'], 'engine':str(engine),
                'installed_skill':str(skill), 'skill_sha256':sha(skill/'SKILL.md'),
                'controllers':{str(p.relative_to(ROOT)):sha(p) for p in sources},
                'installed_resources':installation['resources'],
                'helper_sha256':sha(engine/'libexec/taskspec-meshd'),
                'qualification':'Every observation requires a separate review of actual actions and claims; successful process exit is insufficient.',
                'limits':'Synthetic state fixtures, one fresh journey per case and harness; not the real-work comparative delivery corpus.'}
    if args.resume:
        contract = json.loads(registration.read_text())
        if contract['engine'] != str(engine) or contract['installed_skill'] != str(skill) or contract['cases'] != CASES:
            raise SystemExit('Resume must use the same installed engine, skill, and registered requests.')
    else:
        registration.write_text(json.dumps(contract, indent=2)+'\n')
    python = engine / '.taskspec/runtime/decompose/bin/python'
    observations = json.loads((folder/'progress.json').read_text())['observations'] if args.resume and (folder/'progress.json').exists() else []

    def run(pair):
        case, harness = pair
        prior = [r for r in observations if r['case'] == case and r['harness'] == harness]
        if prior:
            return prior[0]
        log = folder / f'{case}-{harness}.controller.log'
        command = [str(python), str(ROOT/'tests/evals/toolkit/chat_run.py'), '--case', case,
                   '--harness', harness, '--engine', str(engine), '--installed-skill', str(skill),
                   '--out', str(folder/'runs')]
        with log.open('x') as out:
            result = subprocess.run(command, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT)
        row = {'case':case, 'harness':harness, 'exit_code':result.returncode,
               'controller_log':str(log.relative_to(folder)), 'review_status':'pending'}
        if result.returncode == 0:
            output = json.loads(log.read_text())
            observation = json.loads((Path(output['retained'])/'observation.json').read_text())
            row['needs_permission_review'] = bool(observation.get('reported_permission_denials'))
        print(json.dumps(row), flush=True)
        return row

    with ThreadPoolExecutor(max_workers=2) as pool:
        for case in CASES:
            if len([r for r in observations if r['case'] == case]) == 2:
                continue
            if (folder/'PAUSE').exists():
                print(json.dumps({'state':'paused','before_case':case}), flush=True)
                return 2
            for relative, expected in contract['controllers'].items():
                if sha(ROOT/relative) != expected:
                    raise RuntimeError('Registered chat controller changed: '+relative)
            if sha(skill/'SKILL.md') != contract['skill_sha256']:
                raise RuntimeError('Installed skill changed during chat qualification')
            for relative, expected in contract['installed_resources'].items():
                if sha(engine/relative) != expected:
                    raise RuntimeError('Installed engine changed during chat qualification: '+relative)
            if sha(engine/'libexec/taskspec-meshd') != contract['helper_sha256']:
                raise RuntimeError('Installed helper changed during chat qualification')
            rows = list(pool.map(run, [(case,harness) for harness in contract['harnesses']]))
            observations.extend(row for row in rows if row not in observations)
            (folder/'progress.json').write_text(json.dumps({'observations':observations,
                    'qualified':False, 'state':'awaiting_behavior_review'}, indent=2)+'\n')
            if any(row['exit_code'] != 0 or row.get('needs_permission_review') for row in rows):
                (folder/'PAUSE').write_text('A harness, fixture, or permission check failed; inspect retained evidence before any further dispatch.\n')
                return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
