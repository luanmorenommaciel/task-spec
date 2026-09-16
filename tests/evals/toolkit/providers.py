"""Pinned harness invocations and explicit usage accounting for the pilot."""
from __future__ import annotations
import json
from pathlib import Path
import re
import subprocess


def observed_version(harness, expected):
    """Read the actual CLI identity and refuse drift from the registered version."""
    if harness not in ('codex', 'claude'):
        raise ValueError('Unknown pilot harness: ' + harness)
    if not isinstance(expected, str) or not expected.strip():
        raise ValueError('Comparative runs require a registered harness version')
    output = subprocess.check_output([harness, '--version'], text=True,
                                     stderr=subprocess.STDOUT, timeout=10).strip()
    pattern = r'(?<!\d)\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?'
    actual = re.search(pattern, output)
    pinned = re.search(pattern, expected)
    if not actual or not pinned or actual.group() != pinned.group():
        raise ValueError(f'{harness}: observed version {output!r} differs from registered {expected!r}; re-register before dispatch')
    return output


def argv(harness,workspace,prompt):
    if harness=='codex':
        return ['codex','exec','--ignore-user-config','--ephemeral','--sandbox','workspace-write','--cd',str(workspace),'--json','--color','never','--model','gpt-6-astra','-c','model_reasoning_effort="high"','-c','model_context_window=262144','-c','model_auto_compact_token_limit=196608','-c','service_tier="default"','-'],prompt
    return ['claude','-p',prompt,'--model','claude-opus-5','--output-format','stream-json','--verbose','--no-session-persistence','--permission-mode','acceptEdits','--permission-prompts','none','--allowedTools','Read,Edit,Write,Bash','--restricted','--tools','Read,Edit,Write,Bash','--strict-mcp-config','--mcp-config','{"mcpServers":{}}'],None


def adapter(harness):
    command,_=argv(harness,'{workspace}','{prompt}')
    return {'contract':'TaskMeshAdapter/v1','name':harness+'-native','harness':harness,'executable':command[0],'version_args':['--version'],'command':command[1:],'prompt_mode':'stdin' if harness=='codex' else 'argument','event_format':'jsonl','assurance_modes':['supervised']}


def usage(harness,outputs):
    invocations=[]
    for path,text in outputs:
        rows=[]
        for line in text.splitlines():
            try:row=json.loads(line)
            except ValueError:continue
            if isinstance(row,dict):rows.append(row)
        if harness=='codex':
            reports=[r.get('usage') for r in rows if r.get('type')=='turn.completed' and isinstance(r.get('usage'),dict)]
            if not reports:
                invocations.append({'path':path,'known':False});continue
            totals={k:sum(r.get(k,0) for r in reports) for k in ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens']}
            if any(k not in r for r in reports for k in ['input_tokens','cached_input_tokens','output_tokens']):
                invocations.append({'path':path,'known':False,'reported':reports});continue
            # Context and service tier are pinned in argv; the rate card is retained.
            cost=((totals['input_tokens']-totals['cached_input_tokens'])*10+totals['cached_input_tokens']+totals['cache_write_input_tokens']*12.5+totals['output_tokens']*50)/1e6
            invocations.append({'path':path,'known':True,'tokens':totals,'usd':cost,'basis':'api_equivalent_estimate'})
        else:
            reports=[r for r in rows if r.get('type')=='result' and isinstance(r.get('total_cost_usd'),(float,int))]
            if len(reports)!=1:
                invocations.append({'path':path,'known':False});continue
            invocations.append({'path':path,'known':True,'usd':reports[0]['total_cost_usd'],'model_usage':reports[0].get('modelUsage'),'basis':'harness_reported'})
    complete=bool(invocations) and all(r['known'] for r in invocations)
    return {'complete':complete,'cost_including_failures':sum(r['usd'] for r in invocations) if complete else None,'cost_basis':'api_equivalent_estimate' if harness=='codex' else 'harness_reported','invocations':invocations}


def permission_denials(text):
    found = []
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict):
            continue
        if row.get('type') == 'result' and isinstance(row.get('permission_denials'), list):
            found.extend(row['permission_denials'])
        if row.get('type') == 'user':
            message = row.get('message', {})
            content = message.get('content', []) if isinstance(message, dict) else []
            for result in content if isinstance(content, list) else []:
                if not isinstance(result, dict) or result.get('type') != 'tool_result' or result.get('is_error') is not True:
                    continue
                output = json.dumps(result.get('content', '')).lower()
                if any(term in output for term in ('permission denied', 'permission was denied', '--restricted confines', 'requires explicit approval')):
                    found.append({'source':'failed native tool result', 'tool_use_id':result.get('tool_use_id'), 'output':result.get('content')})
        item = row.get('item', {})
        if not isinstance(item, dict):
            continue
        if item.get('type') == 'command_execution' and item.get('exit_code') not in (0, None):
            output = item.get('aggregated_output', '')
            if isinstance(output, str) and any(term in output.lower() for term in ('permission denied', 'operation not permitted')):
                found.append({'command':item.get('command'), 'exit_code':item['exit_code'],
                              'output':output, 'source':'failed command output'})
    return found
