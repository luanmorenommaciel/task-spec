#!/usr/bin/env bash
# Run a complete Task-Spec lifecycle in an isolated disposable repository.
set -euo pipefail

if [[ "${TASKSPEC_DRY_RUN:-0}" == "1" ]]; then
  echo "DEMO=DRY_RUN isolated lifecycle would run"
  exit 0
fi

# PRE-gate hard-requires shellcheck. Check the host floor before any redirected
# work so a missing floor cannot exit 1 with empty stdout and empty stderr.
if ! command -v shellcheck >/dev/null 2>&1; then
  echo "DEMO=BLOCKED"
  echo "BLOCKER: shellcheck is not installed (required by PRE-gate)"
  echo "NEXT: install shellcheck, then re-run: taskspec demo"
  exit 1
fi

ROOT="${TASKSPEC_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
CLI="$ROOT/bin/taskspec"
WORK="$(mktemp -d -t taskspec-demo-XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

PROJECT="$WORK/project"
PLAN="$PROJECT/tasks/.plans/demo.yaml"
SPEC="$PROJECT/tasks/T-20260812-prove-task-spec.md"
mkdir -p "$PROJECT"

git -C "$PROJECT" init -q
git -C "$PROJECT" config user.email demo@taskspec.local
git -C "$PROJECT" config user.name "Task-Spec demo"

(
  cd "$PROJECT"
  # Redirected PRE-gate / CLI steps must not fail silent if a later host or
  # contract check dies under set -e.
  trap 'echo "DEMO=BLOCKED isolated lifecycle failed. NEXT: taskspec doctor"' ERR
  "$CLI" init >/dev/null
  "$CLI" setup signing >/dev/null
  mkdir -p tasks/.plans src
  cat > "$PLAN" <<'PLAN'
api_version: taskspec.dev/v1
kind: TaskPlan
approved: true
metadata:
  name: prove-task-spec
units:
  - id: T-20260812-prove-task-spec
    title: Prove the isolated Task-Spec lifecycle
    effort: XS
    profile: standard
    agent: any
    execution_backend: any
    depends_on: []
    touches_paths: []
    creates_paths:
      - src/task-spec-demo.txt
    source_note: taskspec demo
    why: A fresh install needs one safe command that proves the complete lifecycle.
    goal: Write the literal text accepted into src/task-spec-demo.txt.
    context: This disposable repository is created and removed by taskspec demo.
    behaviors:
      - id: B-1
        given: the proof file does not exist
        when: the authorized demo leaf executes
        then: src/task-spec-demo.txt contains exactly accepted
    evals:
      - id: eval_1
        description: proof file contains exactly accepted
        command: grep -qx 'accepted' src/task-spec-demo.txt
        verifies:
          - B-1
        terminal: true
        expected_duration_sec: 1
    do_not_touch:
      - .git/info/taskspec-signing-key
PLAN

  "$CLI" plan --manifest "$PLAN" >/dev/null
  "$CLI" batch --plan "$PLAN" >/dev/null
  "$CLI" validate "$SPEC" >/dev/null
  dod_output=$("$CLI" dod "$SPEC")
  grep -q 'DOD=COMPLETE' <<< "$dod_output"
  gate_output=$("$CLI" gate --stamp "$SPEC")
  grep -q 'VERDICT: DELEGATE' <<< "$gate_output"
  grep -q 'TIER=1' <<< "$gate_output"

  git add .
  git commit -qm "Seal isolated Task-Spec demo"

  "$CLI" handoff "$SPEC" --backend any --out tasks/.plans/demo-handoff.json >/dev/null
  python3 -c 'import json; d=json.load(open("tasks/.plans/demo-handoff.json")); assert d["contract"] == "TaskHandoff/v3" and d["signoff_tier"] == 1 and d["attempt"]["id"]'
  printf 'accepted\n' > src/task-spec-demo.txt
  "$CLI" run "$SPEC" >/dev/null
  accept_output=$("$CLI" accept --stamp --handoff tasks/.plans/demo-handoff.json "$SPEC")
  grep -q 'ACCEPTED=1' <<< "$accept_output"
  "$CLI" validate "$SPEC" >/dev/null
)

cat <<'EOF'
Task-Spec isolated lifecycle
  PLAN=VALID
  DOD=COMPLETE
  VERDICT=DELEGATE TIER=1
  HANDOFF=TaskHandoff/v3
  EVAL=PASS
  ACCEPTED=1
DEMO=READY
EOF
