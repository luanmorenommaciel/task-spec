#!/usr/bin/env python3
"""Read-only verification of an exact v3 authorization for managed attempts."""
import argparse
import hashlib
import hmac
from pathlib import Path
import sys

from stamp import signing_key
from task_revision import revision
from taskspec_data import frontmatter


def verify(spec: Path, expected_revision: str) -> None:
    fm = frontmatter(spec.read_text())
    actual = revision(spec)['task_revision_digest']
    if actual != expected_revision or fm.get('signed_off') is not True:
        raise ValueError('task revision or authorization changed')
    key = signing_key(spec)
    if not key:
        raise ValueError('repository signing key unavailable')
    payload = (f'contract=TaskAuthorization/v3\ntask_revision_digest={actual}\n'
               f'signed_off=true\nsigned_off_by={fm.get("signed_off_by")}\nsigned_off_at={fm.get("signed_off_at")}')
    signature = 'hmac-sha256-v3:' + hashlib.sha256(key.encode()).hexdigest()[:8] + ':' + hmac.new(key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, str(fm.get('signed_off_sig', ''))):
        raise ValueError('task HMAC authentication failed')
    if fm.get('provenance') is not None:
        from provenance import verify_task
        from workspace import resolve_workspace
        verify_task(resolve_workspace(spec, environ={}), str(fm['id']), fm['provenance'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec'); parser.add_argument('revision'); parser.add_argument('--origin')
    args = parser.parse_args()
    try:
        verify(Path(args.spec), args.revision)
        if args.origin: verify(Path(args.origin), args.revision)
    except (OSError, ValueError) as error:
        print('AUTHORITY_CHANGED: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
