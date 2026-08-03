#!/usr/bin/env bash
# generate-task-spec.sh — Create a new Task-Spec file (current format) from the template.
#
# Usage:
#   bash generate-task-spec.sh [--status=ready|blocked] [--queue] <slug> <effort> [agent] [source_note]
#
# Example:
#   bash generate-task-spec.sh verify-langfuse-otel S any notes/2026-05-04-observability.md
#   bash generate-task-spec.sh --status=blocked --queue fix-login-redirect S
#
# Produces: tasks/T-YYYYMMDD-<slug>.md (filled from template; stubs marked {{TODO}})
# Updates: tasks/_state.yaml
# Logs: tasks/_metrics.jsonl

set -euo pipefail

# Source shared lib (TASKSPEC_VERSION, ts_version_flag, ts_die)
_LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/_lib.sh"
# shellcheck source=../lib/_lib.sh
source "$_LIB"

# Handle --version uniformly across all task-spec scripts
ts_version_flag "$@"

STATUS="ready"
QUEUE=false
PROFILE="standard"

# Parse flags
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --status=*)
      STATUS="${1#*=}"
      shift
      ;;
    --status)
      STATUS="${2:-ready}"
      shift 2
      ;;
    --profile=*)
      PROFILE="${1#*=}"
      shift
      ;;
    --profile)
      PROFILE="${2:-standard}"
      shift 2
      ;;
    --queue)
      QUEUE=true
      shift
      ;;
    --help|-h)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    --)
      shift
      ARGS+=("$@")
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      echo "Usage: generate-task-spec.sh [--status=ready|blocked] [--queue] <slug> <effort> [agent] [source_note]" >&2
      exit 1
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ ${#ARGS[@]} -lt 2 ]]; then
  echo "Usage: generate-task-spec.sh [--status=ready|blocked] [--queue] <slug> <effort> [agent] [source_note]" >&2
  exit 1
fi

SLUG="${ARGS[0]}"
EFFORT="${ARGS[1]}"
AGENT="${ARGS[2]:-any}"
SOURCE_NOTE="${ARGS[3]:-(none)}"

if [[ "$EFFORT" != "S" && "$EFFORT" != "M" ]]; then
  echo "ERROR: effort must be S or M. L/XL belong in SDD (AgentSpec/OpenSpec/SpecKit), not Task-Spec." >&2
  exit 1
fi

case "$PROFILE" in
  lite|standard|full) ;;
  *)
    echo "ERROR: profile must be lite, standard, or full (got: '$PROFILE')" >&2
    exit 1
    ;;
esac

if ! [[ "$SLUG" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "ERROR: slug must be lowercase kebab-case (e.g., 'verify-langfuse-otel')" >&2
  exit 1
fi

DATE="$(date +%Y%m%d)"
CREATED="$(date -u +%FT%TZ)"
ID="T-${DATE}-${SLUG}"
# Resolve output directory
GIT_ROOT=""
if command -v git >/dev/null 2>&1; then
  GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
fi
if [[ -z "$GIT_ROOT" ]]; then
  GIT_ROOT="$(pwd)"
fi

if [[ "$QUEUE" == true ]]; then
  OUTDIR="$GIT_ROOT/tasks/queue"
elif [[ "$STATUS" == "ready" && -d "$GIT_ROOT/tasks/queue" ]]; then
  OUTDIR="$GIT_ROOT/tasks/queue"
else
  OUTDIR="$GIT_ROOT/tasks"
fi

TARGET="$OUTDIR/${ID}.md"

if [[ -f "$TARGET" ]]; then
  echo "ERROR: $TARGET already exists. Pick a different slug." >&2
  exit 1
fi

mkdir -p "$OUTDIR"

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEMPLATE="$SKILL_DIR/templates/task-spec.md.tpl"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "ERROR: template not found at $TEMPLATE" >&2
  exit 1
fi

sed \
  -e "s|{{ID}}|$ID|g" \
  -e "s|{{TITLE}}|{{TODO: one-line title in imperative voice}}|g" \
  -e "s|{{STATUS}}|$STATUS|g" \
  -e "s|{{PROFILE}}|$PROFILE|g" \
  -e "s|{{EFFORT}}|$EFFORT|g" \
  -e "s|{{BUDGET_ITERATIONS}}|15|g" \
  -e "s|{{AGENT}}|$AGENT|g" \
  -e "s|{{DEPENDS_ON}}|[]|g" \
  -e "s|{{TOUCHES_PATHS_YAML}}|  - {{TODO: path/to/file}}|g" \
  -e "s|{{SOURCE_NOTE}}|$SOURCE_NOTE|g" \
  -e "s|{{CREATED}}|$CREATED|g" \
  -e "s|{{TAGS}}|[]|g" \
  -e "s|{{WHY_ONE_PARAGRAPH}}|{{TODO: 1-2 sentence why}}|g" \
  -e "s|{{GOAL_ONE_PARAGRAPH}}|{{TODO: concrete success in one paragraph}}|g" \
  -e "s|{{CONTEXT_LEAN_MAX_100_LINES}}|{{TODO: lean context, link to existing docs}}|g" \
  -e "s|{{B1_GIVEN}}|{{TODO: precondition}}|g" \
  -e "s|{{B1_WHEN}}|{{TODO: action}}|g" \
  -e "s|{{B1_THEN}}|{{TODO: observable outcome}}|g" \
  -e "s|{{B2_GIVEN}}|{{TODO: precondition}}|g" \
  -e "s|{{B2_WHEN}}|{{TODO: action}}|g" \
  -e "s|{{B2_THEN}}|{{TODO: observable outcome}}|g" \
  -e "s|{{AGENT_PRODUCES}}|code \\| docs \\| config \\| tests|g" \
  -e "s|{{DO_NOT_TOUCH_LIST}}|- {{TODO: exact path or (none)}}|g" \
  "$TEMPLATE" > "$TARGET"

# Append _metrics.jsonl entry
mkdir -p "$OUTDIR"
METRICS="$OUTDIR/_metrics.jsonl"
echo "{\"schema_version\":1,\"ts\":\"$CREATED\",\"task\":\"$ID\",\"event\":\"created\",\"author\":\"$(whoami)\",\"source\":\"$SOURCE_NOTE\",\"effort\":\"$EFFORT\",\"agent\":\"$AGENT\"}" >> "$METRICS"

# Trigger state rebuild
if [[ -x "$SKILL_DIR/src/backlog/rebuild-state.sh" ]]; then
  bash "$SKILL_DIR/src/backlog/rebuild-state.sh" >/dev/null 2>&1 || true
fi

echo "Spec written: $TARGET"
echo "  status: $STATUS  outdir: $OUTDIR  task_spec_version: $TASKSPEC_VERSION"
echo ""
echo "Next steps:"
echo ""
echo "  1. Fill in the {{TODO}} stubs:"
echo "     - title"
echo "     - touches_paths"
echo "     - why / goal / context"
echo "     - eval_1, eval_2, eval_3 (runnable bash — avoid the inverted-grep-c"
echo "       footgun; use '! grep -q PATTERN file' instead of '\$(grep -c X file"
echo "       || echo 0); [ \"\$count\" -eq 0 ]')"
echo "     - anti-patterns + do-not-touch"
echo ""
echo "  2. VALIDATE (pre-gate structural linter — does NOT stamp signed_off):"
echo "     bash $SKILL_DIR/src/gate/validate-task-spec.sh $TARGET"
echo ""
echo "Next: bash $SKILL_DIR/src/gate/safe-to-delegate.sh --stamp $TARGET"
echo ""
echo "     The gate is THE only path to signed_off:true. Hand-stamping the"
echo "     signed_off field is rejected by the structural sign-off envelope check."
echo "     See: docs/concepts/signed-off.md"
echo ""
echo "  3. DISPATCH (after the gate stamps signed_off:true):"
echo "     See docs/runbooks/dispatching-a-task-spec.md for the handoff protocol"
echo "     per execution_backend (kimi, claude, codex, taskship, ...)."
