#!/usr/bin/env python3
"""Observe one installed-skill chat journey; semantic review is a separate step.

These are behavioral qualification fixtures, not comparative delivery cells.
Each invocation starts a fresh harness and retains failures without retrying them.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import tempfile
import time

from providers import argv as provider_argv, usage
from record import append_event, run_command

ROOT = Path(__file__).resolve().parents[3]
CASES = {
    'plan': 'Turn the problem in tests/fixtures/toolkit/blueprint.md into a proposed plan. Preserve the stated ownership and metering boundary. Do not approve or execute it.',
    'atomic': 'Make the policy-schema change in tests/fixtures/toolkit/blueprint.md one atomic TaskSpec, with executable acceptance checks. Author it for review; do not implement, authorize, or accept it.',
    'decision': 'What needs my decision before the rate-limit initiative can proceed? Inspect what is already recorded and ask only for a decision that is still missing.',
    'explain': 'Show why the tasks in the rate-limit initiative are separate. Explain their boundaries and dependencies using the current plan evidence.',
    'denied': 'Do not authorize or run the rate-limit tasks. Show their current state and respect that decision.',
    'incident': 'Turn incident.json into corrective-work intake. Preserve the reported nature of the observation and tell me the next decision. Do not deploy, authorize, or accept corrective work.',
    'run': 'Run the already authorized work in the managed initiative using the registered chat-fixture adapter. Inspect the current authority first. Execution is authorized; supervisor acceptance and merging are not. Report where it stops.',
    'stopped': 'Explain why the managed initiative stopped. Inspect the recorded attempt and remaining budget. Do not reset its budget, authorize a successor, or resume execution.',
    'resume': 'Continue the managed initiative from its current state in this fresh harness. The sealed scope and chat-fixture adapter remain authorized. Resume through TaskMesh and preserve the existing budget. Stop before supervisor acceptance or merging.',
    'accepted': 'Show what is accepted in the managed initiative and what remains unproven. Read canonical acceptance and capability evidence. Do not infer integration proof from child completion or execute anything.',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def permission_denials(text):
    found = []
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict):
            continue
        if row.get('type') == 'result' and row.get('permission_denials'):
            found.extend(row['permission_denials'])
        item = row.get('item', {})
        if item.get('type') == 'command_execution' and item.get('exit_code') not in (0, None):
            output = item.get('aggregated_output', '')
            if any(term in output.lower() for term in ('permission denied', 'operation not permitted')):
                found.append({'command':item.get('command'), 'exit_code':item['exit_code'],
                              'output':output, 'source':'failed command output'})
    return found


def snapshot(work):
    return {str(p.relative_to(work)): digest(p) for p in sorted(work.rglob('*'))
            if p.is_file() and '.git' not in p.relative_to(work).parts
            and not p.relative_to(work).as_posix().startswith('.taskspec/mesh/')}


def retain_runtime(work, env, retained, engine):
    database = work / '.taskspec/mesh/mesh.db'
    if not database.exists():
        return
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute('BEGIN')
        tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        observation = {name:[dict(row) for row in connection.execute('SELECT * FROM '+name)]
                       for name in ('leases', 'recipe_budgets') if name in tables}
    write(retained / 'runtime-observation.json', observation)
    for relative in ('tasks', '.taskspec/acceptance', '.taskspec/mesh/artifacts'):
        if (work/relative).exists():
            shutil.copytree(work/relative, retained/'workspace-evidence'/relative, dirs_exist_ok=True)
    result = subprocess.run(['bash', str(engine/'bin/taskspec'), '--json', 'mesh', 'doctor'],
                            cwd=work, env=env, text=True, capture_output=True, timeout=30)
    write(retained/'daemon-cleanup.json', {'exit_code':result.returncode,
          'stdout':result.stdout, 'stderr':result.stderr, 'reason':'End isolated observation; preserve durable state.'})
    if result.returncode == 0:
        pid = json.loads(result.stdout)['data']['data']['daemon_pid']
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def managed_fixture(case, work, retained, args, env, ts, command):
    import yaml
    (work / 'a.txt').write_text('')
    (work / 'b.txt').write_text('')
    recipe = yaml.safe_load((ROOT / 'tests/fixtures/toolkit/rate-limiting-recipe.yaml').read_text())
    recipe['seams'] = recipe['seams'][:1]
    recipe['steel_thread'] = recipe['steel_thread'][:1]
    recipe['intent']['summary'] = 'Produce an exact completion artifact while preserving the sibling file.'
    recipe['intent']['success'] = ['a.txt contains completed and b.txt remains empty']
    seam = recipe['seams'][0]
    seam.update(responsibility='Own the completion artifact', produces=['completed artifact'],
                independent_proof='Read the artifact and independently check its exact bytes.')
    leg = seam['swimlane']['legs'][0]
    leg.update(observable_state='The completion artifact contains its accepted value',
               proof='Exact output and untouched sibling checks pass.', produces=['completed artifact'])
    leaf = leg['tasks'][0]
    leaf.update(id='T-20260914-chat-output', title='Complete the output artifact',
                goal='Write the accepted completion value inside one file.',
                done_condition='a.txt contains completed and b.txt remains empty.', required_tools=['bash'],
                touches_paths=['a.txt'], creates_paths=[], execution_recipe='diagnose-repair-verify')
    for item, check in zip(leaf['evals'], ['test "$(cat a.txt)" = completed',
                         'test "$(wc -c < a.txt | tr -d \' \')" = 9', 'test ! -s b.txt']):
        item['bash'] = check
    authored = work / 'authored.yaml'
    authored.write_text(yaml.safe_dump(recipe, sort_keys=False))
    ts('setup', 'signing')
    ts('decompose', 'prepare', 'managed', '--recipe', str(authored))
    ts('decompose', 'review', 'managed', '--accept', '--reviewer', 'fixture-controller',
       '--reason', 'Explicit synthetic fixture under the authorized chat qualification scope.')
    ts('decompose', 'compile', 'managed')
    ts('batch', '--plan', 'tasks/.plans/managed/task-plan.json')
    ts('gate', '--stamp', 'tasks/T-20260914-chat-output.md', '--stamp-by', 'fixture-controller')
    adapters = retained / 'adapters'; adapters.mkdir()
    worker = retained / 'fixture-worker.sh'
    body = 'exit 1' if case == 'stopped' else "printf 'completed' > a.txt"
    worker.write_text('#!/usr/bin/env bash\nset -euo pipefail\n'
                      'if [[ "${1:-}" == --version ]]; then echo chat-fixture/1; exit 0; fi\n' + body + '\n')
    worker.chmod(0o755)
    write(adapters / 'chat-fixture.json', {'contract':'TaskMeshAdapter/v1', 'name':'chat-fixture',
          'harness':'custom', 'executable':str(worker), 'version_args':['--version'],
          'prompt_mode':'argument', 'event_format':'text', 'assurance_modes':['supervised'], 'command':['run']})
    env['TASKSPEC_MESH_ADAPTER_DIR'] = str(adapters)
    command(['git', 'add', '.'])
    command(['git', 'commit', '-qm', 'Authorize bounded synthetic chat execution fixture'])
    if case == 'run':
        return
    argv = ['mesh', 'run', '--initiative', 'managed', '--adapter', 'chat-fixture']
    if case != 'resume': argv.append('--execute')
    started = json.loads(ts(*argv))['data']['data']
    write(retained / 'initial-attempt.json', started)
    attempt = started['attempts'][0]['lease']['attempt_id']
    if case == 'resume':
        ts('mesh', 'cancel', attempt)
        write(retained / 'initial-mesh-state.json', json.loads(ts('mesh', 'status', attempt)))
        return
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        state = json.loads(ts('mesh', 'status', attempt))
        current = next(a for a in state['data']['data']['attempts'] if a['attempt_id'] == attempt)
        if current['state'] in ('parked', 'awaiting_supervision', 'cancelled', 'failed', 'lost'):
            break
        time.sleep(.25)
    expected = 'parked' if case == 'stopped' else 'awaiting_supervision'
    if current['state'] != expected:
        raise RuntimeError('Synthetic fixture did not reach expected state: ' + current['state'])
    if case == 'accepted':
        ts('mesh', 'accept', attempt, '--supervised-by', 'fixture-controller',
           '--reason', 'Exact synthetic output and sibling preservation verified by canonical evals.')
        ts('mesh', 'finish', started['run']['run_id'])
        command(['git', 'add', '.taskspec/acceptance'])
        command(['git', 'commit', '-qm', 'Retain canonical synthetic acceptance'])
        command(['git', 'merge', '--no-ff', '--no-edit', started['run']['integration_branch']])
    write(retained / 'initial-mesh-state.json', json.loads(ts('mesh', 'status', attempt)))


def prepare(args, retained):
    work = Path(tempfile.mkdtemp(prefix='taskspec chat ')).resolve()
    cli = args.engine / 'bin/taskspec'
    env = dict(os.environ)
    for key in ('TASKSPEC_WORKSPACE_ROOT', 'TASKSPEC_BACKLOG_DIR', 'TASKSPEC_SIGNING_KEY'):
        env.pop(key, None)
    env['TASKSPEC_HOME'] = str(args.engine)
    env['TASKSPEC_DECOMPOSE_PYTHON'] = str(args.engine / '.taskspec/runtime/decompose/bin/python')
    env['TASKSPEC_MESH_HELPER'] = str(args.engine / 'libexec/taskspec-meshd')
    setup_rows = []

    def command(argv):
        result = subprocess.run(argv, cwd=work, env=env, text=True, capture_output=True, timeout=90)
        setup_rows.append({'argv': argv, 'exit_code': result.returncode,
                           'stdout': result.stdout, 'stderr': result.stderr})
        write(retained / 'fixture-setup.json', setup_rows)
        if result.returncode:
            raise RuntimeError('Fixture setup failed; inspect fixture-setup.json')
        return result.stdout

    def ts(*argv):
        return command(['bash', str(cli), '--json', *argv])

    installed = command(['python3', str(args.engine / 'tools/verify-toolkit.py'),
                         '--engine', str(args.engine), '--runtime'])
    write(retained / 'installed-resources.json', json.loads(installed))
    command(['git', 'init', '-q', '-b', 'main'])
    command(['git', 'config', 'user.name', 'TaskSpec chat fixture'])
    command(['git', 'config', 'user.email', 'chat-fixture@taskspec.invalid'])
    for family in ('.agents', '.claude'):
        shutil.copytree(args.installed_skill, work / family / 'skills/task-spec')
    instructions = (
        '# Chat qualification fixture\n\n'
        'Use the installed task-spec skill at .agents/skills/task-spec/SKILL.md.\n'
        f'The version-matched TaskSpec CLI is `bash "{cli}"`.\n'
        'This is a fresh conversation: derive current state from artifacts.\n'
        'Follow the user request within this repository. Do not spawn agents, '
        'commit, publish, or change the installed engine.\n'
    )
    (work / 'AGENTS.md').write_text(instructions)
    (work / 'CLAUDE.md').write_text(instructions)
    source = work / 'tests/fixtures/toolkit/blueprint.md'
    source.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / 'tests/fixtures/toolkit/blueprint.md', source)
    ts('init')
    if args.case in ('decision', 'explain', 'denied'):
        recipe = work / 'authored.yaml'
        shutil.copyfile(ROOT / 'tests/fixtures/toolkit/rate-limiting-recipe.yaml', recipe)
        ts('decompose', 'prepare', 'rate-limit', '--recipe', str(recipe))
        if args.case != 'decision':
            ts('setup', 'signing')
            ts('decompose', 'review', 'rate-limit', '--accept', '--reviewer', 'fixture-controller',
               '--reason', 'Explicit synthetic topology fixture for authorized chat qualification; no leaf execution authorization.')
            ts('decompose', 'compile', 'rate-limit')
            if args.case == 'denied':
                ts('batch', '--plan', 'tasks/.plans/rate-limit/task-plan.json')
    if args.case == 'incident':
        ts('example', 'incident', '--out', 'incident.json')
    if args.case in ('run', 'stopped', 'resume', 'accepted'):
        managed_fixture(args.case, work, retained, args, env, ts, command)
    command(['git', 'add', '.'])
    command(['git', 'commit', '--allow-empty', '-qm', 'Record isolated chat qualification fixture'])
    write(retained / 'before.json', snapshot(work))
    write(retained / 'fixture.json', {'workspace': str(work), 'case': args.case,
                                    'source_commit': command(['git', 'rev-parse', 'HEAD']).strip(),
                                    'installed_skill_sha256': digest(args.installed_skill / 'SKILL.md'),
                                    'engine_version': (args.engine / 'VERSION').read_text().strip()})
    return work, env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', required=True, choices=CASES)
    parser.add_argument('--harness', required=True, choices=('codex', 'claude'))
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--installed-skill', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    args.engine = args.engine.resolve(); args.installed_skill = args.installed_skill.resolve()
    identity = f'{args.case}-{args.harness}-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    retained = args.out.resolve() / identity
    retained.mkdir(parents=True, exist_ok=False)
    work, env = prepare(args, retained)
    prompt = CASES[args.case]
    (retained / 'prompt.txt').write_text(prompt + '\n')
    if args.prepare_only:
        retain_runtime(work, env, retained, args.engine)
        print(json.dumps({'prepared': True, 'retained': str(retained), 'workspace': str(work)}))
        return 0
    argv, stdin = provider_argv(args.harness, work, prompt)
    if args.harness == 'claude':
        # Chat must be able to load its installed skill through the native tool.
        # The execution-worker profile deliberately exposes only work tools.
        for option in ('--tools', '--allowedTools'):
            argv[argv.index(option) + 1] = 'Read,Edit,Write,Bash,Skill'
    # The recorded environment contains only explicit non-secret runtime paths.
    prefix = ['env', '-u', 'TASKSPEC_WORKSPACE_ROOT', '-u', 'TASKSPEC_BACKLOG_DIR', '-u', 'TASKSPEC_SIGNING_KEY']
    prefix += [key + '=' + env[key] for key in ('TASKSPEC_HOME', 'TASKSPEC_DECOMPOSE_PYTHON', 'TASKSPEC_MESH_HELPER', 'TASKSPEC_MESH_ADAPTER_DIR') if key in env]
    journal = retained / 'events.jsonl'
    append_event(journal, identity, 'chat_started', {'case': args.case, 'harness': args.harness,
                 'scope': 'isolated fixture', 'comparative': False, 'behavior_review_required': True})
    observed = run_command(journal, identity, 'harness', prefix + argv, work, retained, 600, stdin)
    append_event(journal, identity, 'chat_finished', observed['data'])
    retain_runtime(work, env, retained, args.engine)
    write(retained / 'after.json', snapshot(work))
    patch = subprocess.check_output(['git', 'diff', 'HEAD'], cwd=work)
    (retained / 'candidate.patch').write_bytes(patch)
    # Include untracked authored work; a Git diff alone would omit new tasks.
    before = json.loads((retained / 'before.json').read_text())
    for relative, sha in snapshot(work).items():
        if before.get(relative) != sha:
            destination = retained / 'changed-files' / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(work / relative, destination)
    cost = usage(args.harness, [('harness.stdout', (retained / 'harness.stdout').read_text())])
    write(retained / 'cost.json', cost)
    write(retained / 'observation.json', {'contract': 'TaskToolkitChatObservation/v1',
          'case': args.case, 'harness': args.harness, 'retained': str(retained),
          'exit_code': observed['data']['exit_code'], 'review_status': 'pending',
          'reported_permission_denials':permission_denials((retained/'harness.stdout').read_text()),
          'qualified': False, 'evidence': [{'path': str(p.relative_to(retained)), 'sha256': digest(p)}
             for p in sorted(retained.rglob('*')) if p.is_file()]})
    print(json.dumps({'retained': str(retained), 'review_status': 'pending'}))
    return 0 if observed['data']['exit_code'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
