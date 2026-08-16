#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
WORK="$(mktemp -d -t taskspec-mesh-install-XXXXXX)"
DAEMON_PID=""
cleanup() {
  [[ -z "$DAEMON_PID" ]] || kill "$DAEMON_PID" >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT

host_os="$(uname -s | tr '[:upper:]' '[:lower:]')"
host_arch="$(uname -m)"
case "$host_arch" in x86_64|amd64) host_arch=amd64 ;; arm64|aarch64) host_arch=arm64 ;; esac
asset="taskspec-meshd-$host_os-$host_arch"
mkdir -p "$WORK/assets" "$WORK/core-project" "$WORK/mesh-project" "$WORK/symlink-project" "$WORK/npm-project" "$WORK/npm-bin"
python3 "$ROOT/tools/build-mesh-release.py" --out-dir "$WORK/assets" --target "$host_os/$host_arch" >/dev/null

# Core-only remains unchanged and does not install a helper.
HOME="$WORK/core-home" TASKSPEC_INSTALL_ROOT="$WORK/core-install" \
  bash "$ROOT/install.sh" --target "$WORK/core-project" --bin-dir "$WORK/core-bin" >"$WORK/core.log"
grep -q '^INSTALL=OK$' "$WORK/core.log"
[[ ! -e "$WORK/core-bin/taskspec-meshd" ]]
set +e
(cd "$WORK/core-project" && "$WORK/core-bin/taskspec" mesh doctor >"$WORK/core-mesh.out" 2>"$WORK/core-mesh.err")
core_rc=$?
set -e
[[ "$core_rc" -eq 3 ]]
grep -q 'MESH_NOT_INSTALLED' "$WORK/core-mesh.err"

# Copy mode consumes the checksummed release helper and negotiates the exact version.
HOME="$WORK/mesh-home" TASKSPEC_INSTALL_ROOT="$WORK/mesh-install" TASKSPEC_MESH_ASSET_DIR="$WORK/assets" \
  bash "$ROOT/install.sh" --target "$WORK/mesh-project" --bin-dir "$WORK/mesh-bin" --with-mesh >"$WORK/mesh.log"
grep -q '^INSTALL=OK$' "$WORK/mesh.log"
grep -q '^mesh:' "$WORK/mesh.log"
[[ -x "$WORK/mesh-install/$VERSION/libexec/taskspec-meshd" ]]
[[ -x "$WORK/mesh-bin/taskspec-meshd" ]]
"$WORK/mesh-bin/taskspec-meshd" --version-json | python3 -c \
  'import json,sys; v=json.load(sys.stdin); assert v["contract"] == "TaskMeshAPI/v1alpha1" and v["product_version"] == sys.argv[1]' "$VERSION"
git init -q -b main "$WORK/mesh-project"
git -C "$WORK/mesh-project" config user.name taskspec-test
git -C "$WORK/mesh-project" config user.email taskspec@example.invalid
touch "$WORK/mesh-project/README.md"
git -C "$WORK/mesh-project" add README.md
git -C "$WORK/mesh-project" commit -qm initial
(cd "$WORK/mesh-project" && "$WORK/mesh-bin/taskspec" --json mesh doctor) >"$WORK/mesh-doctor.json"
grep -q 'MESH_DOCTOR_READY' "$WORK/mesh-doctor.json"
DAEMON_PID="$(python3 - "$WORK/mesh-doctor.json" <<'PY'
import json, pathlib, sys
print(json.loads(pathlib.Path(sys.argv[1]).read_text())["data"]["data"]["daemon_pid"])
PY
)"

# Checkout symlink mode keeps the source tree clean and exposes the helper on PATH.
before="$(git -C "$ROOT" status --porcelain)"
HOME="$WORK/symlink-home" TASKSPEC_INSTALL_ROOT="$WORK/symlink-install" TASKSPEC_MESH_ASSET_DIR="$WORK/assets" \
  bash "$ROOT/install.sh" --target "$WORK/symlink-project" --bin-dir "$WORK/symlink-bin" --symlink --with-mesh >"$WORK/symlink.log"
after="$(git -C "$ROOT" status --porcelain)"
[[ "$before" == "$after" ]]
[[ -L "$WORK/symlink-install/$VERSION" ]]
[[ -x "$WORK/symlink-bin/taskspec-meshd" ]]

# The npm package already owns BIN_DIR/taskspec. The harness installer keeps
# that exact package link while adding skills, the pinned engine, and TaskMesh.
ln -s "$ROOT/bin/taskspec" "$WORK/npm-bin/taskspec"
HOME="$WORK/npm-home" TASKSPEC_INSTALL_ROOT="$WORK/npm-install" TASKSPEC_MESH_ASSET_DIR="$WORK/assets" \
  bash "$ROOT/install.sh" --target "$WORK/npm-project" --bin-dir "$WORK/npm-bin" --with-mesh >"$WORK/npm.log"
grep -q '^kept: package CLI ' "$WORK/npm.log"
grep -q '^INSTALL=OK$' "$WORK/npm.log"
[[ -L "$WORK/npm-bin/taskspec" ]]
[[ "$(readlink "$WORK/npm-bin/taskspec")" == "$ROOT/bin/taskspec" ]]
[[ -x "$WORK/npm-bin/taskspec-meshd" ]]

# Missing checksum, changed bytes, and a version-mismatched helper all fail closed.
mkdir -p "$WORK/bad-missing" "$WORK/bad-tamper" "$WORK/bad-version"
cp "$WORK/assets/$asset" "$WORK/bad-missing/$asset"
set +e
HOME="$WORK/bad-home-1" TASKSPEC_INSTALL_ROOT="$WORK/bad-install-1" TASKSPEC_MESH_ASSET_DIR="$WORK/bad-missing" \
  bash "$ROOT/install.sh" --target "$WORK/mesh-project" --bin-dir "$WORK/bad-bin-1" --with-mesh >"$WORK/bad-missing.log" 2>&1
missing_rc=$?
set -e
[[ "$missing_rc" -eq 1 ]]
grep -q 'missing TaskMesh checksum' "$WORK/bad-missing.log"

cp "$WORK/assets/$asset" "$WORK/bad-tamper/$asset"
cp "$WORK/assets/$asset.sha256" "$WORK/bad-tamper/$asset.sha256"
printf 'tamper' >>"$WORK/bad-tamper/$asset"
set +e
HOME="$WORK/bad-home-2" TASKSPEC_INSTALL_ROOT="$WORK/bad-install-2" TASKSPEC_MESH_ASSET_DIR="$WORK/bad-tamper" \
  bash "$ROOT/install.sh" --target "$WORK/mesh-project" --bin-dir "$WORK/bad-bin-2" --with-mesh >"$WORK/bad-tamper.log" 2>&1
tamper_rc=$?
set -e
[[ "$tamper_rc" -eq 1 ]]
grep -q 'TaskMesh checksum mismatch' "$WORK/bad-tamper.log"

cat >"$WORK/bad-version/$asset" <<'EOF'
#!/usr/bin/env sh
printf '%s\n' '{"contract":"TaskMeshAPI/v1alpha1","product_version":"0.0.0"}'
EOF
chmod +x "$WORK/bad-version/$asset"
sha="$(shasum -a 256 "$WORK/bad-version/$asset" | awk '{print $1}')"
printf '%s  %s\n' "$sha" "$asset" >"$WORK/bad-version/$asset.sha256"
set +e
HOME="$WORK/bad-home-3" TASKSPEC_INSTALL_ROOT="$WORK/bad-install-3" TASKSPEC_MESH_ASSET_DIR="$WORK/bad-version" \
  bash "$ROOT/install.sh" --target "$WORK/mesh-project" --bin-dir "$WORK/bad-bin-3" --with-mesh >"$WORK/bad-version.log" 2>&1
version_rc=$?
set -e
[[ "$version_rc" -eq 1 ]]
grep -q 'TaskMesh helper failed its version check' "$WORK/bad-version.log"

echo "INSTALL=OK"
echo "MESH_INSTALL=READY"
