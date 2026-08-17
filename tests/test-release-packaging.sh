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
    "$ROOT/tools/build-release-evidence-archive.py" "$ROOT/tools/build-release-report.py" \
    "$ROOT/tools/build-mesh-release.py"
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
grep -q "^task-spec-$VERSION/mesh/cmd/taskspec-meshd/main.go$" "$WORK/archive-files.txt"
grep -q "^task-spec-$VERSION/mesh/internal/mesh/daemon.go$" "$WORK/archive-files.txt"
grep -q "^task-spec-$VERSION/harness/mesh-adapters/omp-rpc.json$" "$WORK/archive-files.txt"
grep -q "^task-spec-$VERSION/release/mesh/image.lock$" "$WORK/archive-files.txt"
if grep -qE "^task-spec-$VERSION/(release/[0-9]|evidence|tasks)/" "$WORK/archive-files.txt"; then
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
grep -q "release/$VERSION/mesh-release-evidence.json$" "$WORK/evidence-files.txt"
grep -q "release/$VERSION/mesh-conformance.json$" "$WORK/evidence-files.txt"

for retained in mesh-release-evidence.json mesh-conformance.json reviewer-report.json; do
  test -s "$ROOT/release/$VERSION/$retained"
done
python3 - "$ROOT" "$VERSION" <<'PY'
import json, pathlib, re, sys
root, version = pathlib.Path(sys.argv[1]), sys.argv[2]
release = root / "release" / version
evidence = json.loads((release / "mesh-release-evidence.json").read_text(encoding="utf-8"))
conformance = json.loads((release / "mesh-conformance.json").read_text(encoding="utf-8"))
reviewer = json.loads((release / "reviewer-report.json").read_text(encoding="utf-8"))
assert evidence["contract"] == "TaskMeshReleaseEvidence/v1" and evidence["version"] == version
assert evidence["quality_baseline"]["score"] >= 97
assert conformance["contract"] == "TaskMeshConformanceEvidence/v1"
assert all(item["state"] == "pass" for item in conformance["suites"])
assert reviewer["contract"] == "TaskMeshReviewerReport/v1" and reviewer["result"] == "pass"
for row in evidence["artifacts"]:
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", row["digest"])
PY

host_os="$(uname -s | tr '[:upper:]' '[:lower:]')"
host_arch="$(uname -m)"
case "$host_arch" in x86_64|amd64) host_arch=amd64 ;; arm64|aarch64) host_arch=arm64 ;; esac
python3 "$ROOT/tools/build-mesh-release.py" --out-dir "$WORK/one/mesh" --target "$host_os/$host_arch" >/dev/null
python3 "$ROOT/tools/build-mesh-release.py" --out-dir "$WORK/two/mesh" --target "$host_os/$host_arch" >/dev/null
cmp -s "$WORK/one/mesh/taskspec-meshd-$host_os-$host_arch" "$WORK/two/mesh/taskspec-meshd-$host_os-$host_arch"
cmp -s "$WORK/one/mesh/taskspec-meshd-$host_os-$host_arch.sha256" "$WORK/two/mesh/taskspec-meshd-$host_os-$host_arch.sha256"

python3 - "$ROOT/.github/workflows/release-install-smoke.yml" <<'PY'
import pathlib, sys
text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
assert "TASKSPEC_RELEASE_PROVENANCE_KEY_PEM" in text
assert "tools/release-provenance.py create" in text
assert "tools/release-provenance.py verify" in text
assert "actions/attest-build-provenance" not in text
assert "actions/attest-sbom" not in text
assert "build-release-evidence-archive.py" in text and "build-sbom.py" in text
assert "build-mesh-release.py" in text and "--with-mesh" in text
assert "taskmesh-binaries.provenance.dsse.json" in text
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
assert "mesh/cmd/taskspec-meshd/main.go" in files
assert "mesh/internal/mesh/daemon.go" in files
assert "release/mesh/image.lock" in files
PY
fi

echo "RELEASE_PACKAGING=READY"
