#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
WORK="$(mktemp -d /tmp/taskspec-release-package.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT
EPOCH="$(git -C "$ROOT" show -s --format=%ct HEAD)"

bash "$ROOT/tests/lint-skill-docs.sh" >/dev/null

if [[ "${TASKSPEC_RELEASE_BOOTSTRAP:-0}" == "1" ]]; then
  python3 -m py_compile "$ROOT/tools/build-release-archive.py" "$ROOT/tools/build-sbom.py" \
    "$ROOT/tools/build-release-evidence-archive.py" "$ROOT/tools/build-release-report.py"
  echo "RELEASE_PACKAGING=BOOTSTRAP"
  exit 0
fi

mkdir -p "$WORK/one" "$WORK/two"
SOURCE_DATE_EPOCH="$EPOCH" python3 "$ROOT/tools/build-release-archive.py" --out-dir "$WORK/one" >/dev/null
SOURCE_DATE_EPOCH="$EPOCH" python3 "$ROOT/tools/build-release-archive.py" --out-dir "$WORK/two" >/dev/null
cmp -s "$WORK/one/task-spec-$VERSION.tar.gz" "$WORK/two/task-spec-$VERSION.tar.gz"
cmp -s "$WORK/one/task-spec-$VERSION.tar.gz.sha256" "$WORK/two/task-spec-$VERSION.tar.gz.sha256"
tar -tzf "$WORK/one/task-spec-$VERSION.tar.gz" > "$WORK/archive-files.txt"
grep -q "^task-spec-$VERSION/assets/taskspec-banner.png$" "$WORK/archive-files.txt"
grep -q "^task-spec-$VERSION/bin/taskspec$" "$WORK/archive-files.txt"
if grep -qE "^task-spec-$VERSION/(release|evidence|tasks)/" "$WORK/archive-files.txt"; then
  echo "source archive contains mutable release or backlog state" >&2
  exit 1
fi

python3 "$ROOT/tools/build-sbom.py" --archive "$WORK/one/task-spec-$VERSION.tar.gz" --epoch "$EPOCH" --out "$WORK/one/sbom.json" >/dev/null
python3 "$ROOT/tools/build-sbom.py" --archive "$WORK/two/task-spec-$VERSION.tar.gz" --epoch "$EPOCH" --out "$WORK/two/sbom.json" >/dev/null
cmp -s "$WORK/one/sbom.json" "$WORK/two/sbom.json"
python3 - "$WORK/one/sbom.json" "$VERSION" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert value["spdxVersion"] == "SPDX-2.3"
assert value["packages"][0]["versionInfo"] == sys.argv[2]
assert value["packages"][0]["filesAnalyzed"] is True
assert len(value["files"]) > 100
assert len(value["relationships"]) == len(value["files"]) + 1
PY

SOURCE_DATE_EPOCH="$EPOCH" python3 "$ROOT/tools/build-release-evidence-archive.py" --out-dir "$WORK/one" >/dev/null
SOURCE_DATE_EPOCH="$EPOCH" python3 "$ROOT/tools/build-release-evidence-archive.py" --out-dir "$WORK/two" >/dev/null
cmp -s "$WORK/one/task-spec-$VERSION-evidence.tar.gz" "$WORK/two/task-spec-$VERSION-evidence.tar.gz"
tar -tzf "$WORK/one/task-spec-$VERSION-evidence.tar.gz" > "$WORK/evidence-files.txt"
grep -q "release/evidence.json$" "$WORK/evidence-files.txt"
grep -q "release/$VERSION/environment-attestation.json$" "$WORK/evidence-files.txt"
grep -q "release/$VERSION/engine-matrix-result.json$" "$WORK/evidence-files.txt"

for retained in checksums.txt release-report.json local-gates.json install-matrix.json private-release-evidence.json sbom.spdx.json; do
  test -s "$ROOT/release/$VERSION/$retained"
done
python3 - "$ROOT" "$VERSION" <<'PY'
import hashlib, json, pathlib, re, sys
root, version = pathlib.Path(sys.argv[1]), sys.argv[2]
release = root / "release" / version
local = json.loads((release / "local-gates.json").read_text(encoding="utf-8"))
install = json.loads((release / "install-matrix.json").read_text(encoding="utf-8"))
report = json.loads((release / "release-report.json").read_text(encoding="utf-8"))
sbom = json.loads((release / "sbom.spdx.json").read_text(encoding="utf-8"))
private_release = json.loads((release / "private-release-evidence.json").read_text(encoding="utf-8"))
assert local["contract"] == "TaskSpecLocalGateEvidence/v1" and all(local["tokens"].values())
assert all(item["state"] == "pass" for item in local["suites"].values())
assert install["contract"] == "InstallationMatrixEvidence/v1"
assert all(item["state"] == "pass" for item in install["local"].values())
assert install["complete"] is True and install["repository_visibility"] == "private"
assert all(item["state"] == "pass" for item in install["remote"].values())
assert private_release["contract"] == "PrivateReleaseEvidence/v1"
assert private_release["repository"]["visibility"] == "private"
assert private_release["authentication"]["anonymous_download_required"] is False
assert private_release["provenance"]["independent_verification"] == "pass"
assert private_release["provenance"]["tamper_test"] == "pass"
assert private_release["installation"]["scope_or_secret_violations"] == 0
assert report["contract"] == "TaskSpecReleaseReport/v1" and report["version"] == version
assert sbom["spdxVersion"] == "SPDX-2.3"
for row in report["artifacts"]:
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", row["digest"])
assert report["checksums"]["digest"] == "sha256:" + hashlib.sha256((release / "checksums.txt").read_bytes()).hexdigest()
PY

python3 - "$ROOT/.github/workflows/release-install-smoke.yml" <<'PY'
import pathlib, sys
text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
assert "TASKSPEC_RELEASE_PROVENANCE_KEY_PEM" in text
assert "tools/release-provenance.py create" in text
assert "tools/release-provenance.py verify" in text
assert "actions/attest-build-provenance" not in text
assert "actions/attest-sbom" not in text
assert "build-release-evidence-archive.py" in text and "build-sbom.py" in text
assert "gh api" in text and "gh auth setup-git" in text
PY

if command -v npm >/dev/null 2>&1; then
  (cd "$ROOT" && npm pack --dry-run --json > "$WORK/npm-pack.json")
  python3 - "$WORK/npm-pack.json" <<'PY'
import json, sys
files = {row["path"] for row in json.load(open(sys.argv[1], encoding="utf-8"))[0]["files"]}
assert "assets/taskspec-banner.png" in files
assert "bin/taskspec" in files
assert "src/evidence/environment_attestation.py" in files
PY
fi

echo "RELEASE_PACKAGING=READY"
