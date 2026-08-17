# Runbook: Dispatching a Task-Spec

> **Use when:** A spec has passed the gate (`signed_off: true` in frontmatter) and you're ready to hand it to an autonomous engine.

This runbook closes the loop after stamping. Up to and including `safe-to-delegate.sh --stamp`, the author is in the driver's seat. Past `signed_off: true`, the engine is.

This file is a **router**. The pre-flight checks and post-dispatch verification are common to every engine; the engine-specific dispatch command lives in a paired recipe file under `../harness/engines/`.

---

## Pick your engine

The spec's `execution_backend:` frontmatter field names the canonical executor. Look up the value and jump to the matching recipe:

| `execution_backend` | Recipe | Best for |
|---------------------|--------|----------|
| `claude` | [../harness/engines/claude-code.md](../../harness/engines/claude-code.md) | Interactive sessions, subagent delegation via `Task()`; the orchestrator |
| `codex` | [../harness/engines/codex.md](../../harness/engines/codex.md) | OpenAI Codex CLI; review + adversarial passes (different model family) |
| `kimi` | [../harness/engines/kimi.md](../../harness/engines/kimi.md) | One supported harness for atomic XS/S/M/L leaves when configured |
| `glm` | [../harness/engines/gemini.md](../../harness/engines/gemini.md) | Example long-horizon backend for L leaves |
| `gemini` | [../harness/engines/gemini.md](../../harness/engines/gemini.md) | Generic completion-API CLIs (Gemini, llm, ollama, aichat) |
| `any` / `custom` / unknown | [../harness/engines/custom.md](../../harness/engines/custom.md) | DIY escape hatch; references v2.2's deferred `dispatch_recipe:` field |

If `execution_backend: any`, choose an installed harness explicitly when creating the handoff.

### Size and capability

When the backend is `any`, use the spec's `effort` to pick a builder. This is a *dispatcher
heuristic*, not a spec requirement — it never overrides an explicit `execution_backend`, and
the agent contract treats the model inside a backend as a black box (clause C9).

| `effort` | Recommended engine | Rationale |
|----------|--------------------|-----------|
| `XS` / `S` / `M` | Any conformant selected harness | Runnable atomic leaves |
| `L` | A backend listed in `TASKSPEC_LONG_HORIZON_BACKENDS` | One coherent long-horizon leaf |
| `XL` / `XXL` | None | Composition nodes; hand off their child leaves instead |

> Backend names are non-normative. Configure eligible L-leaf tokens through
> `TASKSPEC_LONG_HORIZON_BACKENDS`; executor-specific settings stay under
> `backend_metadata` or outside the portable handoff.

---

## Pre-flight checklist

Regardless of engine, verify these before dispatching:

```bash
# 1. The spec is at signed_off: true
grep '^signed_off:' tasks/T-<your-spec>.md
# Expect: signed_off: true

# 2. Re-running the gate is a no-op (idempotency) AND check the sign-off TIER
taskspec gate tasks/T-<your-spec>.md
# Expect: VERDICT: DELEGATE
# Also read the sign-off tier line:
#   "sign-off: Tier 1"                          → full crypto trust, unsupervised OK
#   "sign-off: structural-only (Tier 2)"        → SUPERVISED DISPATCH ONLY (see policy below)
#   "sign-off: Tier 3"                          → DO NOT DISPATCH (tampered after stamping)

# 3. The working tree is clean (so we can attribute the engine's diff)
git status --short
# Expect: empty (or only the spec file itself)

# 4. You're on the branch where the work should land
git branch --show-current
```

If any of these fail, **do not dispatch**. Fix the precondition first, then return to your engine's recipe.

### Sign-off tier gate (MANDATORY, v2.2)

The HMAC sign-off envelope (see [../concepts/signed-off.md](../concepts/signed-off.md)) classifies every stamped spec into one of three tiers. Unsupervised dispatch eligibility depends on the tier:

| Tier | Meaning | Unsupervised crank? |
|------|---------|---------------------|
| **Tier 1** | key present, `signed_off_sig` HMAC verifies | **Yes** — full crypto trust |
| **Tier 2** | no key resolved, narrow HMAC v1/v2, or another explicitly downgraded gate | **NO — supervised dispatch only**. Acceptance needs supervisor identity and reason. |
| **Tier 3** | key present but HMAC mismatch / malformed sig | **NO** — treat as tampered; re-stamp before dispatch |

**Why Tier 2 is supervised-only:** Tier 2 is structurally valid but cryptographically unverified — an adversary who read this skill could run the verifier *without* the key to reach the (forgeable) Tier-2 state and try to dispatch unsupervised. The supervised-only rule removes that bypass. To promote a Tier-2 spec to Tier-1 unsupervised trust: provision a key with `tools/setup-taskspec-signing-key.sh` (or export `TASKSPEC_SIGNING_KEY`), then re-run `safe-to-delegate.sh --stamp`.

**Enforcing the policy in automation:** the supervised-only rule is not just prose—an automated dispatcher can enforce it mechanically.

*Machine-readable tier* — for any signed spec, `safe-to-delegate.sh` emits exactly one `TIER=N` line to stdout (`N` ∈ {1,2,3}). Parse that line instead of the colored prose:

```bash
tier=$(taskspec gate tasks/T-<spec>.md | sed -n 's/^TIER=//p')
[[ "$tier" == "1" ]] || { echo "refusing unsupervised dispatch (Tier $tier)"; exit 1; }
```

*Hard gate* — pass `--require-tier1` to make the gate itself exit non-zero on anything below Tier 1, so a CI pipeline that branches on `$?` cannot crank a Tier-2 spec unattended:

```bash
taskspec gate --require-tier1 tasks/T-<spec>.md
# exit 0 only when sign-off is Tier 1 (crypto trust); exit 1 otherwise
```

---

## Post-dispatch acceptance (Phase 9 — ACCEPT)

`safe-to-delegate.sh` is the PRE-flight gate ONLY — it asks "are these evals well-formed enough to delegate?" (an assertion *failure* on unbuilt work is EXPECTED there). It is the WRONG tool after execution. The POST-execution contract is `accept-task.sh`, which asks the opposite question — "now that the executor claims it is done, is the work REAL?" — and answers it without trusting the executor's word.

The executor may transition `ready` → `in-progress` (or `parked` on terminal
failure). It must not write `done` directly. After the session completes:

```bash
# 1. The spec's status should reflect the outcome
grep '^status:' tasks/T-<spec>.md

# 2. ACCEPT the work against the same TaskHandoff/v3: rerun evals, compare the
#    committed/index/worktree/untracked union with its immutable base, verify
#    TaskRevision and closure, bind receipts, and write AcceptanceRecord/v1.
taskspec accept --handoff .taskspec/handoffs/<attempt>.json --stamp tasks/T-<spec>.md
# Expect: VERDICT: ACCEPT (and the machine-readable line ACCEPTED=1)
#
# Optional hardening:
#   --gold-sanity   also reconstruct the unpatched baseline in an ephemeral git
#                   worktree and BLOCK any eval that PASSES there (a non-
#                   discriminating / reward-hackable eval proves nothing).
# e.g.: taskspec accept --handoff .taskspec/handoffs/<attempt>.json --stamp --gold-sanity tasks/T-<spec>.md

# 3. Settle only after acceptance
taskspec transition T-<spec> done
```

If the engine reported success but `accept-task.sh` returns `VERDICT: REJECT` (`ACCEPTED=0`, exit 1), treat that as a **real defect** — the engine claimed completion that the contract does not corroborate. Park the task with `blocked_reason: engine-success-but-accept-fails`, document the divergence, and re-author or re-dispatch.

---

## What NOT to do

- **Don't manually flip `signed_off:` back to `false` after dispatch.** The contract is durable — if the engine produces wrong work, the right response is to revert the diff, not to relitigate the gate. Park the task instead.
- **Don't dispatch a spec whose `signed_off: true` was hand-edited.** The structural sign-off envelope check (see `validate-task-spec.sh` v2.1+) will reject it; supervisors should refuse to dispatch.
- **Don't issue a handoff from an unreviewed dirty working tree.** The immutable
  base and union diff can identify later changes, but they cannot decide which
  pre-existing uncommitted change you intended to authorize.
- **Don't ignore engine exit codes 2-6.** Each one names a specific recoverable condition; treating them as opaque failures wastes the typed-error system the engine provides. See the engine's recipe for the exit-code table.
- **Don't treat a clean `safe-to-delegate.sh` re-run as acceptance.** That script is the PRE-flight gate; post-execution acceptance is `accept-task.sh` (Phase 9). A spec is provably DONE only when `accept-task.sh --stamp` returns `VERDICT: ACCEPT` and writes the `accepted:` envelope.

---

## See also

- [../harness/engines/claude-code.md](../../harness/engines/claude-code.md)
- [../harness/engines/codex.md](../../harness/engines/codex.md)
- [../harness/engines/kimi.md](../../harness/engines/kimi.md)
- [../harness/engines/gemini.md](../../harness/engines/gemini.md) — also serves `glm` (generic completion-API) until a dedicated recipe lands
- [../harness/engines/custom.md](../../harness/engines/custom.md)
- [validating-a-task-spec.md](validating-a-task-spec.md) — pre-gate linter walkthrough
- `../../src/accept/accept-task.sh` — the Phase 9 POST-execution acceptance gate (run after the engine finishes)
- [../concepts/signed-off.md](../concepts/signed-off.md) — the autonomy contract
- [../concepts/agent-contract.md](../concepts/agent-contract.md) — cross-vendor execution contract
- [from-fuzzy-intent.md](from-fuzzy-intent.md) — paragraph → spec (start here if you don't have a spec yet)
- [first-spec-walkthrough.md](first-spec-walkthrough.md) — your first 10 minutes (new authors)
