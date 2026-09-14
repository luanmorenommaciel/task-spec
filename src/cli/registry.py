#!/usr/bin/env python3
"""One command metadata source for help, shell completion, and reference output."""
import json
from pathlib import Path
import shlex
import sys

ROOT = Path(__file__).resolve().parents[2]
COMMANDS = json.loads((ROOT / 'src/cli/commands.json').read_text())


def words():
    result = {'': sorted({key.split()[0] for key in COMMANDS})}
    for key, row in COMMANDS.items():
        result[key] = sorted(set(row['flags'] + ['--help', '--json', '--dry-run'] + [x[len(key)+1:] for x in COMMANDS if x.startswith(key+' ') and ' ' not in x[len(key)+1:]]))
    return result


def completion_key(shell):
    """Follow registered command paths, ignoring global flags and operands."""
    print('  key=""')
    print('  local index word candidate')
    if shell == 'bash':
        print('  for ((index=1; index<COMP_CWORD; index++)); do\n    word="${COMP_WORDS[index]}"')
    else:
        print('  for ((index=2; index<CURRENT; index++)); do\n    word="${words[index]}"')
    print('    case "$word" in -*) continue ;; esac\n    candidate="${key:+$key }$word"\n    case "$candidate" in')
    for key in COMMANDS:
        print('      '+shlex.quote(key)+') key="$candidate" ;;')
    print('    esac\n  done')


def main():
    mode = sys.argv[1]
    if mode == 'help':
        key = ' '.join(sys.argv[2:])
        if key:
            if key not in COMMANDS:
                print('Unknown command: '+key+'; use taskspec help', file=sys.stderr); return 2
            print(COMMANDS[key]['usage']); print(COMMANDS[key]['summary'])
        else:
            print('TaskSpec — atomic contracts and native AI engineering toolkit\n\nUsage: taskspec [--json] [--dry-run] <command> [options]\n')
            for key,row in COMMANDS.items():
                if ' ' not in key: print(f'  {key:18} {row["summary"]}')
            print('\nUse taskspec help <command>, taskspec guide <topic>, or taskspec agent-context.')
    elif mode == 'completion':
        shell = sys.argv[2] if len(sys.argv)>2 else ''
        catalog = words()
        if shell in ('bash','zsh'):
            print('''_taskspec_complete() {
  local key choices
''')
            completion_key(shell)
            print('  case "$key" in')
            for key, values in catalog.items(): print('    '+shlex.quote(key)+') choices='+shlex.quote(' '.join(values))+' ;;')
            print('    *) choices="--help --json --dry-run" ;;\n  esac')
            if shell == 'bash':
                print('  COMPREPLY=( $(compgen -W "$choices" -- "${COMP_WORDS[COMP_CWORD]}") )\n}\ncomplete -F _taskspec_complete taskspec')
            else: print('  compadd -- ${(z)choices}\n}\ncompdef _taskspec_complete taskspec')
        elif shell == 'fish':
            for key, values in catalog.items():
                condition='__fish_use_subcommand' if not key else '__fish_seen_subcommand_from '+key.split()[-1]
                for word in values:
                    flag='-l '+word[2:] if word.startswith('--') else '-a '+shlex.quote(word)
                    print('complete -c taskspec -n '+shlex.quote(condition)+' '+flag)
        else:
            print('Usage: taskspec completion bash|zsh|fish',file=sys.stderr);return 2
    elif mode == 'reference':
        print('# CLI reference\n\nGenerated from `src/cli/commands.json`. Global `--json` emits TaskSpecCLIResult/v1.\n')
        for key,row in COMMANDS.items(): print('## '+key+'\n\n```text\n'+row['usage']+'\n```\n\n'+row['summary']+'\n')
    return 0


if __name__ == '__main__': raise SystemExit(main())
