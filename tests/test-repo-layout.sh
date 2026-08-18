#!/usr/bin/env bash
# test-repo-layout.sh — the repository structure is a contract, so it gets evals.
#
# This repo consolidated 25 top-level directories down to 16 and then drifted
# back up when a new top-level directory and two new root files arrived without
# anyone deciding they belonged. Layout regressions are silent: nothing fails,
# the tree just gets worse. So the shape is declared here and asserted.
#
# Adding a top-level directory or a root file is allowed. It requires editing
# the manifest below AND the layout table in AGENTS.md in the same change.
# That friction is the point.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
FAILURES=0
CHECKS=0

fail() { echo "  FAIL: $*" >&2; FAILURES=$((FAILURES + 1)); }
ok()   { echo "  ok   $*"; }
check() { CHECKS=$((CHECKS + 1)); }

# ---------------------------------------------------------------------------
# The declared shape
# ---------------------------------------------------------------------------

# Every tracked top-level directory. Keep sorted.
DECLARED_DIRS="
.claude-plugin
.github
.taskspec
assets
bin
docs
harness
interop
mesh
release
skills
spec
src
tasks
tests
tools
"

# Every tracked root-level file. Keep sorted. Root-file creep is the axis that
# regressed once already, so this list is exact, not a prefix match.
DECLARED_ROOT_FILES="
.gitignore
AGENTS.md
CHANGELOG.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
Makefile
OPERATING.md
README.md
SECURITY.md
SKILL.md
VERSION
go.mod
go.sum
install.sh
package.json
"

# Single-file top-level directories are normally a smell. These two are not:
#   bin/     — one deliberate CLI entry point
#   interop/ — UPSTREAM.lock, digest-pinned by 3.8.1 evidence; moving it makes
#              retained release evidence unverifiable
ALLOWED_THIN_DIRS="bin interop"

# Paths retired by the consolidation. If one comes back as a top-level entry,
# a refactor was reverted by accident.
RETIRED_TOP_LEVEL="adapters integrations configs templates evals fixtures cmd internal evidence brand research"

# Nested paths retired after 3.9.0. If one comes back, a flatten was reverted.
RETIRED_NESTED="assets/readme src/mesh"

# docs/runbooks/ is closed as a growth axis (AGENTS.md, docs/index.md). New
# how-tos belong in docs/guides/. Raise this only when closing the axis is
# explicitly reversed in both docs.
RUNBOOK_CEILING=12

echo "test-repo-layout.sh"
echo "════════════════════════════════════════"

# ---------------------------------------------------------------------------
# 1. Top-level directories match the manifest exactly
# ---------------------------------------------------------------------------
check
# Derived from the index, not HEAD, so a staged-but-uncommitted new
# directory is caught before the commit lands rather than after.
ACTUAL_DIRS="$(git ls-files | grep / | cut -d/ -f1 | sort -u)"
EXPECTED_DIRS="$(printf '%s\n' $DECLARED_DIRS | sort)"
if [[ "$ACTUAL_DIRS" == "$EXPECTED_DIRS" ]]; then
  ok "top-level directories match the manifest ($(printf '%s\n' $DECLARED_DIRS | wc -l | tr -d ' ') declared)"
else
  fail "top-level directories drifted from the manifest"
  comm -13 <(printf '%s\n' "$EXPECTED_DIRS") <(printf '%s\n' "$ACTUAL_DIRS") \
    | sed 's/^/    undeclared: /' >&2
  comm -23 <(printf '%s\n' "$EXPECTED_DIRS") <(printf '%s\n' "$ACTUAL_DIRS") \
    | sed 's/^/    missing:    /' >&2
  echo "    update DECLARED_DIRS here and the layout table in AGENTS.md" >&2
fi

# ---------------------------------------------------------------------------
# 2. Root files match the manifest exactly
# ---------------------------------------------------------------------------
check
ACTUAL_ROOT="$(git ls-files | grep -v / | sort)"
EXPECTED_ROOT="$(printf '%s\n' $DECLARED_ROOT_FILES | sort)"
if [[ "$ACTUAL_ROOT" == "$EXPECTED_ROOT" ]]; then
  ok "root files match the manifest ($(printf '%s\n' $DECLARED_ROOT_FILES | wc -l | tr -d ' ') declared)"
else
  fail "root files drifted from the manifest"
  comm -13 <(printf '%s\n' "$EXPECTED_ROOT") <(printf '%s\n' "$ACTUAL_ROOT") \
    | sed 's/^/    undeclared: /' >&2
  comm -23 <(printf '%s\n' "$EXPECTED_ROOT") <(printf '%s\n' "$ACTUAL_ROOT") \
    | sed 's/^/    missing:    /' >&2
fi

# ---------------------------------------------------------------------------
# 3. Every declared directory is documented in the AGENTS.md layout table
# ---------------------------------------------------------------------------
check
UNDOCUMENTED=""
LAYOUT_TABLE="$(sed -n '/## Repository layout/,/^## Build/p' AGENTS.md)"
for dir in $DECLARED_DIRS; do
  case "$dir" in
    bin) grep -q '`bin/taskspec`' <<<"$LAYOUT_TABLE" || UNDOCUMENTED="$UNDOCUMENTED $dir" ;;
    *)   grep -q "\`$dir/\`" <<<"$LAYOUT_TABLE" || UNDOCUMENTED="$UNDOCUMENTED $dir" ;;
  esac
done
if [[ -z "$UNDOCUMENTED" ]]; then
  ok "every top-level directory appears in the AGENTS.md layout table"
else
  fail "not in the AGENTS.md layout table:$UNDOCUMENTED"
fi

# ---------------------------------------------------------------------------
# 4. No undeclared single-file top-level directory
# ---------------------------------------------------------------------------
check
THIN=""
for dir in $DECLARED_DIRS; do
  count="$(git ls-files "$dir" | wc -l | tr -d ' ')"
  if [[ "$count" -le 1 ]]; then
    case " $ALLOWED_THIN_DIRS " in
      *" $dir "*) : ;;
      *) THIN="$THIN $dir($count)" ;;
    esac
  fi
done
if [[ -z "$THIN" ]]; then
  ok "no undeclared single-file top-level directory"
else
  fail "single-file top-level directory:$THIN — fold it in or declare why not"
fi

# ---------------------------------------------------------------------------
# 5. Retired paths have not come back
# ---------------------------------------------------------------------------
check
RETURNED=""
for dir in $RETIRED_TOP_LEVEL; do
  [[ -e "$dir" ]] && RETURNED="$RETURNED $dir"
done
for path in $RETIRED_NESTED; do
  [[ -e "$path" ]] && RETURNED="$RETURNED $path"
done
if [[ -z "$RETURNED" ]]; then
  ok "no retired top-level or nested path reappeared"
else
  fail "retired path is back:$RETURNED"
fi

# ---------------------------------------------------------------------------
# 6. Live files do not reference retired paths
#    Frozen records (tasks/done, tasks/.plans, release/<version>/, CHANGELOG,
#    .taskspec/) describe what shipped and are excluded on purpose.
#    tools/export-converge.py is excluded too: its right-hand values are
#    converge's layout, not this repository's.
# ---------------------------------------------------------------------------
check
STALE="$(git ls-files \
  | grep -vE '^(release/[0-9]|\.taskspec/|tasks/done/|tasks/\.plans/|CHANGELOG\.md|tests/test-repo-layout\.sh|tools/export-converge\.py)' \
  | tr '\n' '\0' \
  | xargs -0 grep -lE '(^|[^a-zA-Z0-9_/-])(adapters/(engines|mesh|trackers)|integrations/(claude-code|codex|github-action|mutations|research)|src/mesh/|configs/setup-taskspec|templates/task-spec\.md\.tpl|evidence/3\.)' \
  2>/dev/null || true)"
if [[ -z "$STALE" ]]; then
  ok "no live file references a pre-consolidation path"
else
  fail "live files still reference retired paths:"
  printf '    %s\n' $STALE >&2
fi

# ---------------------------------------------------------------------------
# 7. All three SKILL.md copies are byte-identical
#    skills/README.md claims this; nothing enforced it before.
# ---------------------------------------------------------------------------
check
SKILL_COPIES="$(git ls-files | grep -E '(^|/)SKILL\.md$')"
CANONICAL_DIGEST="$(shasum -a 256 SKILL.md | cut -d' ' -f1)"
DIVERGED=""
for copy in $SKILL_COPIES; do
  [[ "$copy" == "SKILL.md" ]] && continue
  # harness/claude-code/SKILL.md is intentionally Claude-specific prose.
  [[ "$copy" == "harness/claude-code/SKILL.md" ]] && continue
  digest="$(shasum -a 256 "$copy" | cut -d' ' -f1)"
  [[ "$digest" == "$CANONICAL_DIGEST" ]] || DIVERGED="$DIVERGED $copy"
done
if [[ -z "$DIVERGED" ]]; then
  ok "every byte-for-byte SKILL.md copy matches root SKILL.md"
else
  fail "SKILL.md copy drifted from root:$DIVERGED"
  echo "    these claim to be byte-for-byte copies; regenerate or fix the claim" >&2
fi

# ---------------------------------------------------------------------------
# 8. Fixtures live under exactly one root
# ---------------------------------------------------------------------------
check
FIXTURE_ROOTS="$(git ls-files | grep -oE '^[^/]+/fixtures/' | sort -u)"
if [[ "$FIXTURE_ROOTS" == "tests/fixtures/" ]]; then
  ok "fixtures live under exactly one root (tests/fixtures/)"
else
  fail "more than one fixture root: $(echo $FIXTURE_ROOTS)"
fi

# ---------------------------------------------------------------------------
# 9. Digest-pinned evidence paths still resolve
#    A future refactor that moves a pinned path must fail here, not silently
#    make retained release evidence unverifiable.
# ---------------------------------------------------------------------------
check
MISSING_PINNED="$(python3 - <<'PY'
import json, pathlib
root = pathlib.Path(".")
missing = []
for bundle in sorted(root.glob("release/*/protocol-conformance.json")):
    data = json.loads(bundle.read_text(encoding="utf-8"))
    for item in data if isinstance(data, list) else [data]:
        for artifact in item.get("artifacts", []):
            path = artifact.get("path")
            if path and not (root / path).exists():
                missing.append(f"{bundle}: {path}")
print("\n".join(missing))
PY
)"
if [[ -z "$MISSING_PINNED" ]]; then
  ok "every digest-pinned evidence path still resolves"
else
  fail "pinned evidence path no longer exists:"
  printf '    %s\n' "$MISSING_PINNED" >&2
fi

# ---------------------------------------------------------------------------
# 10. docs/runbooks/ stays closed
# ---------------------------------------------------------------------------
check
RUNBOOKS="$(git ls-files 'docs/runbooks/*.md' | wc -l | tr -d ' ')"
if [[ "$RUNBOOKS" -le "$RUNBOOK_CEILING" ]]; then
  ok "docs/runbooks/ stays closed ($RUNBOOKS of $RUNBOOK_CEILING; new how-tos go in docs/guides/)"
else
  fail "docs/runbooks/ grew to $RUNBOOKS (ceiling $RUNBOOK_CEILING) — new how-tos belong in docs/guides/"
fi

# ---------------------------------------------------------------------------
# 11. Every non-frozen top-level directory explains itself
# ---------------------------------------------------------------------------
check
NEEDS_README="harness release tasks skills spec tests docs"
MISSING_README=""
for dir in $NEEDS_README; do
  [[ -f "$dir/README.md" || -f "$dir/index.md" ]] || MISSING_README="$MISSING_README $dir"
done
if [[ -z "$MISSING_README" ]]; then
  ok "every grouped directory has a README or index"
else
  fail "no README.md or index.md in:$MISSING_README"
fi

echo "════════════════════════════════════════"
if [[ "$FAILURES" -eq 0 ]]; then
  echo "REPO_LAYOUT=OK ($CHECKS checks)"
  exit 0
fi
echo "REPO_LAYOUT=DRIFT ($FAILURES of $CHECKS checks failed)" >&2
exit 1
