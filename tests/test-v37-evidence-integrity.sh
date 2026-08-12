#!/usr/bin/env bash
# Task-Spec 3.7: format-v4 evidence policy, receipts, identity, interop, and compatibility.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS="$ROOT/bin/taskspec"
WORK="$(mktemp -d -t taskspec-v37-XXXXXX)"
trap 'rm -rf "$WORK"' EXIT
PASS=0

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then PASS=$((PASS + 1)); echo "ok $PASS - $label"
  else echo "not ok - $label" >&2; "$@" >&2 || true; exit 1; fi
}

git -C "$WORK" init -q
git -C "$WORK" config user.email taskspec@example.invalid
git -C "$WORK" config user.name taskspec-test
mkdir -p "$WORK/tasks" "$WORK/evidence"
mkdir -p "$WORK/scaffold"
git -C "$WORK/scaffold" init -q
check "v4 authoring is explicit and non-default" bash -c "cd '$WORK/scaffold' && '$TS' new --format 4 scaffold-contract S codex >/dev/null && grep -q '^format_version: 4$' tasks/T-*-scaffold-contract.md && grep -q '^evaluation_policy:$' tasks/T-*-scaffold-contract.md"

cat > "$WORK/evidence/holdout.json" <<'JSON'
{
  "contract": "HoldoutBundle/v1",
  "task_id": "T-20260812-evidence-loop",
  "checks": [{"id": "holdout_proof", "argv": ["bash", "-lc", "grep -qx portable proof.txt"], "verifies": ["B-1"], "timeout_sec": 10}]
}
JSON
BUNDLE_DIGEST="sha256:$(python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$WORK/evidence/holdout.json")"

cat > "$WORK/evidence/environment.json" <<'JSON'
{"contract":"EnvironmentContract/v1","runtime":{"name":"bash","version":"3.2+"},"network":{"mode":"deny"},"filesystem":{"workspace":".","writes":["proof.txt"]}}
JSON
ENV_DIGEST="sha256:$(python3 - "$WORK/evidence/environment.json" "$ROOT/src/lib" <<'PY'
import json,sys
sys.path.insert(0,sys.argv[2])
from taskspec_data import canonical_digest
print(canonical_digest(json.load(open(sys.argv[1]))))
PY
)"

"$TS" identity init --out-dir "$WORK/evidence/identity" >/dev/null
KEY_ID="$(openssl pkey -pubin -in "$WORK/evidence/identity/identity.ed25519.pub.pem" -outform DER | openssl dgst -sha256 | awk '{print substr($2,1,16)}')"
RUBRIC="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

cat > "$WORK/tasks/T-20260812-evidence-loop.md" <<EOF
---
id: T-20260812-evidence-loop
title: Prove the portable evidence loop
status: ready
format_version: 4
profile: standard
effort: XS
budget_iterations: 2
agent: any
parent: (none)
depends_on: []
touches_paths: []
creates_paths: [proof.txt]
source_note: v3.7 evidence test
created: 2026-08-12T12:00:00Z
tags: [evidence]
owner: test
priority: P1
severity: feature
execution_backend: any
signed_off: false
signed_off_by: (none)
signed_off_at: (none)
accepted: false
accepted_by: (none)
accepted_at: (none)
baseline_ref: HEAD
evaluation_policy:
  acceptance_scope: portable
  deterministic:
    required: true
  holdout:
    required: true
    authorization_ref: $BUNDLE_DIGEST
  graded:
    required: true
    rubric_digest: $RUBRIC
    threshold: 0.8
  human:
    required: true
    owner: release-owner
environment_contract:
  required: true
  ref: evidence/environment.json
  digest: $ENV_DIGEST
identity_policy:
  required: true
  key_id: $KEY_ID
---

# Prove the portable evidence loop

> **Why:** A v4 task must fail closed unless every policy-bound receipt matches.

## Goal

Produce a proof file whose exact content is independently evaluated and accepted.

## Context

This disposable repository exercises Task-Spec 3.7 without external providers.

## Behavior

- **B-1** — GIVEN no proof WHEN the task runs THEN proof.txt contains portable

## Success Criteria

\`\`\`bash
eval_1() {
  grep -qx portable proof.txt
}
\`\`\`

## Validation Card

\`\`\`yaml
success_criteria:
  - id: eval_1
    description: The exact portable proof exists
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 1
retry_policy:
  max_iterations: 2
  circuit_breaker_no_progress: 1
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails, operations]
  produce: [docs]
  required_tools: [git, bash]
  timeout_minutes: 2
  sandbox_type: isolated
  output_artifacts: []
  mcp_dependencies: []
  emit: [pass, fail, parked_with_context]
\`\`\`

## Exit Check

\`\`\`bash
eval_1
\`\`\`

## Rollback Plan

Remove proof.txt.

## Observability Hooks

The deterministic and holdout receipt results are the observable signals.

## Anti-Patterns

- Do not let the executor choose its own acceptance policy.

## Do-Not-Touch

- evidence/identity/identity.ed25519.pem

## Open Questions

(none)
EOF

git -C "$WORK" add tasks evidence/holdout.json evidence/environment.json
git -C "$WORK" commit -qm baseline

check "v3 compatibility fixture remains valid" bash "$ROOT/src/gate/validate-task-spec.sh" --no-state --skip-id-filename "$ROOT/tests/fixtures/T-20260602-golden.md"
check "v4 policy validates" bash "$ROOT/src/gate/validate-task-spec.sh" --no-state "$WORK/tasks/T-20260812-evidence-loop.md"
check "author doctor finds no blockers" "$TS" author-doctor "$WORK/tasks/T-20260812-evidence-loop.md"

(cd "$WORK" && "$TS" setup signing >/dev/null)
(cd "$WORK" && "$TS" gate --stamp tasks/T-20260812-evidence-loop.md >/dev/null)
AUTH_REF="$(grep '^signed_off_sig:' "$WORK/tasks/T-20260812-evidence-loop.md" | sed 's/^signed_off_sig: //')"
check "v4 handoff emitted" bash -c "cd '$WORK' && '$TS' handoff tasks/T-20260812-evidence-loop.md --backend codex > evidence/handoff.json && grep -q '\"contract\": \"TaskHandoff/v2\"' evidence/handoff.json"

printf 'portable\n' > "$WORK/proof.txt"
check "baseline discrimination audit" bash -c "cd '$WORK' && '$TS' eval-audit tasks/T-20260812-evidence-loop.md --baseline HEAD --report evidence/audit.json"
check "holdout descriptor sealed" "$TS" holdout seal "$WORK/evidence/holdout.json" --out "$WORK/evidence/holdout-descriptor.json"
cat > "$WORK/evidence/tampered-holdout.json" <<'JSON'
{"contract":"HoldoutBundle/v1","task_id":"T-20260812-evidence-loop","checks":[{"id":"holdout_proof","argv":["bash","-lc","true"],"verifies":["B-1"]}]}
JSON
check "tampered holdout bundle is rejected" bash -c "! '$TS' holdout verify '$WORK/evidence/holdout-descriptor.json' '$WORK/evidence/tampered-holdout.json' >/dev/null 2>&1"
check "holdout executed independently" "$TS" holdout run "$WORK/evidence/holdout-descriptor.json" "$WORK/evidence/holdout.json" --workspace "$WORK" --receipt-out "$WORK/evidence/holdout-receipt.json"
check "environment receipt created" "$TS" receipt environment --task-id T-20260812-evidence-loop --contract "$WORK/evidence/environment.json" --provider local-test --environment-digest env:test --out "$WORK/evidence/environment-receipt.json"
check "graded receipt created" "$TS" receipt graded --task-id T-20260812-evidence-loop --authorization-ref "$AUTH_REF" --evaluator rubric-test --rubric-digest "$RUBRIC" --score 0.9 --threshold 0.8 --out "$WORK/evidence/graded-receipt.json"
check "human receipt created" "$TS" receipt human --task-id T-20260812-evidence-loop --authorization-ref "$AUTH_REF" --owner release-owner --accepted-by reviewer --decision accept --out "$WORK/evidence/human-receipt.json"
check "identity receipt signed" "$TS" identity sign "$WORK/tasks/T-20260812-evidence-loop.md" --private-key "$WORK/evidence/identity/identity.ed25519.pem" --public-key "$WORK/evidence/identity/identity.ed25519.pub.pem" --signer reviewer --out "$WORK/evidence/identity-receipt.json"
check "identity receipt verified" "$TS" identity verify "$WORK/evidence/identity-receipt.json" --public-key "$WORK/evidence/identity/identity.ed25519.pub.pem"
check "all typed receipts validate" "$TS" receipt validate "$WORK/evidence/holdout-receipt.json" "$WORK/evidence/environment-receipt.json" "$WORK/evidence/graded-receipt.json" "$WORK/evidence/human-receipt.json" "$WORK/evidence/identity-receipt.json"
cat > "$WORK/evidence/credential-bearing.json" <<'JSON'
{"contract":"HumanAcceptanceReceipt/v1","task_id":"T-20260812-evidence-loop","authorization_ref":"x","owner":"release-owner","accepted_by":"reviewer","accepted_at":"2026-08-12T12:00:00Z","decision":"accept","api_key":"must-not-cross"}
JSON
check "credential-bearing receipt is rejected" bash -c "! '$TS' receipt validate '$WORK/evidence/credential-bearing.json' >/dev/null 2>&1"

cat > "$WORK/evidence/engine-matrix.json" <<'JSON'
{"contract":"EngineMatrix/v1","engines":[
{"family":"openai","provider":"OpenAI","model_id":"gpt-5.6","adapter_version":"1","enabled":false},
{"family":"anthropic","provider":"Anthropic","model_id":"claude-opus-4.1","adapter_version":"1","enabled":false},
{"family":"google","provider":"Google","model_id":"gemini-2.5-pro","adapter_version":"1","enabled":false},
{"family":"xai","provider":"xAI","model_id":"grok-4","adapter_version":"1","enabled":false},
{"family":"deepseek","provider":"DeepSeek","model_id":"deepseek-v3","adapter_version":"1","enabled":false},
{"family":"kimi","provider":"Moonshot","model_id":"kimi-k2","adapter_version":"1","enabled":false},
{"family":"minimax","provider":"MiniMax","model_id":"minimax-m2","adapter_version":"1","enabled":false},
{"family":"qwen","provider":"Alibaba","model_id":"qwen3-coder","adapter_version":"1","enabled":false},
{"family":"glm","provider":"Zhipu","model_id":"glm-4.5","adapter_version":"1","enabled":false}]}
JSON
python3 - "$WORK/evidence/engine-matrix.json" "$WORK/evidence/engine-matrix-enabled.json" <<'PY'
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
value["engines"][0].update({"enabled": True, "argv": ["bash", "-lc", "printf 'portable\\n' > proof.txt"]})
json.dump(value, open(sys.argv[2], "w", encoding="utf-8"))
PY
check "enabled engine runs in a detached worktree" "$TS" evidence run "$WORK/evidence/engine-matrix-enabled.json" --handoff "$WORK/evidence/handoff.json" --out-dir "$WORK/evidence/matrix-enabled"
check "isolated engine receipt records a real attempt" bash -c "python3 -c 'import json; d=json.load(open(\"$WORK/evidence/matrix-enabled/receipts/openai.json\")); assert d[\"terminal_outcome\"] == \"pass\" and d[\"attempts\"] == 1 and \"isolation=detached-git-worktree\" in d[\"deviations\"]'"
check "isolated engine change is captured outside the source workspace" bash -c "grep -q 'proof.txt' '$WORK/evidence/matrix-enabled/raw/openai-status.txt' && grep -q '\"path\": \"proof.txt\"' '$WORK/evidence/matrix-enabled/raw/openai-files.json' && test \"\$(cat '$WORK/proof.txt')\" = portable"

check "acceptance blocks when evidence is omitted" bash -c "cd '$WORK' && ! '$TS' accept --no-blast-radius tasks/T-20260812-evidence-loop.md >/dev/null 2>&1"
check "acceptance passes with matching evidence" bash -c "cd '$WORK' && '$TS' accept --stamp --no-blast-radius --holdout-receipt evidence/holdout-receipt.json --graded-receipt evidence/graded-receipt.json --human-receipt evidence/human-receipt.json --environment-receipt evidence/environment-receipt.json --identity-receipt evidence/identity-receipt.json --identity-public-key evidence/identity/identity.ed25519.pub.pem tasks/T-20260812-evidence-loop.md"
check "revoked identity no longer verifies" bash -c "'$TS' identity revoke --key-id '$KEY_ID' --registry '$WORK/evidence/revocations.json' >/dev/null && ! '$TS' identity verify '$WORK/evidence/identity-receipt.json' --public-key '$WORK/evidence/identity/identity.ed25519.pub.pem' --revocations '$WORK/evidence/revocations.json' >/dev/null 2>&1"

check "A2A bridge round trip" bash -c "'$TS' bridge export '$WORK/evidence/handoff.json' --protocol a2a --out '$WORK/evidence/a2a.json' && '$TS' bridge validate '$WORK/evidence/a2a.json'"
check "MCP bridge round trip" bash -c "'$TS' bridge export '$WORK/evidence/handoff.json' --protocol mcp --out '$WORK/evidence/mcp-task.json' && '$TS' bridge validate '$WORK/evidence/mcp-task.json'"
check "MCP server lists read-only tools" bash -c "printf '%s\n' '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}' | '$TS' mcp | grep -q taskspec_validate"

check "nine-family engine matrix validates" "$TS" evidence validate "$WORK/evidence/engine-matrix.json"
check "disabled engine matrix records unavailable, not fabricated passes" "$TS" evidence run "$WORK/evidence/engine-matrix.json" --handoff "$WORK/evidence/handoff.json" --out-dir "$WORK/evidence/matrix-run"
check "engine matrix emits typed run receipts" bash -c "'$TS' receipt validate '$WORK'/evidence/matrix-run/receipts/*.json"

echo "PASS: Task-Spec 3.7 evidence integrity ($PASS checks)"
