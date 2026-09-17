#!/usr/bin/env bash
# Prove the hosted TaskMesh isolation job cannot be silently parked again.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CI="$ROOT/.github/workflows/ci.yml"
ISO="$ROOT/tests/test-mesh-isolation.sh"
FAILURES=0

fail() { echo "  FAIL: $*" >&2; FAILURES=$((FAILURES + 1)); }
ok() { echo "  ok   $*"; }

[[ -f "$CI" ]] || { echo "missing $CI" >&2; exit 1; }
[[ -f "$ISO" ]] || { echo "missing $ISO" >&2; exit 1; }

if grep -q 'mesh-isolation:' "$CI"; then
  ok "ci.yml declares mesh-isolation"
else
  fail "ci.yml missing mesh-isolation job"
fi

if awk '
  $0 ~ /^  mesh-isolation:/ { in_job=1; next }
  in_job && $0 ~ /^  [A-Za-z0-9_-]+:/ { exit }
  in_job && $0 ~ /if:[[:space:]]*github\.event_name == .workflow_dispatch./ { found=1 }
  END { exit found ? 0 : 1 }
' "$CI"; then
  fail "mesh-isolation is parked on workflow_dispatch"
else
  ok "mesh-isolation is not dispatch-only"
fi

if awk '
  $0 ~ /^  mesh-isolation:/ { in_job=1; next }
  in_job && $0 ~ /^  [A-Za-z0-9_-]+:/ { exit }
  in_job && $0 ~ /TASKSPEC_REQUIRE_MESH_ISOLATION:[[:space:]]*.1./ { found=1 }
  END { exit found ? 0 : 1 }
' "$CI"; then
  ok "mesh-isolation requires TASKSPEC_REQUIRE_MESH_ISOLATION=1"
else
  fail "mesh-isolation missing TASKSPEC_REQUIRE_MESH_ISOLATION=1"
fi

BIN="$(mktemp -d)"
cat >"$BIN/docker" <<'DOCK'
#!/bin/sh
exit 1
DOCK
chmod +x "$BIN/docker"

set +e
out="$(PATH="$BIN:$PATH" TASKSPEC_REQUIRE_MESH_ISOLATION=1 bash "$ISO" 2>&1)"
rc=$?
set -e
if [[ "$rc" -eq 1 ]] && grep -q 'MESH_ISOLATION=UNAVAILABLE reason=docker' <<<"$out"; then
  ok "REQUIRE=1 fails closed without Docker"
else
  fail "REQUIRE=1 did not fail closed (rc=$rc)"
  printf '%s\n' "$out" >&2
fi

set +e
out="$(PATH="$BIN:$PATH" TASKSPEC_REQUIRE_MESH_ISOLATION=0 bash "$ISO" 2>&1)"
rc=$?
set -e
if [[ "$rc" -eq 0 ]] && grep -q 'MESH_ISOLATION=UNAVAILABLE reason=docker' <<<"$out"; then
  ok "local default still reports UNAVAILABLE when Docker is missing"
else
  fail "local default skip changed (rc=$rc)"
  printf '%s\n' "$out" >&2
fi

rm -rf "$BIN"
if [[ "$FAILURES" -ne 0 ]]; then
  echo "MESH_ISOLATION_HOSTED=FAIL count=$FAILURES" >&2
  exit 1
fi
echo "MESH_ISOLATION_HOSTED=READY"
