#!/usr/bin/env bash
# Clean-room 3.6 journey plus CLI, installer, provider, and packaging contracts.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CURRENT_VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
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
  && grep -q '^INSTALL=OK$' "$WORK/install.out" \
  && grep -q '^Verify: taskspec doctor$' "$WORK/install.out" \
  && grep -q '^Prove:  taskspec demo$' "$WORK/install.out"; then pass "copy install"; else fail "copy install"; fi
if TASKSPEC_INSTALL_ROOT="$INSTALL_ROOT" bash "$ROOT/install.sh" --target "$TARGET" --copy --bin-dir "$BIN_DIR" >"$WORK/reinstall.out" 2>&1 \
  && grep -q '^INSTALL=OK$' "$WORK/reinstall.out"; then pass "idempotent install"; else fail "idempotent install"; fi
if [[ "$(shasum -a 256 "$TARGET/.agents/skills/task-spec/SKILL.md" | awk '{print $1}')" == "$(shasum -a 256 "$TARGET/.claude/skills/task-spec/SKILL.md" | awk '{print $1}')" \
   && "$(shasum -a 256 "$TARGET/.agents/skills/task-spec/SKILL.md" | awk '{print $1}')" == "$(shasum -a 256 "$TARGET/.grok/skills/task-spec/SKILL.md" | awk '{print $1}')" \
   && "$(shasum -a 256 "$TARGET/.agents/skills/task-spec/SKILL.md" | awk '{print $1}')" == "$(shasum -a 256 "$TARGET/.cursor/skills/task-spec/SKILL.md" | awk '{print $1}')" ]]; then pass "equivalent harness skills"; else fail "equivalent harness skills"; fi

GLOBAL_HOME="$WORK/global-home"
GLOBAL_ROOT="$WORK/global-root"
mkdir -p "$GLOBAL_HOME" "$GLOBAL_ROOT"
if HOME="$GLOBAL_HOME" TASKSPEC_INSTALL_ROOT="$GLOBAL_ROOT" bash "$ROOT/install.sh" --global --copy >"$WORK/global.out" 2>&1 \
  && grep -q '^INSTALL=OK$' "$WORK/global.out" \
  && [[ -f "$GLOBAL_HOME/.agents/skills/task-spec/SKILL.md" ]] \
  && [[ -f "$GLOBAL_HOME/.claude/skills/task-spec/SKILL.md" ]] \
  && [[ -f "$GLOBAL_HOME/.grok/skills/task-spec/SKILL.md" ]] \
  && [[ -f "$GLOBAL_HOME/.cursor/skills/task-spec/SKILL.md" ]] \
  && [[ -f "$GLOBAL_HOME/.claude/agents/task-architect.md" ]] \
  && [[ "$("$GLOBAL_HOME/.local/bin/taskspec" version)" == "$CURRENT_VERSION" ]] \
  && cmp -s "$GLOBAL_HOME/.agents/skills/task-spec/SKILL.md" "$GLOBAL_HOME/.claude/skills/task-spec/SKILL.md" \
  && cmp -s "$GLOBAL_HOME/.agents/skills/task-spec/SKILL.md" "$GLOBAL_HOME/.grok/skills/task-spec/SKILL.md" \
  && cmp -s "$GLOBAL_HOME/.agents/skills/task-spec/SKILL.md" "$GLOBAL_HOME/.cursor/skills/task-spec/SKILL.md"; then
  pass "global user install"
else
  fail "global user install"
fi

SYMLINK_TARGET="$WORK/symlink-project"
SYMLINK_ROOT="$WORK/symlink-root"
SYMLINK_BIN="$WORK/symlink-bin"
mkdir -p "$SYMLINK_TARGET" "$SYMLINK_ROOT" "$SYMLINK_BIN"
if TASKSPEC_INSTALL_ROOT="$SYMLINK_ROOT" bash "$ROOT/install.sh" --target "$SYMLINK_TARGET" --symlink --bin-dir "$SYMLINK_BIN" >"$WORK/symlink.out" 2>&1 \
  && [[ -L "$SYMLINK_TARGET/.agents/skills/task-spec" ]] \
  && [[ -L "$SYMLINK_TARGET/.claude/skills/task-spec" ]] \
  && [[ -L "$SYMLINK_TARGET/.grok/skills/task-spec" ]] \
  && [[ -L "$SYMLINK_TARGET/.cursor/skills/task-spec" ]] \
  && [[ -L "$SYMLINK_TARGET/.claude/agents/task-architect.md" ]] \
  && [[ "$($SYMLINK_BIN/taskspec version)" == "$CURRENT_VERSION" ]]; then
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

UNMANAGED_TARGET="$WORK/unmanaged-project"
UNMANAGED_ROOT="$WORK/unmanaged-root"
UNMANAGED_BIN="$WORK/unmanaged-bin"
mkdir -p "$UNMANAGED_TARGET/.agents/skills/task-spec" "$UNMANAGED_ROOT" "$UNMANAGED_BIN"
printf 'user-owned\n' > "$UNMANAGED_TARGET/.agents/skills/task-spec/SKILL.md"
set +e
TASKSPEC_INSTALL_ROOT="$UNMANAGED_ROOT" bash "$ROOT/install.sh" --target "$UNMANAGED_TARGET" --copy --bin-dir "$UNMANAGED_BIN" >"$WORK/unmanaged.out" 2>&1
unmanaged_rc=$?
set -e
if [[ "$unmanaged_rc" -ne 0 ]] \
  && grep -q 'refusing to clobber' "$WORK/unmanaged.out" \
  && grep -qx 'user-owned' "$UNMANAGED_TARGET/.agents/skills/task-spec/SKILL.md"; then
  pass "unmanaged destination is preserved"
else
  fail "unmanaged destination protection"
fi

if TASKSPEC_INSTALL_ROOT="$UNMANAGED_ROOT" bash "$ROOT/install.sh" --target "$UNMANAGED_TARGET" --copy --bin-dir "$UNMANAGED_BIN" --force >"$WORK/forced.out" 2>&1 \
  && find "$UNMANAGED_TARGET/.agents/skills" -maxdepth 1 -name 'task-spec.backup.*' -type d | grep -q . \
  && grep -q '^name: task-spec$' "$UNMANAGED_TARGET/.agents/skills/task-spec/SKILL.md"; then
  pass "forced replacement leaves a backup"
else
  fail "forced replacement backup"
fi

printf '%s\n' '#!/usr/bin/env sh' '# task-spec launcher v3.6.0' 'exit 91' > "$BIN_DIR/taskspec"
chmod +x "$BIN_DIR/taskspec"
if TASKSPEC_INSTALL_ROOT="$INSTALL_ROOT" bash "$ROOT/install.sh" --target "$TARGET" --copy --bin-dir "$BIN_DIR" >"$WORK/launcher-upgrade.out" 2>&1 \
  && grep -q '^updated: CLI launcher ' "$WORK/launcher-upgrade.out" \
  && [[ "$("$BIN_DIR/taskspec" version)" == "$CURRENT_VERSION" ]]; then
  pass "managed launcher upgrades safely"
else
  fail "managed launcher upgrade"
fi

TS="$BIN_DIR/taskspec"
check "installed version" bash -c "[[ \"\$('$TS' version)\" == '$CURRENT_VERSION' ]]"
check "installed isolated demo" bash -c "'$TS' demo | grep -q '^DEMO=READY$'"
check "agent context JSON" bash -c "'$TS' agent-context | python3 -m json.tool"
check "agent context covers the complete public command and schema surfaces" bash -c "'$TS' agent-context | python3 -c 'import json,sys; d=json.load(sys.stdin); commands=set(d[\"commands\"]); required=set(\"init setup demo new plan batch migrate validate dod gate handoff run accept author-doctor holdout receipt eval-audit identity evidence bridge dsse mcp mesh ready graph status lint transition rebuild-state archive backup metrics conformance executor agent-context completion doctor version help\".split()); assert required <= commands and d[\"default_format_version\"] == 3; assert len(d[\"contracts\"]) == 36 and {\"task_materialization_receipt\",\"acceptance_finalized\",\"taskmesh_api\",\"run_lease\"} <= set(d[\"contracts\"])'"
if grep -q 'TaskHandoff/v3' "$ROOT/harness/agents/task-architect.md" \
  && grep -q 'taskspec plan --manifest' "$ROOT/harness/codex/AGENTS.md" \
  && grep -q 'AcceptanceRecord/v1' "$ROOT/harness/codex/AGENTS.md" \
  && grep -q 'taskspec handoff' "$ROOT/harness/claude-code/SKILL.md" \
  && grep -q 'TaskHandoff/v3' "$ROOT/harness/claude-code/SKILL.md" \
  && ! grep -q '3.6 contract' "$ROOT/harness/agents/task-architect.md" \
  && ! grep -q 'Canonical Task-Spec 3.6' "$ROOT/.claude-plugin/marketplace.json"; then
  pass "agent guidance surfaces share the 3.9 lifecycle"
else
  fail "agent guidance lifecycle alignment"
fi
check "global JSON envelope" bash -c "'$TS' --json help | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d[\"ok\"] and d[\"command\"] == \"help\"'"
for command in init setup demo new plan batch migrate validate dod gate handoff run accept author-doctor holdout receipt dsse eval-audit identity evidence bridge mcp mesh ready graph status lint transition rebuild-state archive backup metrics conformance executor agent-context completion doctor version help; do
  check "per-command help $command" "$TS" help "$command"
done
for command in "status" "transition" "migrate" "executor" "run"; do
  check "usage exit 2: $command" bash -c "set +e; '$TS' $command >/dev/null 2>&1; rc=\$?; set -e; test \$rc -eq 2"
done
for shell_name in bash zsh fish; do check "completion $shell_name" bash -c "test -n \"\$('$TS' completion '$shell_name')\""; done

echo "== clean-room journey =="
git -C "$TARGET" init -q
git -C "$TARGET" config user.email test@taskspec.local
git -C "$TARGET" config user.name "Task-Spec test"
set +e
(
  cd "$TARGET"
  "$TS" init
  "$TS" setup
  "$TS" setup signing
  "$TS" setup signing
  "$TS" doctor
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
    required_tools: [git, bash, python3]
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
  "$TS" --json batch --dry-run --plan tasks/.plans/marker.yaml > "$WORK/materialization.json"
  python3 - "$WORK/materialization.json" <<'PY' || exit 1
import json, sys
value = json.load(open(sys.argv[1]))
assert value["contract"] == "TaskSpecCLIResult/v1"
assert value["ok"] is True
receipt = value["data"]
assert receipt["contract"] == "TaskMaterializationReceipt/v1"
assert receipt["input"]["contract"] == "TaskPlan/v1"
assert receipt["input"]["approved"] is True
assert receipt["dry_run"] is True
assert receipt["materialized"] is False
assert receipt["changed"] is False
assert receipt["state"] == "dry_run"
assert receipt["dispatch_authorized"] is False
assert receipt["tasks"][0]["task_id"] == "T-20260811-write-marker"
assert len(receipt["tasks"][0]["sha256"]) == 64
assert value["stdout"] == ""
PY
  "$TS" batch --plan tasks/.plans/marker.yaml
  "$TS" --json batch --plan tasks/.plans/marker.yaml > "$WORK/materialization-rerun.json"
  python3 - "$WORK/materialization-rerun.json" <<'PY' || exit 1
import json, sys
receipt = json.load(open(sys.argv[1]))["data"]
assert receipt["materialized"] is True
assert receipt["changed"] is False
assert receipt["state"] == "unchanged"
assert receipt["dispatch_authorized"] is False
PY
  cp tasks/T-20260811-write-marker.md "$WORK/marker-exact.md"
  printf '\nexecutor-owned change\n' >> tasks/T-20260811-write-marker.md
  if "$TS" batch --plan tasks/.plans/marker.yaml >"$WORK/materialization-conflict.out" 2>&1; then
    exit 1
  fi
  grep -q 'TASK_BATCH=REFUSED' "$WORK/materialization-conflict.out" || exit 1
  grep -q 'executor-owned change' tasks/T-20260811-write-marker.md || exit 1
  cp "$WORK/marker-exact.md" tasks/T-20260811-write-marker.md

  python3 - "$ROOT/src/lib" tasks/.plans/marker.yaml tasks/.plans/pair.json <<'PY' || exit 1
import copy, json, sys
sys.path.insert(0, sys.argv[1])
from taskspec_data import load_document

plan = load_document(sys.argv[2])
second = copy.deepcopy(plan["units"][0])
second.update({
    "id": "T-20260811-write-second-marker",
    "title": "Write the second accepted marker",
    "creates_paths": ["src/second-marker.txt"],
})
plan["units"].append(second)
with open(sys.argv[3], "w", encoding="utf-8") as stream:
    json.dump(plan, stream)
PY
  "$TS" batch --plan tasks/.plans/pair.json --out-dir pair-tasks >/dev/null
  rm pair-tasks/T-20260811-write-second-marker.md
  if "$TS" batch --plan tasks/.plans/pair.json --out-dir pair-tasks >"$WORK/materialization-partial.out" 2>&1; then
    exit 1
  fi
  grep -q 'partial existing task set' "$WORK/materialization-partial.out" || exit 1
  rm -r pair-tasks tasks/.plans/pair.json

  grep -Fq 'required_tools: [git, bash, python3]' tasks/T-20260811-write-marker.md || exit 1
  "$TS" author-doctor tasks/T-20260811-write-marker.md
  "$TS" validate tasks/T-20260811-write-marker.md
  "$TS" dod tasks/T-20260811-write-marker.md
  "$TS" ready --all
  "$TS" graph --check
  "$TS" gate --stamp tasks/T-20260811-write-marker.md
  git add .
  git commit -qm "sealed clean-room task"
  "$TS" status T-20260811-write-marker
  "$TS" doctor --backlog
  "$TS" handoff tasks/T-20260811-write-marker.md --backend codex --out "$WORK/handoff.json"
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["contract"] == "TaskHandoff/v3" and d["signoff_tier"] == 1 and d["attempt"]["id"]' "$WORK/handoff.json"
  printf 'done\n' > src/marker.txt
  "$TS" run tasks/T-20260811-write-marker.md
  "$TS" accept --stamp --gold-sanity --handoff "$WORK/handoff.json" tasks/T-20260811-write-marker.md
  "$TS" --json accept --stamp --gold-sanity --handoff "$WORK/handoff.json" tasks/T-20260811-write-marker.md > "$WORK/acceptance.json"
  python3 - "$WORK/acceptance.json" <<'PY'
import json, pathlib, sys
value = json.load(open(sys.argv[1]))
assert value["contract"] == "TaskSpecCLIResult/v1"
assert value["ok"] is True
result = value["data"]
assert result["contract"] == "AcceptanceFinalized/v1"
record = pathlib.Path(result["acceptance_record"])
assert record.is_file()
assert json.load(record.open())["contract"] == "AcceptanceRecord/v1"
assert result["acceptance_record_digest"].startswith("sha256:")
PY
  "$TS" transition T-20260811-write-marker done
  "$TS" validate tasks/done/T-20260811-write-marker.md
  "$TS" status T-20260811-write-marker
) >"$WORK/journey.out" 2>&1
journey_rc=$?
set -e
if [[ "$journey_rc" -eq 0 ]] && grep -q 'ACCEPTED=1' "$WORK/journey.out" && grep -q 'DOD=COMPLETE' "$WORK/journey.out"; then pass "install-to-accept clean room with structured materialization receipt"; else fail "install-to-accept clean room"; tail -30 "$WORK/journey.out" >&2; fi

README_NEW="$WORK/readme-new"
mkdir -p "$README_NEW"
git -C "$README_NEW" init -q
if (cd "$README_NEW" && "$TS" new add-search S codex >/dev/null && "$TS" new --format 4 benchmark-search S codex >/dev/null) \
  && grep -q '^format_version: 3$' "$README_NEW"/tasks/T-*-add-search.md \
  && grep -q '^format_version: 4$' "$README_NEW"/tasks/T-*-benchmark-search.md; then
  pass "README v3 and opt-in v4 scaffold commands"
else
  fail "README scaffold commands"
fi

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
  "$ROOT/harness/research/$provider/fake-adapter.sh" "atomic task" > "$evidence"
  check "$provider evidence" python3 "$ROOT/harness/research/validate-evidence.py" "$evidence"
done
failure="$WORK/failure.json"
"$ROOT/harness/research/tavily/fake-adapter.sh" --state rate_limited "atomic task" > "$failure"
check "named provider failure" python3 "$ROOT/harness/research/validate-evidence.py" "$failure"
python3 - "$failure" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path))
data["usage"]["api_key"] = "must-not-pass"
json.dump(data, open(path, "w"))
PY
if python3 "$ROOT/harness/research/validate-evidence.py" "$failure" >/dev/null 2>&1; then
  fail "evidence rejects credential-bearing keys"
else
  pass "evidence rejects credential-bearing keys"
fi
check "composition example preview" "$TS" plan --manifest "$ROOT/docs/examples/composition-plan.yaml"
check "checked-in evidence example" python3 "$ROOT/harness/research/validate-evidence.py" "$ROOT/docs/examples/authoring-evidence.json"
check "checked-in handoff example" python3 -m json.tool "$ROOT/docs/examples/task-handoff.json"
check "README release status is generated from evidence" python3 "$ROOT/tools/render-status.py" --check "$ROOT/README.md"

echo "== checksum-backed release archive =="
DIST="$WORK/dist"
python3 "$ROOT/tools/build-release-archive.py" --out-dir "$DIST" --include-worktree >"$WORK/archive.out"
REMOTE_TARGET="$WORK/remote-project"; REMOTE_ROOT="$WORK/remote-root"; REMOTE_BIN="$WORK/remote-bin"
mkdir -p "$REMOTE_TARGET" "$REMOTE_ROOT" "$REMOTE_BIN"
cp "$ROOT/install.sh" "$WORK/remote-install.sh"
if TASKSPEC_RELEASE_BASE_URL="file://$DIST" TASKSPEC_INSTALL_ROOT="$REMOTE_ROOT" \
  bash "$WORK/remote-install.sh" --target "$REMOTE_TARGET" --bin-dir "$REMOTE_BIN" >"$WORK/remote.out" 2>&1 \
  && grep -q '^verified: release archive sha256:' "$WORK/remote.out" \
  && grep -q '^INSTALL=OK$' "$WORK/remote.out"; then
  pass "checksum-backed remote install"
else
  fail "checksum-backed remote install"
fi
cp "$DIST/task-spec-$CURRENT_VERSION.tar.gz" "$WORK/tampered.tar.gz"
printf 'tamper' >> "$DIST/task-spec-$CURRENT_VERSION.tar.gz"
set +e
TASKSPEC_RELEASE_BASE_URL="file://$DIST" TASKSPEC_INSTALL_ROOT="$WORK/tampered-root" \
  bash "$WORK/remote-install.sh" --target "$REMOTE_TARGET" --no-bin >"$WORK/tampered.out" 2>&1
tampered_rc=$?
set -e
if [[ $tampered_rc -ne 0 ]] && grep -q 'checksum mismatch' "$WORK/tampered.out"; then
  pass "tampered release archive fails closed"
else
  fail "tampered release archive fails closed"
fi
mv "$WORK/tampered.tar.gz" "$DIST/task-spec-$CURRENT_VERSION.tar.gz"

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
  && [[ "$("$WORK/npm-prefix/bin/taskspec" version)" == "$CURRENT_VERSION" ]] \
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
if [[ "$FAIL" -eq 0 ]]; then
  echo "INSTALL=OK"
fi
[[ "$FAIL" -eq 0 ]]
