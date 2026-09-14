#!/usr/bin/env python3
"""Provision the locked decomposition runtime without touching global Python."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil

ROOT=Path(__file__).resolve().parents[2]
lock=ROOT/'src/decompose/requirements.lock'
expected=hashlib.sha256(lock.read_bytes()).hexdigest()
version=(ROOT/'VERSION').read_text().strip()
runtime=ROOT/'.taskspec/runtime/decompose'
try:
    if len(sys.argv)>1: raise ValueError('Usage: taskspec setup decompose')
    if sys.version_info<(3,11): raise ValueError('Python >= 3.11 is required for native decomposition')
    if runtime.is_symlink() or any(p.is_symlink() for p in (runtime.parent,runtime.parent.parent)): raise ValueError('private runtime path cannot traverse symlinks')
    if os.environ.get('TASKSPEC_DRY_RUN')=='1':
        print(json.dumps({'contract':'TaskRuntimeSetup/v1','dry_run':True,'path':str(runtime),'lock_digest':expected}));raise SystemExit(0)
    receipt=runtime/'taskspec-runtime.json'
    if receipt.is_file() and json.loads(receipt.read_text())=={'contract':'TaskRuntime/v1','version':version,'lock_digest':expected}:
        subprocess.run([str(runtime/'bin/python'),'-c','import yaml,jsonschema; from jsonschema import Draft202012Validator'],check=True)
    else:
        runtime.parent.mkdir(parents=True,exist_ok=True)
        temporary=Path(tempfile.mkdtemp(prefix='.decompose-',dir=runtime.parent))
        try:
            subprocess.run([sys.executable,'-m','venv',str(temporary)],check=True)
            subprocess.run([str(temporary/'bin/python'),'-m','pip','install','--disable-pip-version-check','--require-hashes','-r',str(lock)],check=True,stdout=sys.stderr)
            subprocess.run([str(temporary/'bin/python'),'-c','import yaml,jsonschema; from jsonschema import Draft202012Validator'],check=True)
            (temporary/'taskspec-runtime.json').write_text(json.dumps({'contract':'TaskRuntime/v1','version':version,'lock_digest':expected})+'\n')
            previous=runtime.with_name('.decompose-previous')
            if previous.exists(): raise ValueError('interrupted runtime replacement: inspect .decompose-previous before retrying')
            if runtime.exists(): runtime.rename(previous)
            try: temporary.rename(runtime)
            except BaseException:
                if previous.exists():previous.rename(runtime)
                raise
            if previous.exists():shutil.rmtree(previous)
        finally:
            if temporary.exists():shutil.rmtree(temporary)
    print(json.dumps({'contract':'TaskRuntimeSetup/v1','ready':True,'path':str(runtime),'lock_digest':expected}))
except (OSError,ValueError,subprocess.CalledProcessError) as error:
    print('DECOMPOSE_SETUP=FAILED '+str(error),file=sys.stderr);raise SystemExit(3)
