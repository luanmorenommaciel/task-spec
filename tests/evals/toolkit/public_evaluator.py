"""Workspace-readable public pilot evidence with signed integrity checks.

The controller retains its external evaluator for independent assessments.
These exact public inputs are shared by all comparison arms before dispatch.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import shlex
import sys

DIRECTORY = Path('tests/fixtures/toolkit/public-evaluator')
SCRIPT = Path('tests/evals/toolkit/evaluate_issue.py')
INPUTS = (SCRIPT, Path('spec/conformance/toolkit/execution-recipe.json'),
          Path('docs/examples/incident.json'))


def install(tooling, workspace):
    manifest = {}
    for relative in INPUTS:
        content = (tooling / relative).read_bytes()
        target = workspace / DIRECTORY / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        manifest[str(DIRECTORY / relative)] = hashlib.sha256(content).hexdigest()
    return manifest


def verify(workspace, manifest):
    for relative, expected in manifest.items():
        path = workspace / relative
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('public evaluator changed: ' + relative)


def command(manifest, scenario):
    # Digests are literals in the eval command, and therefore in the HMAC body.
    # Execute the checked script bytes rather than reopening a mutable path.
    script = str(DIRECTORY / SCRIPT)
    program = (
        'import hashlib,pathlib,sys; '
        f'manifest={manifest!r}; '
        'contents={p:pathlib.Path(p).read_bytes() for p in manifest}; '
        'valid=all(not pathlib.Path(p).is_symlink() and hashlib.sha256(contents[p]).hexdigest()==h for p,h in manifest.items()); '
        'sys.exit("public evaluator integrity check failed") if not valid else None; '
        f'sys.argv=[{script!r},{scenario!r},"--root","."]; '
        f'exec(compile(contents[{script!r}],{script!r},"exec"),{{"__name__":"__main__","__file__":{script!r}}})'
    )
    return shlex.join([sys.executable, '-c', program])
