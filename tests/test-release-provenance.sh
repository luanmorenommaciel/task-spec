#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/taskspec-release-provenance.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
TOOL="$ROOT/tools/release-provenance.py"
COMMIT="0123456789abcdef0123456789abcdef01234567"

mkdir -p "$WORK/dist"
printf '%s\n' 'private release archive' > "$WORK/dist/task-spec-3.8.1.tar.gz"
printf '%s\n' '{"spdxVersion":"SPDX-2.3"}' > "$WORK/dist/task-spec-3.8.1.spdx.json"
openssl genpkey -algorithm Ed25519 -out "$WORK/private.pem"
openssl pkey -in "$WORK/private.pem" -pubout -out "$WORK/public.pem"

python3 "$TOOL" create \
  --release-version 3.8.1 \
  --release-ref v3.8.1-rc.3 \
  --source-repository luanmorenommaciel/task-spec \
  --source-commit "$COMMIT" \
  --subject "$WORK/dist/task-spec-3.8.1.tar.gz" \
  --sbom "$WORK/dist/task-spec-3.8.1.spdx.json" \
  --builder-id https://github.com/luanmorenommaciel/task-spec/actions/workflows/release-install-smoke.yml \
  --invocation-id https://github.com/luanmorenommaciel/task-spec/actions/runs/1 \
  --started-at 2026-08-16T18:00:00Z \
  --finished-at 2026-08-16T18:01:00Z \
  --private-key "$WORK/private.pem" \
  --public-key "$WORK/public.pem" \
  --out "$WORK/provenance.dsse.json" | grep -q '^PROVENANCE=CREATED '

VERIFY=(
  python3 "$TOOL" verify
  --release-version 3.8.1
  --release-ref v3.8.1-rc.3
  --source-repository luanmorenommaciel/task-spec
  --source-commit "$COMMIT"
  --subject "$WORK/dist/task-spec-3.8.1.tar.gz"
  --sbom "$WORK/dist/task-spec-3.8.1.spdx.json"
  --envelope "$WORK/provenance.dsse.json"
  --public-key "$WORK/public.pem"
)
"${VERIFY[@]}" | grep -q '^PROVENANCE=VERIFIED '

if python3 "$TOOL" create \
  --release-version 3.8.1 --release-ref v3.8.1-rc.3 \
  --source-repository luanmorenommaciel/task-spec --source-commit "$COMMIT" \
  --subject "$WORK/dist/task-spec-3.8.1.tar.gz" --sbom "$WORK/dist/task-spec-3.8.1.spdx.json" \
  --builder-id fixture --invocation-id fixture \
  --started-at 2026-08-16T18:00:00Z --finished-at 2026-08-16T18:01:00Z \
  --private-key "$WORK/private.pem" --public-key "$WORK/public.pem" \
  --out "$WORK/provenance.dsse.json" >/dev/null 2>&1; then
  echo "provenance output was clobbered without --force" >&2
  exit 1
fi

printf '%s\n' 'tampered release archive' > "$WORK/dist/task-spec-3.8.1.tar.gz"
if "${VERIFY[@]}" >/dev/null 2>&1; then
  echo "tampered release archive retained valid provenance" >&2
  exit 1
fi
printf '%s\n' 'private release archive' > "$WORK/dist/task-spec-3.8.1.tar.gz"

python3 - "$WORK/provenance.dsse.json" <<'PY'
import base64, json, pathlib, sys
path = pathlib.Path(sys.argv[1])
value = json.loads(path.read_text())
payload = json.loads(base64.b64decode(value["payload"]))
payload["predicate"]["buildDefinition"]["externalParameters"]["releaseRef"] = "v3.8.1-forged"
value["payload"] = base64.b64encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).decode()
path.write_text(json.dumps(value, indent=2) + "\n")
PY
if "${VERIFY[@]}" >/dev/null 2>&1; then
  echo "tampered provenance payload retained a valid signature" >&2
  exit 1
fi

if rg -q 'BEGIN PRIVATE KEY' "$WORK/provenance.dsse.json" "$ROOT/release/trust/release-provenance.ed25519.pub.pem"; then
  echo "private signing key leaked into retained provenance" >&2
  exit 1
fi

python3 -m py_compile "$TOOL"
echo "PRIVATE_PROVENANCE=READY"
