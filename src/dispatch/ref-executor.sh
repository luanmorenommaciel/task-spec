#!/usr/bin/env bash
# ref-executor.sh — the canonical reference Task-Spec EXECUTOR (L2-conformant).
#
# This is NOT an AI agent. It is the smallest possible thing that honors the
# Task-Spec consumer contract end-to-end, so that:
#   1. conformance-check.sh --self-test has a known-good target, and
#   2. adapter authors have a 60-line worked example of "what an executor does."
#
# The contract it honors (mirrors the on_pickup / per_iteration / on_terminal
# blocks in README's "agent contract"):
#   on pickup        : status ready → in-progress  (acquire the lock)
#   per iteration    : attempt the work, then run the Exit Check
#   on success       : independent acceptance → status done
#   on budget exhaust: status → parked  (with a blocked_reason)
#
# Its "work" is deliberately dumb: it reads the Goal and, if the Goal asks it to
# write a literal string into a file (the conformance solvable spec), it does so.
# A real executor swaps this one block for an AI agent / build tool. Everything
# else — the lifecycle, the budget loop, the park — is the part that MATTERS and
# is identical for any executor.
#
# Usage: taskspec executor <path/to/T-*.md>

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/_lib.sh
source "$SCRIPT_DIR/../lib/_lib.sh"
ts_version_flag "$@"

if [[ $# -ne 1 ]]; then
  echo "Usage: taskspec executor <task-spec>" >&2
  exit 2
fi
SPEC="$1"
[[ -f "$SPEC" ]] || { echo "no such spec: $SPEC" >&2; exit 2; }

GIT_ROOT=$(cd "$(dirname "$SPEC")" && git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
export GIT_ROOT

budget=$(grep -m1 '^budget_iterations:' "$SPEC" | awk '{print $2}'); budget="${budget:-10}"
read retry_max no_progress < <(python3 - "$SPEC" "$TASKSPEC_SKILL_DIR/src/lib" <<'PY'
import re,sys
sys.path.insert(0,sys.argv[2])
from taskspec_data import parse_yaml_subset
text=open(sys.argv[1],encoding="utf-8").read()
m=re.search(r"## Validation Card.*?```ya?ml\s*\n(.*?)```",text,re.S|re.I)
card=parse_yaml_subset(m.group(1)) if m else {}
retry=card.get("retry_policy",{}) if isinstance(card,dict) else {}
print(retry.get("max_iterations",1),retry.get("circuit_breaker_no_progress",1))
PY
)
if [[ "$retry_max" -gt "$budget" ]]; then
  echo "taskspec executor: retry_policy.max_iterations exceeds signed budget_iterations" >&2
  exit 1
fi
effective_max="$retry_max"
TASK_ID="$(grep -m1 '^id:' "$SPEC" | awk '{print $2}')"
HANDOFF_FILE="$(mktemp -t taskspec-ref-handoff-XXXXXX.json)"
trap 'rm -f "$HANDOFF_FILE"' EXIT
HANDOFF_BACKEND="$(grep -m1 '^execution_backend:' "$SPEC" | awk '{print $2}')"
[[ -n "$HANDOFF_BACKEND" && "$HANDOFF_BACKEND" != "any" ]] || HANDOFF_BACKEND=ref-executor
python3 "$SCRIPT_DIR/handoff.py" "$SPEC" --backend "$HANDOFF_BACKEND" --out "$HANDOFF_FILE" --force >/dev/null

# --- on pickup: acquire the lock ---
bash "$SCRIPT_DIR/../backlog/transition-status.sh" "$TASK_ID" in-progress >/dev/null

# --- the swappable "work" block (a real executor calls an AI agent here) ---
attempt_work() {
  # Heuristic for the reference fixtures: if the Goal says write `done` into a
  # marker file, do exactly that. Anything else, this dumb executor cannot do
  # (so an unsolvable spec naturally exhausts budget → park).
  if grep -qiE 'write the literal text .?done.? into .?src/marker\.txt' "$SPEC"; then
    mkdir -p "$GIT_ROOT/src"
    printf 'done\n' > "$GIT_ROOT/src/marker.txt"
  fi
}

# --- per-iteration loop, bounded by budget_iterations ---
i=0; repeated=0; previous_failure=""
while [[ $i -lt $effective_max ]]; do
  i=$((i + 1))
  attempt_work
  if bash "$SCRIPT_DIR/../gate/run-task-spec.sh" "$SPEC" >/dev/null 2>&1; then
    # --- on success: independently accept, then release as done ---
    if ! bash "$SCRIPT_DIR/../accept/accept-task.sh" --stamp --handoff "$HANDOFF_FILE" \
      --accepted-by ref-executor "$SPEC" >/dev/null 2>&1; then
      bash "$SCRIPT_DIR/../backlog/transition-status.sh" "$TASK_ID" parked "reference acceptance gate rejected the work" >/dev/null
      echo "ref-executor: evals passed but acceptance rejected → status: parked"
      exit 0
    fi
    bash "$SCRIPT_DIR/../backlog/transition-status.sh" "$TASK_ID" done >/dev/null
    echo "ref-executor: PASS after $i iteration(s) → status: done"
    exit 0
  fi
  failure="$(bash "$SCRIPT_DIR/../gate/run-task-spec.sh" "$SPEC" 2>&1 || true)"
  failure_digest="$(printf '%s' "$failure" | ts_sha256)"
  if [[ "$failure_digest" == "$previous_failure" ]]; then repeated=$((repeated + 1)); else repeated=1; previous_failure="$failure_digest"; fi
  if [[ "$repeated" -ge "$no_progress" ]]; then
    bash "$SCRIPT_DIR/../backlog/transition-status.sh" "$TASK_ID" parked "circuit_breaker_no_progress reached after identical failing eval results" >/dev/null
    echo "ref-executor: no-progress circuit breaker after $i iteration(s) → status: parked"
    exit 0
  fi
done

# --- on budget exhaustion: park with context (never loop forever) ---
bash "$SCRIPT_DIR/../backlog/transition-status.sh" "$TASK_ID" parked "retry_policy.max_iterations ($effective_max) exhausted without a passing Exit Check" >/dev/null
echo "ref-executor: retry budget exhausted after $i iteration(s) → status: parked"
exit 0
