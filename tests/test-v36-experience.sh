#!/usr/bin/env bash
# Clean-room 3.6 journey plus CLI, installer, provider, and packaging contracts.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0
pass() { echo "  ✓ $1"; PASS=$((PASS + 1)); }
fail() { echo "  ✗ $1" >&2; FAIL=$((FAIL + 1)); }
check() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then pass "$name"; else fail "$name"; fi; }

WORK="$(mktemp -d -t taskspec-v36-XXXXXX)"
TARGET="$WORK/project"
INSTALL_ROOT="$WORK/install-root"
BIN_DIR="$WORK/bin"
mkdir -p "$TARGET" "$INSTALL_ROOT" "$BIN_DIR"

echo "== install =="
if TASKSPEC_INSTALL_ROOT="$INSTALL_ROOT" bash "$ROOT/install.sh" --target "$TARGET" --copy --bin-dir "$BIN_DIR" >"$WORK/install.out" 2>&1 \
  && grep -q '^INSTALL=OK$' "$WORK/install.out"; then pass "copy install"; else fail "copy install"; fi
if TASKSPEC_INSTALL_ROOT="$INSTALL_ROOT" bash "$ROOT/install.sh" --target "$TARGET" --copy --bin-dir "$BIN_DIR" >"$WORK/reinstall.out" 2>&1 \
  && grep -q '^INSTALL=OK$' "$WORK/reinstall.out"; then pass "idempotent install"; else fail "idempotent install"; fi
if [[ "$(shasum -a 256 "$TARGET/.agents/skills/task-spec/SKILL.md" | awk '{print $1}')" == "$(shasum -a 256 "$TARGET/.claude/skills/task-spec/SKILL.md" | awk '{print $1}')" \
   && "$(shasum -a 256 "$TARGET/.agents/skills/task-spec/SKILL.md" | awk '{print $1}')" == "$(shasum -a 256 "$TARGET/.grok/skills/task-spec/SKILL.md" | awk '{print $1}')" ]]; then pass "equivalent harness skills"; else fail "equivalent harness skills"; fi

SYMLINK_TARGET="$WORK/symlink-project"
SYMLINK_ROOT="$WORK/symlink-root"
SYMLINK_BIN="$WORK/symlink-bin"
mkdir -p "$SYMLINK_TARGET" "$SYMLINK_ROOT" "$SYMLINK_BIN"
if TASKSPEC_INSTALL_ROOT="$SYMLINK_ROOT" bash "$ROOT/install.sh" --target "$SYMLINK_TARGET" --symlink --bin-dir "$SYMLINK_BIN" >"$WORK/symlink.out" 2>&1 \
  && [[ -L "$SYMLINK_TARGET/.agents/skills/task-spec" ]] \
  && [[ -L "$SYMLINK_TARGET/.claude/skills/task-spec" ]] \
  && [[ -L "$SYMLINK_TARGET/.grok/skills/task-spec" ]] \
  && [[ -L "$SYMLINK_TARGET/.claude/agents/task-architect.md" ]] \
  && [[ "$($SYMLINK_BIN/taskspec version)" == "3.6.0" ]]; then
  pass "checkout symlink install"
else
  fail "checkout symlink install"
fi

NO_BIN_TARGET="$WORK/no-bin-project"
NO_BIN_ROOT="$WORK/no-bin-root"
NO_BIN_DIR="$WORK/must-remain-empty"
mkdir -p "$NO_BIN_TARGET" "$NO_BIN_ROOT" "$NO_BIN_DIR"
if TASKSPEC_INSTALL_ROOT="$NO_BIN_ROOT" bash "$ROOT/install.sh" --target "$NO_BIN_TARGET" --copy --no-bin --bin-dir "$NO_BIN_DIR" >"$WORK/no-bin.out" 2>&1 \
  && [[ ! -e "$NO_BIN_DIR/taskspec" ]]; then pass "skills-only install"; else fail "skills-only install"; fi

TS="$BIN_DIR/taskspec"
check "installed version" bash -c "[[ \"\$('$TS' version)\" == 3.6.0 ]]"
check "agent context JSON" bash -c "'$TS' agent-context | python3 -m json.tool"
check "global JSON envelope" bash -c "'$TS' --json help | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d[\"ok\"] and d[\"command\"] == \"help\"'"
for shell_name in bash zsh fish; do check "completion $shell_name" bash -c "test -n \"\$('$TS' completion '$shell_name')\""; done

echo "== clean-room journey =="
git -C "$TARGET" init -q
git -C "$TARGET" config user.email test@taskspec.local
git -C "$TARGET" config user.name "Task-Spec test"
set +e
(
  cd "$TARGET"
  "$TS" init
  "$TS" setup signing
  "$TS" setup signing
  mkdir -p tasks/.plans src
  cat > tasks/.plans/marker.yaml <<'PLAN'
api_version: taskspec.dev/v1
kind: TaskPlan
approved: true
metadata:
  name: marker-clean-room
units:
  - id: T-20260811-write-marker
    title: Write the accepted marker
    effort: XS
    profile: standard
    agent: any
    execution_backend: codex
    depends_on: []
    touches_paths: []
    creates_paths:
      - src/marker.txt
    source_note: tests/test-v36-experience.sh
    why: A marker is the smallest discriminating clean-room execution.
    goal: Write the literal text done into src/marker.txt.
    context: The stub executor performs exactly one declared write.
    behaviors:
      - id: B-1
        given: the marker does not exist
        when: the authorized leaf executes
        then: src/marker.txt contains exactly done
    evals:
      - id: eval_1
        description: marker contains exactly done
        command: grep -qx 'done' src/marker.txt
        verifies:
          - B-1
        terminal: true
        expected_duration_sec: 1
    do_not_touch:
      - .git/info/taskspec-signing-key
PLAN
  "$TS" plan --manifest tasks/.plans/marker.yaml
  "$TS" batch --plan tasks/.plans/marker.yaml
  "$TS" validate tasks/T-20260811-write-marker.md
  "$TS" dod tasks/T-20260811-write-marker.md
  "$TS" gate --stamp tasks/T-20260811-write-marker.md
  git add .
  git commit -qm "sealed clean-room task"
  "$TS" handoff tasks/T-20260811-write-marker.md --backend codex > "$WORK/handoff.json"
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["contract"] == "TaskHandoff/v1" and d["signoff_tier"] == 1' "$WORK/handoff.json"
  printf 'done\n' > src/marker.txt
  "$TS" run tasks/T-20260811-write-marker.md
  "$TS" accept --stamp tasks/T-20260811-write-marker.md
  "$TS" transition T-20260811-write-marker done
  "$TS" validate tasks/done/T-20260811-write-marker.md
) >"$WORK/journey.out" 2>&1
journey_rc=$?
set -e
if [[ "$journey_rc" -eq 0 ]] && grep -q 'ACCEPTED=1' "$WORK/journey.out" && grep -q 'DOD=COMPLETE' "$WORK/journey.out"; then pass "install-to-accept clean room"; else fail "install-to-accept clean room"; tail -30 "$WORK/journey.out" >&2; fi

cat > "$WORK/invalid-plan.json" <<'PLAN'
{
  "api_version": "taskspec.dev/v1",
  "kind": "TaskPlan",
  "approved": true,
    "metadata": {"name": "invalid-structure"},
    "api_key": "must-not-pass",
  "units": [{
    "id": "T-20260811-invalid-structure",
    "title": "Reject malformed plan values",
    "effort": "XS",
    "profile": "lite",
    "agent": "any",
    "execution_backend": "any",
    "depends_on": ["T-20260811-missing-unit"],
    "touches_paths": [{"not": "a path"}],
    "creates_paths": [],
    "source_note": "contract test",
    "why": "Invalid manifests must fail closed without a traceback.",
    "goal": "Reject this manifest.",
    "evals": [{"id": "eval_1", "description": "never generated", "command": "false"}]
  }]
}
PLAN
set +e
invalid_out=$("$TS" plan --manifest "$WORK/invalid-plan.json" 2>&1)
invalid_rc=$?
set -e
if [[ $invalid_rc -eq 1 ]] && echo "$invalid_out" | grep -q 'dependency .* is not declared' \
  && echo "$invalid_out" | grep -q 'credential-bearing keys are forbidden' \
  && ! echo "$invalid_out" | grep -q 'Traceback'; then
  pass "malformed and dangling TaskPlan fails closed"
else
  fail "malformed TaskPlan contract"
fi

echo "== dry-run and color =="
DRY="$WORK/dry"
mkdir -p "$DRY"
git -C "$DRY" init -q
(cd "$DRY" && "$TS" --dry-run init > "$WORK/dry.out")
if [[ ! -e "$DRY/tasks" ]] && grep -q 'INIT=DRY_RUN' "$WORK/dry.out"; then pass "dry-run prevents init"; else fail "dry-run prevents init"; fi
if NO_COLOR=1 TASKSPEC_COLOR=1 "$TS" gate --help | LC_ALL=C grep -q $'\033'; then fail "NO_COLOR precedence"; else pass "NO_COLOR precedence"; fi

echo "== research evidence =="
for provider in firecrawl tavily exa; do
  evidence="$WORK/$provider.json"
  "$ROOT/integrations/research/$provider/fake-adapter.sh" "atomic task" > "$evidence"
  check "$provider evidence" python3 "$ROOT/integrations/research/validate-evidence.py" "$evidence"
done
failure="$WORK/failure.json"
"$ROOT/integrations/research/tavily/fake-adapter.sh" --state rate_limited "atomic task" > "$failure"
check "named provider failure" python3 "$ROOT/integrations/research/validate-evidence.py" "$failure"
python3 - "$failure" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path))
data["usage"]["api_key"] = "must-not-pass"
json.dump(data, open(path, "w"))
PY
if python3 "$ROOT/integrations/research/validate-evidence.py" "$failure" >/dev/null 2>&1; then
  fail "evidence rejects credential-bearing keys"
else
  pass "evidence rejects credential-bearing keys"
fi
check "composition example preview" "$TS" plan --manifest "$ROOT/docs/examples/composition-plan.yaml"
check "checked-in evidence example" python3 "$ROOT/integrations/research/validate-evidence.py" "$ROOT/docs/examples/authoring-evidence.json"
check "checked-in handoff example" python3 -m json.tool "$ROOT/docs/examples/task-handoff.json"
check "README release status is generated from evidence" python3 "$ROOT/tools/render-status.py" --check "$ROOT/README.md"

echo "== package =="
if command -v npm >/dev/null 2>&1 && (cd "$ROOT" && npm pack --dry-run --json > "$WORK/npm-pack.json") \
  && python3 -c 'import json; d=json.load(open("'"$WORK/npm-pack.json"'")); assert d[0]["name"] == "@luanmorenommaciel/task-spec"'; then
  pass "npm pack dry run"
else
  fail "npm pack dry run"
fi
NPM_TARGET="$WORK/npm-project"
NPM_INSTALL_ROOT="$WORK/npm-install-root"
mkdir -p "$NPM_TARGET" "$NPM_INSTALL_ROOT"
if command -v npm >/dev/null 2>&1 \
  && npm install --global --prefix "$WORK/npm-prefix" "$ROOT" >/dev/null 2>&1 \
  && [[ "$("$WORK/npm-prefix/bin/taskspec" version)" == "3.6.0" ]] \
  && [[ -x "$WORK/npm-prefix/bin/taskspec-install" ]] \
  && TASKSPEC_INSTALL_ROOT="$NPM_INSTALL_ROOT" "$WORK/npm-prefix/bin/taskspec-install" --target "$NPM_TARGET" --no-bin >"$WORK/npm-install.out" 2>&1 \
  && grep -q '^INSTALL=OK$' "$WORK/npm-install.out" \
  && [[ -f "$NPM_TARGET/.claude/agents/task-architect.md" ]]; then
  pass "local npm package install"
else
  fail "local npm package install"
fi

echo
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
