#!/usr/bin/env bash
# lint-backlog.sh — Cross-task linter for the task-spec backlog.
#
# Detects:
#   (a) touches_paths overlaps between active (non-parked, non-archive) tasks
#   (b) depends_on cycles via tsort (with pure-bash fallback)
#   (b2) depends_on referencing a non-existent task (dangling DAG edge)
#   (c) duplicate id values across the backlog
#   (d) stale precondition references
#
# Usage:
#   bash lint-backlog.sh [--help]
#
# Exit codes:
#   0 — no issues
#   1 — one or more issues found

set -euo pipefail

# shellcheck source=../lib/_lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/_lib.sh"
ts_version_flag "$@"
ts_require_bash4 "$@"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: bash lint-backlog.sh [--help]"
  echo ""
  echo "Cross-task linter for the task-spec backlog. Detects:"
  echo "  - touches_paths overlaps between active tasks"
  echo "  - depends_on cycles"
  echo "  - depends_on referencing a non-existent task"
  echo "  - duplicate task IDs"
  echo "  - stale precondition references"
  echo ""
  echo "Output: one line per issue. Exits non-zero if any issues are found."
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# The backlog under lint belongs to the repo the user runs this FROM (PWD),
# not to the task-spec engine repo. Anchor at the caller's git root.
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# Data structures
# task_status[id] = status
# task_file[id] = filepath
# task_touches[id] = "path1 path2 ..."
# task_depends[id] = "dep1 dep2 ..."
# task_precondition[id] = "precondition text"
declare -A task_status
declare -A task_file
declare -A task_touches
declare -A task_depends
declare -A task_precondition

# List of all task IDs
declare -a all_ids=()

# Helper: extract frontmatter from a file (delegates to the shared _lib.sh
# implementation — single source of truth, was previously a verbatim copy).
extract_frontmatter() {
  ts_frontmatter "$1"
}

# Helper: parse YAML list from frontmatter block
parse_yaml_list() {
  local key="$1"
  local block="$2"
  local line
  line=$(echo "$block" | grep "^${key}:" | head -1 || true)
  if [[ -z "$line" ]]; then
    return 0
  fi
  if echo "$line" | grep -qE '\['; then
    local result
    result=$(echo "$line" | sed -n 's/.*\[\(.*\)\].*/\1/p' | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || true)
    echo "$result" | grep -v '^$' || true
  elif echo "$line" | grep -qE "^${key}:[[:space:]]*$"; then
    echo "$block" | sed -n "/^${key}:/,/^[^ #]/p" | tail -n +2 | sed '/^[^ ]/d' | sed 's/^[[:space:]]*-[[:space:]]*//' | grep -v '^$' || true
  fi
  return 0
}

# Discover all task files
mapfile -t task_files < <(find tasks -name 'T-*.md' -type f 2>/dev/null | sort)

if [[ ${#task_files[@]} -eq 0 ]]; then
  echo "No task files found in tasks/"
  exit 0
fi

# Parse all task files
for f in "${task_files[@]}"; do
  fm=$(extract_frontmatter "$f")
  id=$(echo "$fm" | grep "^id:" | head -1 | awk '{print $2}' || true)
  status=$(echo "$fm" | grep "^status:" | head -1 | awk '{print $2}' || true)
  
  if [[ -z "$id" ]]; then
    echo "WARNING: $f missing id field"
    continue
  fi
  
  task_status[$id]="${status:-unknown}"
  task_file[$id]="$f"
  all_ids+=("$id")
  
  touches=$(parse_yaml_list "touches_paths" "$fm")
  if [[ -n "$touches" ]]; then
    task_touches[$id]="$touches"
  fi
  
  deps=$(parse_yaml_list "depends_on" "$fm")
  if [[ -n "$deps" ]]; then
    task_depends[$id]="$deps"
  fi
  
  # Extract precondition text
  pc_line=$(echo "$fm" | grep "^precondition:" | head -1 || true)
  if [[ -n "$pc_line" ]]; then
    pc_text=$(echo "$pc_line" | sed 's/^precondition:[[:space:]]*//' | sed 's/^"//;s/"$//;s/^'"'"'//;s/'"'"'$//')
    task_precondition[$id]="$pc_text"
  fi
done

ERRORS=0
WARNINGS=0

# ---------------------------------------------------------------------------
# Check (a): touches_paths overlaps between active tasks
# ---------------------------------------------------------------------------
# Build map: path -> "id1 id2 ..."
declare -A path_owners

for id in "${all_ids[@]}"; do
  status=${task_status[$id]}
  f=${task_file[$id]}
  
  # Skip parked tasks and archive tasks for overlap detection
  if [[ "$status" == "parked" ]]; then
    continue
  fi
  if [[ "$f" == tasks/archive/* ]]; then
    continue
  fi
  
  touches=${task_touches[$id]:-}
  if [[ -z "$touches" ]]; then
    continue
  fi
  
  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    if [[ -z "${path_owners[$path]+x}" ]]; then
      path_owners[$path]="$id"
    else
      path_owners[$path]="${path_owners[$path]} $id"
    fi
  done <<< "$touches"
done

# Determine if a path is a code/script file
code_exts='\.(sh|py|js|ts|go|rs|java|rb|pl|c|cpp|h|hpp|cs|swift|kt|scala|r|m|mm|lua|vim|ps1|bat|cmd|php|tcl|awk|sed)$'

for path in "${!path_owners[@]}"; do
  owners=${path_owners[$path]}
  count=$(echo "$owners" | wc -w | tr -d ' ')
  
  if [[ "$count" -gt 1 ]]; then
    # Filter out any parked/archive owners that might have slipped in
    active_owners=""
    for owner in $owners; do
      owner_status=${task_status[$owner]}
      owner_file=${task_file[$owner]}
      if [[ "$owner_status" != "parked" && "$owner_file" != tasks/archive/* ]]; then
        if [[ -z "$active_owners" ]]; then
          active_owners="$owner"
        else
          active_owners="$active_owners $owner"
        fi
      fi
    done
    
    active_count=$(echo "$active_owners" | wc -w | tr -d ' ')
    if [[ "$active_count" -gt 1 ]]; then
      if echo "$path" | grep -qiE "$code_exts"; then
        echo "ERROR: touches_paths overlap on '$path' between tasks: $active_owners"
        ERRORS=$((ERRORS + 1))
      else
        echo "WARNING: touches_paths overlap on '$path' between tasks: $active_owners"
        WARNINGS=$((WARNINGS + 1))
      fi
    fi
  fi
done

# ---------------------------------------------------------------------------
# Check (b2): depends_on referencing a non-existent task (dangling DAG edge)
# ---------------------------------------------------------------------------
# The tsort/DFS edge-builders below only add an edge when BOTH endpoints exist
# (the '${task_file[$dep]+x}' guard), which means a depends_on pointing at a task
# that is not in the backlog is silently DROPPED and never surfaced. Report it
# here so a typo'd or purged dependency is caught at the backlog level (the
# per-file validator already catches it for a single spec; this is the cross-task
# net). Additive: does not alter the edge-building or cycle logic below.
for id in "${all_ids[@]}"; do
  deps=${task_depends[$id]:-}
  [[ -z "$deps" ]] && continue
  for dep in $deps; do
    [[ -z "$dep" ]] && continue
    if [[ -z "${task_file[$dep]+x}" ]]; then
      echo "ERROR: depends_on references non-existent task: '$dep' (declared by $id)"
      ERRORS=$((ERRORS + 1))
    fi
  done
done

# ---------------------------------------------------------------------------
# Check (b): depends_on cycles
# ---------------------------------------------------------------------------
# Build adjacency list for tsort
tsort_input=$(mktemp)
tsort_nodes=$(mktemp)

for id in "${all_ids[@]}"; do
  deps=${task_depends[$id]:-}
  echo "$id" >> "$tsort_nodes"
  if [[ -n "$deps" ]]; then
    for dep in $deps; do
      # Only include edges where both nodes exist
      if [[ -n "${task_file[$dep]+x}" ]]; then
        echo "$dep $id" >> "$tsort_input"
        echo "$dep" >> "$tsort_nodes"
      fi
    done
  fi
done

# tsort approach
if command -v tsort >/dev/null 2>&1; then
  tsort_err=$(tsort "$tsort_input" 2>&1 >/dev/null) || true
  if echo "$tsort_err" | grep -qi "cycle"; then
    cycle_line=$(echo "$tsort_err" | grep -i "cycle" | head -1)
    # NOTE: 'grep -v ^tsort:' matches NOTHING for a pure cycle (every tsort line
    # is 'tsort:'-prefixed), returning exit 1. As a standalone assignment under
    # 'set -euo pipefail' that aborted the whole script BEFORE the echo below —
    # so cycles were detected (rc=1) but reported SILENTLY. The trailing '|| true'
    # neutralises the empty-match exit so the ERROR line always prints.
    cycle_nodes=$(echo "$tsort_err" | grep -v "^tsort:" | head -5 | tr '\n' ' ' || true)
    echo "ERROR: depends_on cycle detected ($cycle_line) involving: $cycle_nodes"
    ERRORS=$((ERRORS + 1))
  fi
else
  # Pure bash fallback: DFS cycle detection
  declare -A adj
  for id in "${all_ids[@]}"; do
    deps=${task_depends[$id]:-}
    adj[$id]="$deps"
  done
  
  cycle_found=0
  for start in "${all_ids[@]}"; do
    [[ $cycle_found -eq 1 ]] && break
    declare -A visited=()
    declare -A recstack=()
    
    dfs() {
      local node=$1
      visited[$node]=1
      recstack[$node]=1
      local neighbors=${adj[$node]:-}
      for neighbor in $neighbors; do
        [[ -z "${task_file[$neighbor]+x}" ]] && continue
        if [[ -z "${visited[$neighbor]+x}" ]]; then
          dfs "$neighbor"
          [[ $cycle_found -eq 1 ]] && return
        elif [[ "${recstack[$neighbor]:-0}" == "1" ]]; then
          echo "ERROR: depends_on cycle detected involving $neighbor"
          cycle_found=1
          return
        fi
      done
      recstack[$node]=0
    }
    
    dfs "$start"
  done
  
  if [[ $cycle_found -eq 1 ]]; then
    ERRORS=$((ERRORS + 1))
  fi
fi

rm -f "$tsort_input" "$tsort_nodes"

# ---------------------------------------------------------------------------
# Check (c): duplicate IDs
# ---------------------------------------------------------------------------
declare -A id_files

for id in "${all_ids[@]}"; do
  f=${task_file[$id]}
  if [[ -z "${id_files[$id]+x}" ]]; then
    id_files[$id]="$f"
  else
    id_files[$id]="${id_files[$id]} $f"
  fi
done

for id in "${!id_files[@]}"; do
  files=${id_files[$id]}
  count=$(echo "$files" | wc -w | tr -d ' ')
  if [[ "$count" -gt 1 ]]; then
    echo "ERROR: duplicate id '$id' found in files: $files"
    ERRORS=$((ERRORS + 1))
  fi
done

# ---------------------------------------------------------------------------
# Check (d): stale precondition references
# ---------------------------------------------------------------------------
for id in "${all_ids[@]}"; do
  pc=${task_precondition[$id]:-}
  [[ -z "$pc" ]] && continue
  
  status=${task_status[$id]}
  
  # Extract path-like tokens from precondition text
  path_tokens=$(echo "$pc" | grep -oE '[a-zA-Z0-9_.][a-zA-Z0-9_./-]*' | grep '/' | grep -v '://' | sort -u || true)
  
  while IFS= read -r token; do
    [[ -z "$token" ]] && continue
    
    # Resolve relative to repo root
    if [[ -e "$token" ]]; then
      # Path exists — if task is active, precondition may be stale
      if [[ "$status" == "ready" || "$status" == "in-progress" || "$status" == "blocked" ]]; then
        echo "WARNING: stale precondition in $id: referenced path exists, work may be unblocked: $token"
        WARNINGS=$((WARNINGS + 1))
      fi
    else
      # Path does not exist — if task is done, the precondition was never met
      if [[ "$status" == "done" ]]; then
        echo "WARNING: stale precondition in $id: referenced path missing for done task: $token"
        WARNINGS=$((WARNINGS + 1))
      fi
    fi
  done <<< "$path_tokens"
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
if [[ $ERRORS -gt 0 || $WARNINGS -gt 0 ]]; then
  exit 1
fi

exit 0
