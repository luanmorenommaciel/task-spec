#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/taskspec-protocol.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
TS="$ROOT/bin/taskspec"

python3 - "$WORK/handoff.json" <<'PY'
import json
import sys
digest = "sha256:" + "a" * 64
handoff = {
    "contract": "TaskHandoff/v3",
    "task_id": "T-20260815-protocol-fixture",
    "format_version": 3,
    "spec": "tasks/T-20260815-protocol-fixture.md",
    "spec_digest": digest,
    "task_revision_digest": "sha256:" + "b" * 64,
    "signoff_tier": 1,
    "backend": "fixture",
    "workspace": "/tmp/fixture",
    "authorization": {
        "scheme": "hmac-sha256-v3",
        "ref": "hmac-sha256-v3:12345678:" + "c" * 64,
        "tier": 1,
        "signed_by": "fixture",
        "signed_at": "2026-08-15T18:00:00Z",
    },
    "attempt": {"id": "11111111-1111-4111-8111-111111111111", "issued_at": "2026-08-15T18:01:00Z"},
    "source": {"workspace": "/tmp/fixture", "base_commit": "d" * 40},
    "dependency_closure": {"contract": "DependencyClosure/v1", "task_id": "T-20260815-protocol-fixture", "digest": "sha256:" + "e" * 64, "members": []},
    "write_scope": {"touches_paths": ["src/feature.py"], "creates_paths": ["tests/feature.py"], "do_not_touch": ["secrets/"]},
    "budgets": {"iterations": 7, "tokens": 5000, "effort": "M"},
    "agent_contract": {"version": 2, "read": ["intent"], "produce": ["code"], "required_tools": ["git"], "timeout_minutes": 10, "sandbox_type": "host", "output_artifacts": [], "mcp_dependencies": [], "emit": ["pass"], "backend_metadata": {}},
    "eval_command": ["taskspec", "run", "tasks/T-20260815-protocol-fixture.md"],
    "acceptance_command": ["taskspec", "accept", "tasks/T-20260815-protocol-fixture.md"],
    "evaluation_policy": {"mode": "portable"},
    "environment_contract": {"network": "denied"},
    "identity_policy": {"required": True},
    "receipt_requirements": ["evaluation", "environment"],
}
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(handoff, handle, indent=2)
    handle.write("\n")
PY

"$TS" bridge export "$WORK/handoff.json" --protocol a2a --out "$WORK/a2a.json"
"$TS" bridge validate "$WORK/a2a.json" >/dev/null
"$TS" bridge export "$WORK/handoff.json" --protocol mcp --out "$WORK/mcp.json"
"$TS" bridge validate "$WORK/mcp.json" >/dev/null

python3 - "$ROOT" "$WORK" <<'PY'
import json
import pathlib
import sys
root = pathlib.Path(sys.argv[1])
work = pathlib.Path(sys.argv[2])
sys.path.insert(0, str(root / "tests"))
from schema_contracts import validate_instance

a2a = json.loads((work / "a2a.json").read_text(encoding="utf-8"))
mcp = json.loads((work / "mcp.json").read_text(encoding="utf-8"))
assert a2a["contract"] == "TaskSpecA2AArtifact/v3"
assert set(a2a["parts"][0]) == {"data", "mediaType"}
assert json.loads(a2a["parts"][0]["data"])["budgets"]["iterations"] == 7
assert mcp["contract"] == "TaskSpecMCPTask/v2"
assert mcp["protocol"] == {"name": "MCP", "version": "2026-07-28", "mode": "stateless"}
for key in ("task_revision_digest", "authorization_ref", "attempt_id", "base_commit", "write_scope_digest", "budgets_digest", "evidence_requirements_digest"):
    assert a2a["metadata"][key] == mcp["metadata"][key]
validate_instance(a2a, "a2a-artifact.schema.json")
validate_instance(mcp, "mcp-task.schema.json")

# Historical bridge objects remain readable on their original shapes.
legacy_a2a = json.loads(json.dumps(a2a))
legacy_a2a["contract"] = "TaskSpecA2AArtifact/v2"
legacy_a2a["parts"] = [{"kind": "data", "data": json.loads(a2a["parts"][0]["data"])}]
(work / "a2a-legacy.json").write_text(json.dumps(legacy_a2a) + "\n", encoding="utf-8")
legacy_mcp = json.loads(json.dumps(mcp))
legacy_mcp["contract"] = "TaskSpecMCPTask/v1"
legacy_mcp.pop("protocol")
(work / "mcp-legacy.json").write_text(json.dumps(legacy_mcp) + "\n", encoding="utf-8")
validate_instance(legacy_a2a, "a2a-artifact.schema.json")
validate_instance(legacy_mcp, "mcp-task.schema.json")
PY
"$TS" bridge validate "$WORK/a2a-legacy.json" >/dev/null
"$TS" bridge validate "$WORK/mcp-legacy.json" >/dev/null

MODERN_META='{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientInfo":{"name":"fixture","version":"1"},"io.modelcontextprotocol/clientCapabilities":{}}'
DISCOVER="$(printf '%s\n' "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"server/discover\",\"params\":{\"_meta\":$MODERN_META}}" | "$TS" mcp)"
python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["result"]["supportedVersions"] == ["2026-07-28"]' <<<"$DISCOVER"
MISSING_META="$(printf '%s\n' '{"jsonrpc":"2.0","id":2,"method":"server/discover","params":{}}' | "$TS" mcp)"
python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["error"]["code"] == -32602' <<<"$MISSING_META"
LEGACY="$(printf '%s\n' '{"jsonrpc":"2.0","id":3,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}' | "$TS" mcp)"
python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["result"]["protocolVersion"] == "2025-06-18" and d["result"]["serverInfo"]["name"] == "taskspec-legacy"' <<<"$LEGACY"

python3 - "$ROOT" <<'PY'
import hashlib
import json
import pathlib
import sys
root = pathlib.Path(sys.argv[1])
lock = json.loads((root / "spec/UPSTREAM.lock").read_text(encoding="utf-8"))
assert lock["lock_version"] == 1
for name, expected in (("a2a", ("1.0", "1.1.2")), ("mcp", ("2026-07-28", "2.0.0"))):
    item = lock["protocols"][name]
    assert (item["specification"]["version"], item["sdk"]["version"]) == expected
    for source in (item["specification"], item["sdk"]):
        assert len(source["commit"]) == 40
        assert source["digest"].startswith("sha256:") and len(source["digest"]) == 71

bundle = json.loads((root / "release/3.8.1/protocol-conformance.json").read_text(encoding="utf-8"))
assert isinstance(bundle, list) and {item["protocol"] for item in bundle} == {"A2A", "MCP"}
sys.path.insert(0, str(root / "tests"))
from schema_contracts import validate_instance
for item in bundle:
    validate_instance(item, "protocol-conformance-evidence.schema.json")
    assert item["result"] == "pass"
    for artifact in item["artifacts"]:
        path = (root / artifact["path"]).resolve()
        path.relative_to(root.resolve())
        observed = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        assert observed == artifact["digest"], artifact["path"]
PY

AUDIT_OUTPUT="$(python3 "$ROOT/src/evidence/release_audit.py" audit 2>&1 || true)"
grep -q '^PROTOCOLS=READY$' <<<"$AUDIT_OUTPUT"

SDK_PYTHON="${TASKSPEC_PROTOCOL_SDK_PYTHON:-}"
if [[ -z "$SDK_PYTHON" ]]; then
  if python3 -c 'import importlib.metadata as m; assert m.version("a2a-sdk") == "1.1.2" and m.version("mcp") == "2.0.0"' >/dev/null 2>&1; then
    SDK_PYTHON="$(command -v python3)"
  fi
fi

if [[ -n "$SDK_PYTHON" ]]; then
  "$SDK_PYTHON" - "$ROOT" "$WORK" <<'PY'
import anyio
import importlib.metadata
import json
import pathlib
import sys
from a2a.types import Artifact
from google.protobuf.json_format import MessageToDict, ParseDict
from mcp import Client, StdioServerParameters, stdio_client

assert importlib.metadata.version("a2a-sdk") == "1.1.2"
assert importlib.metadata.version("mcp") == "2.0.0"
root = pathlib.Path(sys.argv[1])
work = pathlib.Path(sys.argv[2])

wrapped = json.loads((work / "a2a.json").read_text(encoding="utf-8"))
official = {key: wrapped[key] for key in ("artifactId", "name", "parts", "metadata")}
round_trip = MessageToDict(ParseDict(official, Artifact()), preserving_proto_field_name=False)
round_trip = {"contract": wrapped["contract"], "protocol": wrapped["protocol"], **round_trip}
(work / "a2a-sdk-roundtrip.json").write_text(json.dumps(round_trip, indent=2) + "\n", encoding="utf-8")

async def check_mcp() -> None:
    params = StdioServerParameters(command=sys.executable, args=[str(root / "src/interop/mcp_server.py")])
    async with Client(stdio_client(params)) as client:
        assert client.protocol_version == "2026-07-28"
        listing = await client.list_tools()
        assert [tool.name for tool in listing.tools] == ["taskspec_handoff", "taskspec_validate"]
        result = await client.call_tool("taskspec_validate", {"spec": str(root / "tests/fixtures/T-20260603-stamp-then-verify.md")})
        assert result.is_error is False
        assert "valid Task-Spec" in result.content[0].text

anyio.run(check_mcp)
PY
  "$TS" bridge validate "$WORK/a2a-sdk-roundtrip.json" >/dev/null
  echo "OFFICIAL_PROTOCOL_SDK=READY"
else
  echo "OFFICIAL_PROTOCOL_SDK=UNAVAILABLE retained evidence verified"
fi

echo "PROTOCOL_CONFORMANCE=READY"
