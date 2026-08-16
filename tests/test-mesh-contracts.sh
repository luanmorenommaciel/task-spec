#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI="$ROOT/bin/taskspec"
TMP="$(mktemp -d -t taskspec-mesh-contracts-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

python3 "$ROOT/tests/schema_contracts.py" >/dev/null
bash "$CLI" mesh help | grep -q 'TaskMesh is optional'
bash "$CLI" help mesh | grep -q 'taskspec mesh'
bash "$CLI" completion bash | grep -q 'mesh'
python3 "$ROOT/src/dispatch/agent-context.py" | python3 -c '
import json, sys
value = json.load(sys.stdin)
assert "mesh" in value["commands"]
for name in ("taskmesh_api", "taskmesh_run", "executor_capability", "dispatch_decision", "run_lease", "taskmesh_event", "taskmesh_view", "sandbox_evidence", "credential_lease"):
    assert name in value["contracts"]
'

set +e
TASKSPEC_MESH_HELPER="$TMP/missing" bash "$CLI" mesh doctor >"$TMP/missing.out" 2>"$TMP/missing.err"
missing_rc=$?
set -e
[[ "$missing_rc" -eq 3 ]]
grep -q 'MESH_NOT_INSTALLED' "$TMP/missing.err"

set +e
TASKSPEC_MESH_HELPER="$TMP/missing" bash "$CLI" --json mesh doctor >"$TMP/missing.json"
missing_json_rc=$?
set -e
[[ "$missing_json_rc" -eq 3 ]]
python3 - "$TMP/missing.json" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert value["contract"] == "TaskSpecCLIResult/v1"
assert value["data"]["contract"] == "TaskMeshError/v1"
assert value["data"]["code"] == "MESH_NOT_INSTALLED"
PY

bash "$CLI" --dry-run mesh run --frontier | grep -q 'TASKMESH_DRY_RUN'
bash "$CLI" --json --dry-run mesh run --frontier | python3 -c '
import json, sys
value = json.load(sys.stdin)
assert value["ok"] is True
assert value["data"]["contract"] == "TaskMeshDryRun/v1"
'

cat >"$TMP/helper" <<EOF
#!/usr/bin/env bash
if [[ "\${1:-}" == "--version-json" ]]; then
  printf '%s\n' '{"contract":"TaskMeshAPI/v1alpha1","product_version":"$(cat "$ROOT/VERSION")","api_version":"v1alpha1","capabilities":[]}'
  exit 0
fi
printf '%s\n' '{"contract":"TaskMeshForwarded/v1","arguments":"forwarded"}'
EOF
chmod +x "$TMP/helper"
TASKSPEC_MESH_HELPER="$TMP/helper" bash "$CLI" --json mesh doctor | python3 -c '
import json, sys
value = json.load(sys.stdin)
assert value["ok"] is True
assert value["data"]["contract"] == "TaskMeshForwarded/v1"
'

cat >"$TMP/mismatch" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' '{"contract":"TaskMeshAPI/v1alpha1","product_version":"0.0.0","api_version":"v1alpha1","capabilities":[]}'
EOF
chmod +x "$TMP/mismatch"
set +e
TASKSPEC_MESH_HELPER="$TMP/mismatch" bash "$CLI" --json mesh doctor >"$TMP/mismatch.json"
mismatch_rc=$?
set -e
[[ "$mismatch_rc" -eq 3 ]]
python3 - "$TMP/mismatch.json" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert value["data"]["code"] == "MESH_VERSION_MISMATCH"
PY

echo "MESH_CONTRACTS=READY"
