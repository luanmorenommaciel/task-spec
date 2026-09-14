#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d -t 'toolkit-install-XXXXXX')"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/project with spaces"
TASKSPEC_INSTALL_ROOT="$TMP/engines" bash "$ROOT/install.sh" --toolkit --target "$TMP/project with spaces" --bin-dir "$TMP/bin with spaces" > "$TMP/install.log" 2>&1 || { cat "$TMP/install.log"; exit 1; }
"$TMP/bin with spaces/taskspec" --json guide decomposition > "$TMP/guide.json"
version="$(cat "$ROOT/VERSION")"
TASKSPEC_TEST_CLI="$TMP/bin with spaces/taskspec" \
TASKSPEC_DECOMPOSE_PYTHON="$TMP/engines/$version/.taskspec/runtime/decompose/bin/python" \
  bash "$ROOT/tests/test-toolkit-decompose.sh"
python3 - "$ROOT" "$TMP" <<'PY'
from pathlib import Path
import json,shutil,subprocess,sys
root,temp=map(Path,sys.argv[1:]);version=(root/'VERSION').read_text().strip();engine=temp/'engines'/version
assert json.loads((temp/'guide.json').read_text())['data']['version']==version
runtime=engine/'.taskspec/runtime/decompose/bin/python';assert runtime.is_file()
subprocess.run([str(runtime),'-c','import yaml,jsonschema'],check=True)
# A matching dependency lock alone cannot certify a prior engine's runtime.
receipt=engine/'.taskspec/runtime/decompose/taskspec-runtime.json'
identity=json.loads(receipt.read_text());identity['version']='0.0.0-old';receipt.write_text(json.dumps(identity)+'\n')
subprocess.run(['bash',str(engine/'bin/taskspec'),'setup','decompose'],check=True,capture_output=True)
assert json.loads(receipt.read_text())['version']==version
verify=[sys.executable,str(root/'tools/verify-toolkit.py'),'--engine',str(engine),'--source',str(root)]
for relative in ('spec/conformance/results.json','spec/conformance/_state.yaml','spec/conformance/_workdir'):
 assert not (engine/relative).exists(),relative+' was shipped as a resource'
# Running conformance after installation must not look like runtime code drift.
(engine/'spec/conformance/results.json').write_text('{"generated":true}')
(engine/'spec/conformance/_state.yaml').write_text('generated: true')
(engine/'spec/conformance/_workdir').mkdir()
(engine/'spec/conformance/_workdir/runtime.json').write_text('{}')
assert subprocess.run(verify,capture_output=True).returncode==0
# Prepare a fresh chat without invoking a provider. Its bare CLI must resolve
# to this installation, and native guide reads must stay inside the workspace.
prepared=subprocess.run([str(runtime),str(root/'tests/evals/toolkit/chat_run.py'),
 '--case','plan','--harness','claude','--engine',str(engine),
 '--installed-skill',str(temp/'project with spaces/.agents/skills/task-spec'),
 '--out',str(temp/'chat-fixture'),'--prepare-only'],text=True,capture_output=True,check=True)
observed=json.loads(prepared.stdout);assert observed['prepared'] is True
work=Path(observed['workspace']);assert work.name.startswith('taskspec chat ')
fixture=json.loads((Path(observed['retained'])/'fixture.json').read_text())
assert Path(fixture['path_cli']).resolve()==(engine/'bin/taskspec').resolve()
plugin=Path(fixture['native_plugin']);assert plugin.is_relative_to(work)
assert (plugin/'.claude-plugin/plugin.json').read_bytes()==(engine/'.claude-plugin/plugin.json').read_bytes()
for guide in (engine/'docs/guides/toolkit').glob('*.md'):
 assert (plugin/'docs/guides/toolkit'/guide.name).read_bytes()==guide.read_bytes()
shutil.rmtree(work)
# Native Claude skill entries name directories, not markdown files. Verify this
# even without a source checkout available to compare installed bytes against.
manifest=engine/'.claude-plugin/plugin.json';original_manifest=manifest.read_bytes()
bad=json.loads(original_manifest);bad['skills']=['./SKILL.md'];manifest.write_text(json.dumps(bad))
installed_verify=[sys.executable,str(root/'tools/verify-toolkit.py'),'--engine',str(engine)]
result=subprocess.run(installed_verify,capture_output=True)
assert result.returncode!=0 and b'plugin skill directory' in result.stderr
manifest.write_bytes(original_manifest)
bad=json.loads(original_manifest);bad['version']='0.0.0-old';manifest.write_text(json.dumps(bad))
assert subprocess.run(installed_verify,capture_output=True).returncode!=0
manifest.write_bytes(original_manifest)
bad=json.loads(original_manifest);bad['description']='unexpected installed change';manifest.write_text(json.dumps(bad))
assert subprocess.run(verify,capture_output=True).returncode!=0
manifest.write_bytes(original_manifest)
code=engine/'src/recipe/recipes.py';original=code.read_bytes();code.write_bytes(original+b'\n# modified after install\n')
assert subprocess.run(verify,capture_output=True).returncode!=0
code.write_bytes(original)
extra=engine/'src/recipe/unexpected.py';extra.write_text('unregistered runtime input')
assert subprocess.run(verify,capture_output=True).returncode!=0
extra.unlink()
source=temp/'project with spaces/.agents/skills/task-spec/docs/guides/toolkit/decomposition.md';source.write_text('corrupted installation')
result=subprocess.run([sys.executable,str(root/'tools/verify-toolkit.py'),'--engine',str(engine),'--source',str(root),'--target',str(temp/'project with spaces'),'--runtime'],capture_output=True)
assert result.returncode!=0
print('TOOLKIT_INSTALL=PASS clean private runtime, path spaces, version identity, and corrupted-resource refusal')
PY
