#!/usr/bin/env python3
"""Stop a qualification chat before another tool after a recorded denial.

This is a test-harness hook, not an execution runner or permission grant. It reads
the controller's existing JSONL stream and recognizes the retained Claude denial
formats. A failing eval or a usage error is not treated as a permission denial.
"""
import argparse
import json
from pathlib import Path
import sys


def stop(reason):
    # preventContinuation stops the next model turn; explicitly deny the
    # pending tool as well. The pinned harness otherwise executes that tool.
    return {'continue': False, 'stopReason': reason,
            'hookSpecificOutput': {'hookEventName': 'PreToolUse',
                                   'permissionDecision': 'deny',
                                   'permissionDecisionReason': reason}}


def denied(rows):
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get('type') == 'result' and row.get('permission_denials'):
            return True
        if row.get('type') != 'user':
            continue
        for item in row.get('message', {}).get('content', []):
            if not isinstance(item, dict) or item.get('type') != 'tool_result' or not item.get('is_error'):
                continue
            value = item.get('content', '')
            text = (value if isinstance(value, str) else json.dumps(value)).lower()
            if any(term in text for term in ('permission denied', 'permission was denied',
                                             '--restricted confines', 'requires explicit approval')):
                return True
    return False


def decision(path):
    rows = []
    for line in path.read_text().splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            # The writer may still be appending its newest line. Earlier complete
            # records remain available; no partial record can authorize a tool.
            continue
    if denied(rows):
        return stop('TASKSPEC_PERMISSION_DENIED: a prior tool action was denied. Stop and report the boundary; do not retry through another tool or path.')
    return {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--events', type=Path, required=True)
    args = parser.parse_args()
    try:
        event = json.load(sys.stdin)
        if event.get('hook_event_name') != 'PreToolUse':
            raise ValueError('expected PreToolUse')
        output = decision(args.events)
    except (OSError, ValueError, TypeError, AttributeError) as error:
        output = stop('TASKSPEC_GUARD_UNAVAILABLE: cannot inspect the prior tool boundary: '+str(error))
    print(json.dumps(output))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
