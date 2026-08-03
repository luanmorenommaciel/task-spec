#!/usr/bin/env bash
# install.sh — Install the task-spec agent surface (task-architect + thin skill).
#
# The engine itself needs no installation: clone this repo and put
# bin/taskspec on PATH (e.g. `ln -s "$PWD/bin/taskspec" /usr/local/bin/`).
# This script installs the OPTIONAL Claude Code surface from the repo root:
#   1. agents/*.md                       → <target>/.claude/agents/
#   2. integrations/claude-code/SKILL.md → <target>/.claude/skills/task-spec/
#
# Defaults to project-local install under --target (or PWD).
# Use --global to install under ~/.claude/ instead.
# Use --namespace=<name> to prefix the agent filename and avoid colliding with
# an existing `task-architect` agent in the target repo.
#
# Usage:
#   bash src/lib/install.sh                          # install in current repo (PWD)
#   bash src/lib/install.sh --target /path/to/repo   # install in a specific repo
#   bash src/lib/install.sh --global                 # install under ~/.claude/
#   bash src/lib/install.sh --namespace=my-task      # use my-task-task-architect.md
#   bash src/lib/install.sh --version                # print version and exit
#
# Exit codes:
#   0   success (or already installed — idempotent)
#   1   usage error
#   2   target not writable / IO error

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
source "$SCRIPT_DIR/_lib.sh"
ts_version_flag "$@"

# REPO_ROOT = the task-spec engine repo root (install.sh lives at src/lib/).
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TARGET=""
GLOBAL=false
NAMESPACE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target=*)   TARGET="${1#*=}"; shift ;;
    --target)     TARGET="${2:-}"; shift 2 ;;
    --global)     GLOBAL=true; shift ;;
    --namespace=*) NAMESPACE="${1#*=}"; shift ;;
    --namespace)  NAMESPACE="${2:-}"; shift 2 ;;
    --help|-h)
      sed -n '2,24p' "$0"; exit 0 ;;
    *) ts_die "Unknown option: $1" ;;
  esac
done

# Resolve install roots
if [[ "$GLOBAL" == "true" ]]; then
  AGENTS_DST="$HOME/.claude/agents"
  SKILL_DST="$HOME/.claude/skills/task-spec"
else
  TARGET="${TARGET:-$PWD}"
  if [[ ! -d "$TARGET" ]]; then
    ts_die "Target directory does not exist: $TARGET"
  fi
  AGENTS_DST="$TARGET/.claude/agents"
  SKILL_DST="$TARGET/.claude/skills/task-spec"
fi

echo "Installing task-spec v$TASKSPEC_VERSION agent surface → $AGENTS_DST"
mkdir -p "$AGENTS_DST" "$SKILL_DST" || ts_die "cannot create $AGENTS_DST / $SKILL_DST"

# 1. Install the bundled agent(s) from the engine repo root agents/.
if [[ -d "$REPO_ROOT/agents" ]]; then
  for f in "$REPO_ROOT"/agents/*.md; do
    [[ -e "$f" ]] || continue
    base="$(basename "$f")"
    if [[ -n "$NAMESPACE" ]]; then
      base="${NAMESPACE}-${base}"
    fi
    if [[ -f "$AGENTS_DST/$base" ]]; then
      echo "  SKIP: $AGENTS_DST/$base already exists"
    else
      cp "$f" "$AGENTS_DST/$base"
      echo "  agent: $AGENTS_DST/$base"
    fi
  done
fi

# 2. Install the thin Claude Code skill (delegates to the taskspec CLI).
if [[ -f "$REPO_ROOT/integrations/claude-code/SKILL.md" ]]; then
  cp "$REPO_ROOT/integrations/claude-code/SKILL.md" "$SKILL_DST/SKILL.md"
  echo "  skill: $SKILL_DST/SKILL.md"
fi

echo ""
echo "Done. task-spec v$TASKSPEC_VERSION agent surface installed."
echo ""
echo "The engine CLI is separate — put it on PATH once:"
echo "  ln -s \"$REPO_ROOT/bin/taskspec\" /usr/local/bin/taskspec"
echo ""
echo "Then, in any repo with a tasks/ backlog:"
echo "  taskspec new <slug> <effort>     # author a spec"
echo "  taskspec gate --stamp tasks/T-*.md"
echo ""
echo "Configure backlog directory (optional):"
echo "  export TASKSPEC_BACKLOG_DIR=path/to/backlog   # default: tasks"
