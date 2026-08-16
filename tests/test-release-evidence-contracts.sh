#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

output="$(python3 "$ROOT/tests/schema_contracts.py")"
[[ "$output" == SCHEMAS=READY* ]] || { echo "$output" >&2; exit 1; }

python3 - "$ROOT" <<'PY'
import copy
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root / "tests"))
from schema_contracts import Invalid, validate_instance

digest = "sha256:" + "a" * 64
valid = {
    "contract": "TaskSpecQualityScorecard/v1",
    "release_version": "3.8.1",
    "rubric_digest": digest,
    "generated_at": "2026-08-15T18:00:00Z",
    "dimensions": [{
        "id": "proof", "awarded_points": 1, "max_points": 1,
        "criteria": [{
            "id": "proof.local", "points": 1, "awarded": 1, "state": "pass",
            "evidence": [{"path": "release/local.json", "digest": digest, "class": "local", "state": "pass"}],
            "reason": "fixture",
        }],
    }],
    "total": {"awarded": 1, "maximum": 100, "target": 97, "passed": False},
}
validate_instance(valid, "task-spec-quality-scorecard.schema.json")
for mutation in ("missing_digest", "absolute_path", "unknown_contract"):
    candidate = copy.deepcopy(valid)
    if mutation == "missing_digest":
        del candidate["dimensions"][0]["criteria"][0]["evidence"][0]["digest"]
    elif mutation == "absolute_path":
        candidate["dimensions"][0]["criteria"][0]["evidence"][0]["path"] = "/tmp/fake.json"
    else:
        candidate["contract"] = "TaskSpecQualityScorecard/v0"
    try:
        validate_instance(candidate, "task-spec-quality-scorecard.schema.json")
    except Invalid:
        continue
    raise SystemExit(f"schema accepted forbidden mutation: {mutation}")
PY

echo "RELEASE_EVIDENCE_CONTRACTS=READY"
