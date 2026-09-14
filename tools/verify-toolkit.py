#!/usr/bin/env python3
"""Verify installed toolkit resources and private component identity."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--engine',type=Path,required=True);parser.add_argument('--source',type=Path);parser.add_argument('--target',type=Path);parser.add_argument('--runtime',action='store_true')
parser.add_argument('--quiet',action='store_true')
parser.add_argument('--helper',type=Path,help='installed helper path, including checkout/symlink mode')
args=parser.parse_args();engine=args.engine.resolve()

def resource_inventory(root):
 resources={'SKILL.md','VERSION','LICENSE'}
 for directory in ('src','bin','spec','harness','tools','.claude-plugin'):
  for path in (root/directory).rglob('*'):
   relative=path.relative_to(root)
   generated=relative.as_posix() in ('spec/conformance/results.json','spec/conformance/_state.yaml') or relative.parts[:3]==('spec','conformance','_workdir')
   if path.is_file() and not generated and '__pycache__' not in path.parts and path.suffix not in ('.pyc','.pyo'):
    resources.add(str(path.relative_to(root)))
 resources.update(str(p.relative_to(root)) for p in (root/'docs/guides/toolkit').glob('*.md'))
 return sorted(resources)

def verify_skill_manifests(root, version):
 for relative in ('.claude-plugin/plugin.json', 'harness/claude-code/plugin.json'):
  manifest=root/relative
  value=json.loads(manifest.read_text())
  if value.get('version')!=version:raise ValueError('plugin version mismatch: '+relative)
  base=manifest.parent.parent if manifest.parent.name=='.claude-plugin' else manifest.parent
  entries=value.get('skills', [])
  if isinstance(entries,str):entries=[entries]
  if not isinstance(entries,list) or not entries:raise ValueError('plugin has no skill directories: '+relative)
  for entry in entries:
   if not isinstance(entry,str):raise ValueError('invalid plugin skill directory: '+relative)
   directory=(base/entry).resolve()
   if Path(entry).is_absolute() or not directory.is_relative_to(base.resolve()) or not directory.is_dir() or not (directory/'SKILL.md').is_file():
    raise ValueError('plugin skill directory must contain SKILL.md: '+relative+' -> '+entry)

try:
 version=(engine/'VERSION').read_text().strip()
 verify_skill_manifests(engine, version)
 resources=resource_inventory(engine)
 if args.source:
  expected=resource_inventory(args.source)
  if resources!=expected:
   missing=sorted(set(expected)-set(resources)); unexpected=sorted(set(resources)-set(expected))
   raise ValueError(f'installed resource inventory differs (missing={missing}, unexpected={unexpected}); use --force for an explicit replacement')
  for relative in resources:
   if (args.source/relative).read_bytes()!=(engine/relative).read_bytes():raise ValueError('installed resource drift: '+relative+'; use --force for an explicit replacement')
 if args.target:
  for harness in ['.agents','.claude','.cursor','.grok']:
   skill=args.target/harness/'skills/task-spec'
   if (skill/'SKILL.md').read_bytes()!=(engine/'SKILL.md').read_bytes():raise ValueError('installed skill parity: '+harness)
   for relative in resources:
    if relative.startswith('docs/') and (skill/relative).read_bytes()!=(engine/relative).read_bytes():raise ValueError('installed guide parity: '+harness+'/'+relative)
 if args.runtime:
  runtime=engine/'.taskspec/runtime/decompose'
  receipt=json.loads((runtime/'taskspec-runtime.json').read_text())
  if receipt.get('version')!=version or receipt.get('lock_digest')!=hashlib.sha256((engine/'src/decompose/requirements.lock').read_bytes()).hexdigest():raise ValueError('private runtime receipt mismatch')
  subprocess.run([str(runtime/'bin/python'),'-c','import sys,yaml,jsonschema; assert sys.version_info >= (3,11)'],check=True)
  helper=args.helper or engine/'libexec/taskspec-meshd'
  identity=json.loads(subprocess.check_output([str(helper),'--version-json'],text=True))
  if identity.get('product_version')!=version:raise ValueError('TaskMesh helper version mismatch')
 if args.quiet:print(f'TOOLKIT=READY version={version} resources={len(resources)} runtime_checked={str(args.runtime).lower()}')
 else:print(json.dumps({'contract':'TaskToolkitInstallation/v1','ready':True,'version':version,'resources':{p:hashlib.sha256((engine/p).read_bytes()).hexdigest() for p in resources},'runtime_checked':args.runtime}))
except (OSError,ValueError,subprocess.CalledProcessError) as error:
 print('TOOLKIT=INVALID '+str(error),file=sys.stderr);raise SystemExit(1)
