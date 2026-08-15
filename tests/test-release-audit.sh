#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/taskspec-release-audit.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

mkdir -p "$TMP_ROOT/release/3.8.1" "$TMP_ROOT/proof"
cp "$ROOT/release/quality-rubric.json" "$TMP_ROOT/release/quality-rubric.json"
printf '%s\n' 'retained synthetic proof' > "$TMP_ROOT/proof/release.json"
PROOF_DIGEST="sha256:$(shasum -a 256 "$TMP_ROOT/proof/release.json" | awk '{print $1}')"

python3 - "$TMP_ROOT" "$PROOF_DIGEST" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
digest = sys.argv[2]
rubric = json.loads((root / "release/quality-rubric.json").read_text(encoding="utf-8"))
unclaimed = {"semantic_truth", "ecosystem_certification", "production_reliability"}
gates = {}
for dimension in rubric["dimensions"]:
    for criterion in dimension["criteria"]:
        identifier = criterion["id"]
        if identifier in unclaimed:
            gates[identifier] = {
                "state": "unavailable",
                "evidence": None,
                "reason": "Intentionally unclaimed by the fixed rubric.",
            }
        else:
            gates[identifier] = {
                "state": "pass",
                "evidence": {"path": "proof/release.json", "digest": digest},
                "reason": "Synthetic retained fixture.",
            }
evidence = {
    "contract": "TaskSpecReleaseEvidence/v2",
    "version": "3.8.1",
    "format_version": 4,
    "compatible_format_versions": [1, 2, 3, 4],
    "generated_at": "2026-08-15T18:30:00Z",
    "source": {"commit": "a" * 40, "branch": "fixture"},
    "release_status": "rc",
    "quality_scorecard": {"path": "release/3.8.1/scorecard.json", "digest": "sha256:" + "0" * 64},
    "gates": gates,
    "artifacts": [{"path": "proof/release.json", "digest": digest}],
}
(root / "release/evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
PY

AUDIT="python3 $ROOT/src/evidence/release_audit.py"
$AUDIT generate --root "$TMP_ROOT" --update-evidence >/dev/null
$AUDIT check --root "$TMP_ROOT" | grep -q 'QUALITY_SCORE=97 SCORECARD=VALID'
READY_OUTPUT="$($AUDIT audit --root "$TMP_ROOT")"
grep -q '^PROTOCOLS=READY$' <<<"$READY_OUTPUT"
grep -q '^ENGINE_MATRIX=READY$' <<<"$READY_OUTPUT"
grep -q '^SANDBOX_ATTESTATION=VERIFIED$' <<<"$READY_OUTPUT"
grep -q '^QUALITY_SCORE=97$' <<<"$READY_OUTPUT"
grep -q '^RELEASE_AUDIT=READY$' <<<"$READY_OUTPUT"

# A hand-edited total cannot replace the derived result.
python3 - "$TMP_ROOT/release/3.8.1/scorecard.json" <<'PY'
import json
import pathlib
import sys
path = pathlib.Path(sys.argv[1])
value = json.loads(path.read_text(encoding="utf-8"))
value["total"]["awarded"] = 100
path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
PY
if $AUDIT check --root "$TMP_ROOT" >/dev/null 2>&1; then
  echo "manual scorecard total was trusted" >&2
  exit 1
fi
$AUDIT generate --root "$TMP_ROOT" --update-evidence >/dev/null

# A changed retained artifact invalidates every criterion that cites it.
printf '%s\n' 'tampered proof' > "$TMP_ROOT/proof/release.json"
if $AUDIT audit --root "$TMP_ROOT" >/dev/null 2>&1; then
  echo "tampered evidence passed the release audit" >&2
  exit 1
fi
printf '%s\n' 'retained synthetic proof' > "$TMP_ROOT/proof/release.json"

# Pending evidence earns zero even if an artifact is present.
python3 - "$TMP_ROOT/release/evidence.json" <<'PY'
import json
import pathlib
import sys
path = pathlib.Path(sys.argv[1])
value = json.loads(path.read_text(encoding="utf-8"))
value["gates"]["a2a_official"]["state"] = "pending"
value["gates"]["a2a_official"]["reason"] = "Fixture pending."
path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
PY
$AUDIT generate --root "$TMP_ROOT" --update-evidence >/dev/null
PENDING_OUTPUT="$($AUDIT audit --root "$TMP_ROOT" 2>&1 || true)"
grep -q '^PROTOCOLS=BLOCKED$' <<<"$PENDING_OUTPUT"
grep -q '^QUALITY_SCORE=93$' <<<"$PENDING_OUTPUT"
grep -q '^RELEASE_AUDIT=BLOCKED$' <<<"$PENDING_OUTPUT"

# The repository working score is honest and its README projection is exact.
PRODUCTION_OUTPUT="$($AUDIT audit --root "$ROOT" 2>&1 || true)"
EXPECTED_SCORE="$(python3 - "$ROOT/release/3.8.1/scorecard.json" <<'PY'
import json
import pathlib
import sys
print(json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))["total"]["awarded"])
PY
)"
grep -q "^QUALITY_SCORE=${EXPECTED_SCORE}$" <<<"$PRODUCTION_OUTPUT"
if [[ "$EXPECTED_SCORE" -ge 97 ]]; then
  grep -q '^RELEASE_AUDIT=READY$' <<<"$PRODUCTION_OUTPUT"
else
  grep -q '^RELEASE_AUDIT=BLOCKED$' <<<"$PRODUCTION_OUTPUT"
fi
python3 "$ROOT/tools/render-status.py" --check "$ROOT/README.md" >/dev/null
python3 "$ROOT/tests/schema_contracts.py" | grep -q '^SCHEMAS=READY'
python3 - "$ROOT" <<'PY'
import json
import pathlib
import sys
root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root / "tests"))
from schema_contracts import validate_instance
for path, schema in (
    ("release/quality-rubric.json", "quality-rubric.schema.json"),
    ("release/evidence.json", "task-spec-release-evidence.schema.json"),
    ("release/3.8.1/scorecard.json", "task-spec-quality-scorecard.schema.json"),
):
    validate_instance(json.loads((root / path).read_text(encoding="utf-8")), schema)
PY

echo "RELEASE_AUDIT_TESTS=READY"
