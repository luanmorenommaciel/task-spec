#!/usr/bin/env bash
# test-repo-organization-e2e.sh — walk the organized repository as a user would.
#
# test-repo-layout.sh is the directory-shape contract. This script is the
# working-state walkthrough: empty live backlog, parked composition nodes,
# receipt pairing, doctor, isolated demo, and a clean graph. It runs against
# THIS checkout, then against the disposable demo repo.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
FAILURES=0
CHECKS=0

fail() { echo "  FAIL: $*" >&2; FAILURES=$((FAILURES + 1)); }
ok()   { echo "  ok   $*"; }
check() { CHECKS=$((CHECKS + 1)); }

frontmatter_field() {
  # Print the first `key:` value from a Task-Spec frontmatter block.
  awk -v key="$2" '
    NR == 1 && $0 != "---" { exit }
    NR > 1 && $0 == "---" { exit }
    $0 ~ ("^" key ":") {
      sub("^" key ":[[:space:]]*", "")
      print
      exit
    }
  ' "$1"
}

echo "test-repo-organization-e2e.sh"
echo "════════════════════════════════════════"

# ---------------------------------------------------------------------------
# 1. Live backlog matches what tasks/README.md claims
# ---------------------------------------------------------------------------
check
LIVE="$(find tasks -maxdepth 1 -name 'T-*.md' -type f | sort)"
if grep -q 'Live engine chores still open in \*this\* repo (none right now)' tasks/README.md; then
  if [[ -z "$LIVE" ]]; then
    ok "live backlog is empty, matching tasks/README.md"
  else
    fail "tasks/README.md says no live chores, but found:"
    printf '    %s\n' $LIVE >&2
  fi
else
  if [[ -n "$LIVE" ]]; then
    ok "live backlog has $(printf '%s\n' $LIVE | wc -l | tr -d ' ') open T-*.md file(s)"
  else
    fail "tasks/README.md no longer claims an empty live backlog, but tasks/ has no T-*.md"
  fi
fi

# ---------------------------------------------------------------------------
# 2. Parked nodes are non-executable composition units
# ---------------------------------------------------------------------------
check
PARKED="$(find tasks/parked -maxdepth 1 -name 'T-*.md' -type f | sort)"
if [[ -z "$PARKED" ]]; then
  fail "tasks/parked/ has no T-*.md files"
else
  PARKED_BAD=""
  for spec in $PARKED; do
    status="$(frontmatter_field "$spec" status)"
    backend="$(frontmatter_field "$spec" execution_backend)"
    effort="$(frontmatter_field "$spec" effort)"
    if [[ "$status" != "parked" || "$backend" != "none" ]]; then
      PARKED_BAD="$PARKED_BAD $spec(status=$status backend=$backend)"
    fi
    case "$effort" in
      XL|XXL) ;;
      *) PARKED_BAD="$PARKED_BAD $spec(effort=$effort not a composition node)" ;;
    esac
  done
  if [[ -z "$PARKED_BAD" ]]; then
    ok "every parked spec is a non-executable composition node ($(printf '%s\n' $PARKED | wc -l | tr -d ' '))"
  else
    fail "parked spec is executable or not a node:$PARKED_BAD"
  fi
fi

# ---------------------------------------------------------------------------
# 3. Every accepted done leaf has a matching AcceptanceRecord
# ---------------------------------------------------------------------------
check
MISSING_RECEIPT=""
DONE_ACCEPTED=0
for spec in tasks/done/T-*.md; do
  [[ -f "$spec" ]] || continue
  accepted="$(frontmatter_field "$spec" accepted)"
  [[ "$accepted" == "true" ]] || continue
  DONE_ACCEPTED=$((DONE_ACCEPTED + 1))
  id="$(basename "$spec" .md)"
  if ! find ".taskspec/acceptance/$id" -name '*.json' 2>/dev/null | grep -q .; then
    MISSING_RECEIPT="$MISSING_RECEIPT $id"
  fi
done
if [[ -z "$MISSING_RECEIPT" && "$DONE_ACCEPTED" -gt 0 ]]; then
  ok "every accepted done leaf has an AcceptanceRecord ($DONE_ACCEPTED)"
else
  fail "accepted done leaf missing .taskspec/acceptance/<id>/*.json:$MISSING_RECEIPT"
fi

# ---------------------------------------------------------------------------
# 4. The TaskPlan manifests that produced this backlog still exist
# ---------------------------------------------------------------------------
check
if [[ -f tasks/.plans/task-spec-3.8.1.yaml && -f tasks/.plans/task-spec-3.9.0.yaml ]]; then
  ok "tasks/.plans/ still has the 3.8.1 and 3.9.0 TaskPlan manifests"
else
  fail "tasks/.plans/ is missing a shipped TaskPlan manifest"
fi

# ---------------------------------------------------------------------------
# 5. Orientation surfaces name the contract and the dests
# ---------------------------------------------------------------------------
check
ORIENT=""
grep -q 'triple-lock' spec/README.md || ORIENT="$ORIENT spec/README.md:triple-lock"
grep -q 'spec/README.md' docs/index.md || ORIENT="$ORIENT docs/index.md:spec/README"
grep -q '.cursor/skills/task-spec' README.md || ORIENT="$ORIENT README.md:cursor-dest"
if grep -qE '\]\(assets/readme/' README.md; then
  ORIENT="$ORIENT README.md:stale-assets/readme-image"
fi
if [[ -z "$ORIENT" ]]; then
  ok "spec README, docs/index, and root README agree on orientation"
else
  fail "orientation surface drifted:$ORIENT"
fi

# ---------------------------------------------------------------------------
# 6. Doctor on this checkout
# ---------------------------------------------------------------------------
check
DOCTOR_OUT="$(bash bin/taskspec doctor 2>&1)" || true
if grep -q '^DOCTOR=READY$' <<<"$DOCTOR_OUT"; then
  ok "taskspec doctor → DOCTOR=READY"
else
  fail "taskspec doctor did not print DOCTOR=READY"
  printf '%s\n' "$DOCTOR_OUT" | sed 's/^/    /' >&2
fi

# ---------------------------------------------------------------------------
# 7. Isolated demo — the public prove-it path
# ---------------------------------------------------------------------------
check
DEMO_OUT="$(bash bin/taskspec demo 2>&1)" || true
DEMO_MISSING=""
for token in 'PLAN=VALID' 'DOD=COMPLETE' 'VERDICT=DELEGATE TIER=1' \
             'HANDOFF=TaskHandoff/v3' 'EVAL=PASS' 'ACCEPTED=1' 'DEMO=READY'; do
  grep -q "$token" <<<"$DEMO_OUT" || DEMO_MISSING="$DEMO_MISSING $token"
done
if [[ -z "$DEMO_MISSING" ]]; then
  ok "taskspec demo walks plan → seal → handoff → accept"
else
  fail "taskspec demo missing tokens:$DEMO_MISSING"
  printf '%s\n' "$DEMO_OUT" | sed 's/^/    /' >&2
fi

# ---------------------------------------------------------------------------
# 8. Graph is clean and the frontier is empty
# ---------------------------------------------------------------------------
check
GRAPH_OUT="$(bash bin/taskspec graph --check 2>&1)" || true
READY_OUT="$(bash bin/taskspec ready --all 2>&1)" || true
GRAPH_BAD=""
grep -q 'issues=0' <<<"$GRAPH_OUT" || GRAPH_BAD="$GRAPH_BAD issues"
grep -q 'ready=0' <<<"$GRAPH_OUT" || GRAPH_BAD="$GRAPH_BAD ready"
# ready --all prints a header even when empty; a live id would be T-YYYYMMDD-…
if grep -qE '^T-[0-9]{8}-' <<<"$READY_OUT"; then
  GRAPH_BAD="$GRAPH_BAD ready-table"
fi
if [[ -z "$GRAPH_BAD" ]]; then
  ok "graph --check is clean and ready --all is empty"
else
  fail "graph/ready is not a closed backlog:$GRAPH_BAD"
  printf '%s\n' "$GRAPH_OUT" "$READY_OUT" | sed 's/^/    /' >&2
fi

# ---------------------------------------------------------------------------
# 9. Parked composition nodes still validate (warnings are allowed)
# ---------------------------------------------------------------------------
check
VALIDATE_BAD=""
for spec in $PARKED; do
  if ! bash bin/taskspec validate "$spec" >/dev/null; then
    VALIDATE_BAD="$VALIDATE_BAD $spec"
  fi
done
if [[ -z "$VALIDATE_BAD" ]]; then
  ok "every parked composition node still validates"
else
  fail "parked spec failed validate:$VALIDATE_BAD"
fi

echo "════════════════════════════════════════"
if [[ "$FAILURES" -eq 0 ]]; then
  echo "REPO_ORGANIZATION=OK ($CHECKS checks)"
  exit 0
fi
echo "REPO_ORGANIZATION=FAIL ($FAILURES of $CHECKS checks failed)" >&2
exit 1
