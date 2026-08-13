#!/usr/bin/env bash
# Adversarial TaskAuthorization/v3, TaskHandoff/v3, receipt, Git, graph, and crash recovery suite.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; TS="$ROOT/bin/taskspec"; FIXTURE="$ROOT/tests/fixtures/T-20260603-stamp-then-verify.md"
WORK="$(mktemp -d -t taskspec-hardening-XXXXXX)"; ART="$(mktemp -d -t taskspec-hardening-artifacts-XXXXXX)"; trap 'rm -rf "$WORK" "$ART"' EXIT
PASS=0
ok(){ PASS=$((PASS+1)); echo "ok $PASS - $1"; }
must(){ local label="$1"; shift; if "$@" >/dev/null 2>&1; then ok "$label"; else echo "not ok - $label" >&2; "$@" >&2 || true; exit 1; fi; }
must_fail(){ local label="$1" pattern="$2"; shift 2; local output rc; set +e; output=$("$@" 2>&1); rc=$?; set -e; if [[ $rc -ne 0 && "$output" == *"$pattern"* ]]; then ok "$label"; else echo "not ok - $label (rc=$rc)" >&2; echo "$output" >&2; exit 1; fi; }
repo(){ local path="$1"; mkdir -p "$path/tasks"; git -C "$path" init -q; git -C "$path" config user.email hardening@example.invalid; git -C "$path" config user.name hardening; printf '# readme\n' > "$path/README.md"; git -C "$path" add README.md; git -C "$path" commit -qm baseline; }
spec(){ local path="$1" id="$2" format="${3:-3}"; python3 - "$FIXTURE" "$path/tasks/$id.md" "$id" "$format" <<'PY'
import pathlib,sys
text=pathlib.Path(sys.argv[1]).read_text()
text=text.replace("T-20260603-stamp-then-verify",sys.argv[3]).replace("format_version: 2",f"format_version: {sys.argv[4]}\nprofile: lite")
text=text.replace('(none — see references/concepts/signed-off.md "The three tiers")','(none)')
if sys.argv[4]=="4":
    policy="""evaluation_policy:\n  acceptance_scope: local\n  deterministic:\n    required: true\n  holdout:\n    required: true\n    authorization_ref: auth:holdout\n    descriptor_digest: sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\nenvironment_contract:\n  required: false\n"""
    text=text.replace("\n---\n","\n"+policy+"---\n",1)
pathlib.Path(sys.argv[2]).write_text(text)
PY
}
gate(){ (cd "$1" && TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR=tasks "$TS" gate --stamp "tasks/$2.md" >/dev/null); }
handoff(){ (cd "$1" && TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR=tasks "$TS" handoff "tasks/$2.md" --backend codex --attempt-id "$3" --out "$4" >/dev/null); }

# Canonical YAML and complete authority manifest.
R="$WORK/auth"; repo "$R"; spec "$R" T-20260813-authority 4; gate "$R" T-20260813-authority
cp "$R/tasks/T-20260813-authority.md" "$ART/authorized.md"
python3 - "$R/tasks/T-20260813-authority.md" <<'PY'
import pathlib
p=pathlib.Path(__import__('sys').argv[1]); p.write_text(p.read_text().replace("format_version: 4","format_version: 3"))
PY
must_fail "post-seal v4 to v3 downgrade fails closed" "HMAC mismatch" env TASKSPEC_SIGNING_KEY=hardening-key bash "$ROOT/src/gate/validate-task-spec.sh" --no-state "$R/tasks/T-20260813-authority.md"
cp "$ART/authorized.md" "$R/tasks/T-20260813-authority.md"
python3 - "$R/tasks/T-20260813-authority.md" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); lines=p.read_text().splitlines(True); out=[]; dropping=False
for line in lines:
    if line.startswith("evaluation_policy:"): dropping=True; continue
    if dropping and (line.startswith(" ") or not line.strip()): continue
    dropping=False; out.append(line)
p.write_text("".join(out))
PY
must_fail "sealed proof policy deletion fails closed" "HMAC mismatch" env TASKSPEC_SIGNING_KEY=hardening-key bash "$ROOT/src/gate/validate-task-spec.sh" --no-state "$R/tasks/T-20260813-authority.md"
cp "$ART/authorized.md" "$R/tasks/T-20260813-authority.md"
python3 - "$R/tasks/T-20260813-authority.md" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); lines=p.read_text().splitlines(True); out=[]; dropping=False
for line in lines:
    if line.startswith("environment_contract:"): dropping=True; continue
    if dropping and (line.startswith(" ") or not line.strip()): continue
    dropping=False; out.append(line)
p.write_text("".join(out))
PY
must_fail "sealed environment policy deletion fails closed" "HMAC mismatch" env TASKSPEC_SIGNING_KEY=hardening-key bash "$ROOT/src/gate/validate-task-spec.sh" --no-state "$R/tasks/T-20260813-authority.md"
cp "$ART/authorized.md" "$R/tasks/T-20260813-authority.md"
python3 "$ROOT/src/lib/update_frontmatter.py" "$R/tasks/T-20260813-authority.md" --set-json '{"children":["T-20260813-injected-child"]}'
must_fail "parent-child authority mutation fails closed" "HMAC mismatch" env TASKSPEC_SIGNING_KEY=hardening-key bash "$ROOT/src/gate/validate-task-spec.sh" --no-state "$R/tasks/T-20260813-authority.md"
cp "$ART/authorized.md" "$R/tasks/T-20260813-authority.md"
python3 "$ROOT/src/lib/update_frontmatter.py" "$R/tasks/T-20260813-authority.md" --set-json '{"future_authority":"expanded"}'
must_fail "unknown future authority is sealed by default" "HMAC mismatch" env TASKSPEC_SIGNING_KEY=hardening-key bash "$ROOT/src/gate/validate-task-spec.sh" --no-state "$R/tasks/T-20260813-authority.md"
cp "$ART/authorized.md" "$R/tasks/T-20260813-authority.md"
python3 "$ROOT/src/lib/update_frontmatter.py" "$R/tasks/T-20260813-authority.md" --set-json '{"status":"in-progress","tracker_ref":"linear:ABC-1"}'
must "lifecycle and tracker projection remain mutable" env TASKSPEC_SIGNING_KEY=hardening-key bash "$ROOT/src/gate/validate-task-spec.sh" --no-state "$R/tasks/T-20260813-authority.md"
cp "$ART/authorized.md" "$R/tasks/T-20260813-duplicate.md"; python3 - "$R/tasks/T-20260813-duplicate.md" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); p.write_text(p.read_text().replace("title:","id: T-duplicate\ntitle:",1))
PY
must_fail "duplicate YAML keys are rejected" "duplicate key" python3 "$ROOT/src/security/task_revision.py" "$R/tasks/T-20260813-duplicate.md"
cp "$ART/authorized.md" "$R/tasks/T-20260813-ambiguous.md"; python3 - "$R/tasks/T-20260813-ambiguous.md" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); p.write_text(p.read_text().replace("title:", 'future_numeric: {"value":NaN}\ntitle:',1))
PY
must_fail "ambiguous JSON numeric constants are rejected" "ambiguous JSON numeric constant" python3 "$ROOT/src/security/task_revision.py" "$R/tasks/T-20260813-ambiguous.md"
cp "$ART/authorized.md" "$R/tasks/T-20260813-reordered.md"; before=$(python3 "$ROOT/src/security/task_revision.py" "$R/tasks/T-20260813-reordered.md" --field task_revision_digest)
python3 - "$R/tasks/T-20260813-reordered.md" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); text=p.read_text(); a="title: Stamp-then-verify — proves the HMAC payload boundary (Tier 1)\n"; b="status: ready\n"; text=text.replace(a+b,b+a); p.write_text(text)
PY
after=$(python3 "$ROOT/src/security/task_revision.py" "$R/tasks/T-20260813-reordered.md" --field task_revision_digest)
must "authority mapping key order is canonical" test "$before" = "$after"
spec "$R" T-20260813-evidence-warning 4
python3 - "$R/tasks/T-20260813-evidence-warning.md" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); p.write_text(p.read_text().replace("eval_1() {", "# acceptance must read .taskspec/evidence/research.json\neval_1() {", 1))
PY
must "textual authoring-evidence acceptance use produces a lint warning" bash -c "bash '$ROOT/src/gate/validate-task-spec.sh' --no-state '$R/tasks/T-20260813-evidence-warning.md' | grep -q 'cannot satisfy acceptance'"

# Attempt-bound receipts, ordering, replay, and supervised compatibility.
R="$WORK/receipts"; repo "$R"; spec "$R" T-20260813-receipts 4; gate "$R" T-20260813-receipts
H1="$ART/handoff-a.json"; H2="$ART/handoff-b.json"; RECEIPT="$ART/holdout-a.json"
handoff "$R" T-20260813-receipts 11111111-1111-4111-8111-111111111111 "$H1"
handoff "$R" T-20260813-receipts 22222222-2222-4222-8222-222222222222 "$H2"
"$TS" receipt evaluation --handoff "$H1" --check-type holdout --evaluator hardening --result pass --descriptor-digest sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --out "$RECEIPT" >/dev/null
must_fail "receipt replay across attempts fails" "RECEIPT_SUBJECT_MISMATCH" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --handoff "$H2" --holdout-receipt "$RECEIPT" "$R/tasks/T-20260813-receipts.md"
must "global JSON returns typed receipt replay failure" bash -c "set +e; out=\$(TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR='$R/tasks' '$TS' --json accept --handoff '$H2' --holdout-receipt '$RECEIPT' '$R/tasks/T-20260813-receipts.md'); rc=\$?; set -e; test \$rc -eq 1 && printf '%s' \"\$out\" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d[\"data\"]=={\"contract\":\"AcceptanceFailure/v1\",\"accepted\":False,\"code\":\"RECEIPT_SUBJECT_MISMATCH\"}'"
python3 - "$RECEIPT" "$ART/holdout-stale.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); d["observed_at"]="2000-01-01T00:00:00Z"; json.dump(d,open(sys.argv[2],"w"))
PY
must_fail "pre-authorization receipt timestamp fails" "RECEIPT_STALE" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --handoff "$H1" --holdout-receipt "$ART/holdout-stale.json" "$R/tasks/T-20260813-receipts.md"
for field in task_id task_revision_digest base_commit; do
  python3 - "$RECEIPT" "$ART/holdout-wrong-$field.json" "$field" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); field=sys.argv[3]
d["subject"][field] = "T-20260813-wrong" if field == "task_id" else ("sha256:" + "f"*64 if field == "task_revision_digest" else "f"*40)
json.dump(d,open(sys.argv[2],"w"))
PY
  must_fail "receipt wrong $field fails" "RECEIPT_SUBJECT_MISMATCH" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --handoff "$H1" --holdout-receipt "$ART/holdout-wrong-$field.json" "$R/tasks/T-20260813-receipts.md"
done
AUTH=$(grep '^signed_off_sig:' "$R/tasks/T-20260813-receipts.md" | sed 's/^signed_off_sig: //')
cat > "$ART/holdout-v1.json" <<EOF
{"contract":"EvaluationReceipt/v1","task_id":"T-20260813-receipts","check_type":"holdout","authorization_ref":"auth:holdout","descriptor_digest":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","evaluator":"legacy","evaluated_at":"2030-01-01T00:00:00Z","result":"pass","evidence":[]}
EOF
must_fail "legacy structural receipt cannot silently produce Tier 1" "TIER_TOO_LOW" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --handoff "$H1" --holdout-receipt "$ART/holdout-v1.json" "$R/tasks/T-20260813-receipts.md"
sed 's/auth:holdout/structural:T-20260813-receipts/' "$ART/holdout-v1.json" > "$ART/holdout-structural.json"
must_fail "required receipt rejects structural authorization fallback" "RECEIPT_SUBJECT_MISMATCH" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --handoff "$H1" --holdout-receipt "$ART/holdout-structural.json" "$R/tasks/T-20260813-receipts.md"
must "matching v2 receipt accepts Tier 1" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --stamp --handoff "$H1" --holdout-receipt "$RECEIPT" "$R/tasks/T-20260813-receipts.md"

# Git history and filesystem containment.
R="$WORK/committed"; repo "$R"; spec "$R" T-20260813-committed 3; gate "$R" T-20260813-committed; H="$ART/committed.json"; handoff "$R" T-20260813-committed 33333333-3333-4333-8333-333333333333 "$H"
printf 'outside\n' > "$R/outside.txt"; git -C "$R" add tasks outside.txt; git -C "$R" commit -qm executor-commit
must_fail "committed out-of-scope change is rejected" "outside.txt" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --handoff "$H" "$R/tasks/T-20260813-committed.md"

R="$WORK/symlink"; repo "$R"; ln -s "$ART" "$R/escape"; spec "$R" T-20260813-symlink 3
python3 - "$R/tasks/T-20260813-symlink.md" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); p.write_text(p.read_text().replace("touches_paths:\n  - README.md","touches_paths:\n  - README.md\ncreates_paths: [escape/result.txt]"))
PY
gate "$R" T-20260813-symlink; H="$ART/symlink.json"; handoff "$R" T-20260813-symlink 44444444-4444-4444-8444-444444444444 "$H"
must_fail "symlink-escaped creation scope is rejected" "symlink" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --handoff "$H" "$R/tasks/T-20260813-symlink.md"

R="$WORK/handoff-tamper"; repo "$R"; spec "$R" T-20260813-handoff-tamper 3; gate "$R" T-20260813-handoff-tamper; H="$ART/handoff-valid.json"; handoff "$R" T-20260813-handoff-tamper 88888888-8888-4888-8888-888888888888 "$H"
python3 - "$H" "$ART/handoff-absolute.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); d["write_scope"]["creates_paths"]=["/tmp/escape"]; json.dump(d,open(sys.argv[2],"w"))
PY
must_fail "absolute handoff scope fails closed" "HANDOFF_STALE" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --handoff "$ART/handoff-absolute.json" "$R/tasks/T-20260813-handoff-tamper.md"
python3 - "$H" "$ART/handoff-traversal.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); d["write_scope"]["creates_paths"]=["../escape"]; json.dump(d,open(sys.argv[2],"w"))
PY
must_fail "traversal handoff scope fails closed" "HANDOFF_STALE" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --handoff "$ART/handoff-traversal.json" "$R/tasks/T-20260813-handoff-tamper.md"
python3 - "$H" "$ART/handoff-budget.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); d["budgets"]["iterations"]=999; json.dump(d,open(sys.argv[2],"w"))
PY
must_fail "handoff budget expansion fails closed" "HANDOFF_STALE" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --handoff "$ART/handoff-budget.json" "$R/tasks/T-20260813-handoff-tamper.md"
python3 - "$H" "$ART/handoff-attempt.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); d["attempt"]["id"]="../../escape"; json.dump(d,open(sys.argv[2],"w"))
PY
must_fail "non-UUID attempt cannot escape acceptance storage" "HANDOFF_STALE" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --handoff "$ART/handoff-attempt.json" "$R/tasks/T-20260813-handoff-tamper.md"

R="$WORK/active-conflict"; repo "$R"; spec "$R" T-20260813-conflicted 3; spec "$R" T-20260813-running 3
python3 "$ROOT/src/lib/update_frontmatter.py" "$R/tasks/T-20260813-running.md" --set-json '{"status":"in-progress"}'
gate "$R" T-20260813-conflicted
must_fail "handoff rejects conflict with an in-progress task" "in-progress task" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" handoff "$R/tasks/T-20260813-conflicted.md" --backend codex
python3 "$ROOT/src/lib/update_frontmatter.py" "$R/tasks/T-20260813-running.md" --set-json '{"status":"parked"}'
H="$ART/active-conflict.json"; handoff "$R" T-20260813-conflicted aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa "$H"
python3 "$ROOT/src/lib/update_frontmatter.py" "$R/tasks/T-20260813-running.md" --set-json '{"status":"in-progress"}'
must_fail "acceptance rechecks active write conflicts" "GRAPH_INVALID" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --handoff "$H" "$R/tasks/T-20260813-conflicted.md"

R="$WORK/status-crash"; repo "$R"; spec "$R" T-20260813-status-crash 3
must_fail "interrupted status mutation leaves the old complete frontmatter" "injected crash" env TASKSPEC_TEST_CRASH_BEFORE_FRONTMATTER_REPLACE=1 TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" transition T-20260813-status-crash in-progress
must "interrupted status mutation leaves no partial state or temporary" bash -c "grep -q '^status: ready$' '$R/tasks/T-20260813-status-crash.md' && ! find '$R/tasks' -name '.*.tmp.*' | grep -q ."

R="$WORK/diverged"; repo "$R"; spec "$R" T-20260813-diverged 3; gate "$R" T-20260813-diverged; H="$ART/diverged.json"; handoff "$R" T-20260813-diverged 55555555-5555-4555-8555-555555555555 "$H"
printf '# rewritten history\n' > "$R/README.md"; git -C "$R" add README.md; git -C "$R" commit --amend -qm rewritten
must_fail "base commit divergence requires a new handoff" "BASE_DIVERGED" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --handoff "$H" "$R/tasks/T-20260813-diverged.md"

# Dependency closure and crash-fault atomicity.
R="$WORK/closure"; repo "$R"; spec "$R" T-20260813-dependency 3; spec "$R" T-20260813-leaf 3
python3 "$ROOT/src/lib/update_frontmatter.py" "$R/tasks/T-20260813-dependency.md" --set-json '{"status":"done"}'
python3 - "$R/tasks/T-20260813-leaf.md" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); p.write_text(p.read_text().replace("depends_on: []","depends_on: [T-20260813-dependency]"))
PY
git -C "$R" add tasks; git -C "$R" commit -qm graph; gate "$R" T-20260813-leaf; H="$ART/closure.json"; handoff "$R" T-20260813-leaf 66666666-6666-4666-8666-666666666666 "$H"
printf '\nclosure drift\n' >> "$R/tasks/T-20260813-dependency.md"
must_fail "dependency-closure drift fails closed" "CLOSURE_DRIFT" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --handoff "$H" "$R/tasks/T-20260813-leaf.md"

R="$WORK/crash"; repo "$R"; spec "$R" T-20260813-crash 3; gate "$R" T-20260813-crash; H="$ART/crash.json"; handoff "$R" T-20260813-crash 77777777-7777-4777-8777-777777777777 "$H"
must_fail "injected finalize crash leaves old complete task state" "injected crash" env TASKSPEC_TEST_CRASH_AFTER_RECORD=1 TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --stamp --handoff "$H" "$R/tasks/T-20260813-crash.md"
must "crash did not partially stamp accepted state" bash -c "! grep -q '^accepted: true' '$R/tasks/T-20260813-crash.md' && ! grep -q '^accepted_attempt_id:' '$R/tasks/T-20260813-crash.md'"
must "doctor reports the orphan record left by interrupted acceptance" bash -c "cd '$R' && '$TS' doctor --backlog | grep -q ORPHAN_ACCEPTANCE_RECORD"
must "same attempt recovers despite metrics projection failure" env TASKSPEC_TEST_FAIL_METRICS=1 TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --stamp --handoff "$H" "$R/tasks/T-20260813-crash.md"
must "doctor reports the missing accepted metrics projection" bash -c "cd '$R' && '$TS' doctor --backlog | grep -q METRICS_PROJECTION_MISSING"
must_fail "same attempt cannot change its acceptor" "AcceptanceRecord conflicts" env TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" accept --stamp --accepted-by different-operator --handoff "$H" "$R/tasks/T-20260813-crash.md"
must "conflicting retry leaves record and task envelope consistent" bash -c "TASKSPEC_BACKLOG_DIR='$R/tasks' python3 '$ROOT/src/accept/record.py' '$R/tasks/T-20260813-crash.md' --backlog '$R/tasks'"
must "same accepted attempt can be retried without duplicate metrics" bash -c "TASKSPEC_SIGNING_KEY=hardening-key TASKSPEC_BACKLOG_DIR='$R/tasks' '$TS' accept --stamp --handoff '$H' '$R/tasks/T-20260813-crash.md' >/dev/null && test \"\$(grep -c '\"event\":\"accepted\"' '$R/tasks/_metrics.jsonl')\" = 1"
must "TaskStatus names rebuild-state as the one safe projection recovery" bash -c "cd '$R' && TASKSPEC_SIGNING_KEY=hardening-key '$TS' status T-20260813-crash --json | python3 -c 'import json,sys; d=json.load(sys.stdin)[\"data\"]; assert d[\"contract\"]==\"TaskStatus/v1\" and d[\"authorization\"][\"tier\"]==1 and d[\"authorization\"][\"verification\"]==\"verified\" and d[\"acceptance\"][\"accepted\"] and d[\"graph\"][\"stale\"] and d[\"next_command\"]==\"taskspec rebuild-state\"'"
must "rebuilding projection advances the one safe next command" bash -c "cd '$R' && '$TS' rebuild-state >/dev/null && TASKSPEC_SIGNING_KEY=hardening-key '$TS' status T-20260813-crash --json | python3 -c 'import json,sys; d=json.load(sys.stdin)[\"data\"]; assert not d[\"graph\"][\"stale\"] and d[\"next_command\"].endswith(\" done\")'"
must "global JSON preserves the same typed TaskStatus" bash -c "cd '$R' && TASKSPEC_SIGNING_KEY=hardening-key '$TS' --json status T-20260813-crash | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d[\"ok\"] and d[\"data\"][\"contract\"]==\"TaskStatus/v1\" and d[\"data\"][\"task_id\"]==\"T-20260813-crash\"'"
RECORD="$R/.taskspec/acceptance/T-20260813-crash/77777777-7777-4777-8777-777777777777.json"
python3 - "$RECORD" <<'PY'
import json,sys
value=json.load(open(sys.argv[1])); value["accepted_by"]="tampered-acceptor"
json.dump(value,open(sys.argv[1],"w"),sort_keys=True)
PY
must_fail "transition to done verifies the record subject and envelope" "acceptance record does not match" env TASKSPEC_BACKLOG_DIR="$R/tasks" "$TS" transition T-20260813-crash done
must "status exposes semantic acceptance-record mismatch" bash -c "cd '$R' && TASKSPEC_SIGNING_KEY=hardening-key '$TS' status T-20260813-crash --json | python3 -c 'import json,sys; d=json.load(sys.stdin)[\"data\"]; assert not d[\"acceptance\"][\"record_matches\"] and d[\"acceptance\"][\"record_error\"]'"
must_fail "backlog doctor fails on semantic acceptance-record mismatch" "ACCEPTANCE_RECORD_MISMATCH" bash -c "cd '$R' && '$TS' doctor --backlog"

echo "PASS: Task-Spec hardening adversarial suite ($PASS checks)"
