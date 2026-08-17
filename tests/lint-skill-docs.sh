#!/usr/bin/env bash
# lint-skill-docs.sh — Version-consistency lint for the task-spec engine repo.
#
# The single human-facing version source is ./VERSION at the repo root. This
# lint asserts it agrees with:
#   1. the latest CHANGELOG.md heading (## [x.y.z])
#   2. the runtime version string (src/lib/_lib.sh TASKSPEC_VERSION)
# A drift between any pair means a release was cut without updating one of the
# three surfaces.
#
# Usage:
#   bash tests/lint-skill-docs.sh
#   bash tests/lint-skill-docs.sh --version
#
# Exit codes:
#   0   all checks pass
#   1   one or more checks failed
#   2   usage error

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${1:-}" == "--version" ]]; then
  cat "$REPO_ROOT/VERSION" 2>/dev/null | sed 's/^/task-spec v/' && exit 0
fi

ERRORS=()
CHECKS=0
err() { ERRORS+=("$1"); }

# ---------------------------------------------------------------------------
# Check 1: VERSION file exists and holds a bare semver string
# ---------------------------------------------------------------------------
CHECKS=$((CHECKS + 1))
VERSION=""
if [[ ! -f "$REPO_ROOT/VERSION" ]]; then
  err "VERSION file missing at repo root"
else
  VERSION="$(tr -d '[:space:]' < "$REPO_ROOT/VERSION")"
  if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    err "VERSION is not a bare x.y.z semver string (got: '$VERSION')"
  fi
fi

# ---------------------------------------------------------------------------
# Check 2: CHANGELOG.md latest heading matches VERSION
# ---------------------------------------------------------------------------
CHECKS=$((CHECKS + 1))
CHANGELOG_VER=$(grep -m1 -E '^## \[[0-9]+\.[0-9]+\.[0-9]+\]' "$REPO_ROOT/CHANGELOG.md" 2>/dev/null \
  | sed -E 's/^## \[([0-9]+\.[0-9]+\.[0-9]+)\].*/\1/')
if [[ -z "$CHANGELOG_VER" ]]; then
  # An [Unreleased] section on top is fine — the check is about the latest
  # RELEASED heading; if none exists at all, that is the error.
  err "CHANGELOG.md has no '## [x.y.z]' release heading"
elif [[ -n "$VERSION" && "$CHANGELOG_VER" != "$VERSION" ]]; then
  err "version mismatch: VERSION says '$VERSION' but CHANGELOG.md latest release is '$CHANGELOG_VER'"
fi

# ---------------------------------------------------------------------------
# Check 3: src/lib/_lib.sh TASKSPEC_VERSION matches VERSION
# ---------------------------------------------------------------------------
CHECKS=$((CHECKS + 1))
LIB_VER=$(grep -m1 '^TASKSPEC_VERSION=' "$REPO_ROOT/src/lib/_lib.sh" 2>/dev/null \
  | sed -E 's/^TASKSPEC_VERSION="?([^"]*)"?[[:space:]]*$/\1/')
if [[ -z "$LIB_VER" ]]; then
  err "src/lib/_lib.sh missing TASKSPEC_VERSION"
elif [[ -n "$VERSION" && "$LIB_VER" != "$VERSION" ]]; then
  err "version mismatch: VERSION says '$VERSION' but src/lib/_lib.sh says '$LIB_VER'"
fi

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
for metadata_file in \
  "$REPO_ROOT/package.json" \
  "$REPO_ROOT/.claude-plugin/plugin.json" \
  "$REPO_ROOT/.claude-plugin/marketplace.json" \
  "$REPO_ROOT/harness/claude-code/plugin.json" \
  "$REPO_ROOT/harness/claude-code/marketplace.json"; do
  CHECKS=$((CHECKS + 1))
  META_VER=$(python3 - "$metadata_file" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
version = data.get("version", "")
if not version and data.get("plugins"):
    version = data["plugins"][0].get("version", "")
print(version)
PY
  )
  if [[ "$META_VER" != "$VERSION" ]]; then
    err "version mismatch: $(basename "$metadata_file") says '$META_VER' but VERSION says '$VERSION'"
  fi
done

for skill_file in "$REPO_ROOT/SKILL.md" "$REPO_ROOT/harness/claude-code/SKILL.md"; do
  CHECKS=$((CHECKS + 1))
  SKILL_VER=$(awk '/^metadata:/{m=1; next} m && /^[[:space:]]+version:/{gsub(/["[:space:]]/, "", $2); print $2; exit}' "$skill_file")
  if [[ "$SKILL_VER" != "$VERSION" ]]; then
    err "version mismatch: $skill_file says '$SKILL_VER' but VERSION says '$VERSION'"
  fi
done

echo "lint-skill-docs.sh ($CHECKS checks)"
echo "════════════════════════════════════════"
if [[ ${#ERRORS[@]} -gt 0 ]]; then
  echo "FAIL: ${#ERRORS[@]} version-consistency error(s):"
  for e in "${ERRORS[@]}"; do echo "  - $e"; done
  exit 1
fi
echo "OK: VERSION, CHANGELOG.md, and src/lib/_lib.sh agree at v$VERSION"
exit 0
