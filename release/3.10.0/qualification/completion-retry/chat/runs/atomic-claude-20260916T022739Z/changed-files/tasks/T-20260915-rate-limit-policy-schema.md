---
id: T-20260915-rate-limit-policy-schema
title: "Add a versioned rate-limit policy schema that rejects invalid limits and windows"
status: blocked
format_version: 3
# lite | standard | full — scales required zones to effort/blast-radius (see docs/concepts/profiles.md)
profile: standard
# LEAF: XS|S|M|L. NODE: XL|XXL (must declare children; never delegated directly).
effort: S
budget_iterations: 15
agent: any
# FEATURE-altitude PRD/SDD this task decomposes from (path or url); the task DISTILLS it, never embeds it
parent: (none)
depends_on: []
# explicit replanning only; downstream dependencies are never rewritten automatically
supersedes: (none)

touches_paths: []
creates_paths:
  - src/rate_limiting/policy_schema.py
  - tests/test-policy-schema.sh
source_note: "tests/fixtures/toolkit/blueprint.md sha256:f40ed16c2898b8363dfce1c19e7c3fd539d52810d52b21faeaf59323117af445 (steel thread step 1)"
created: 2026-09-16T02:31:58Z
tags: []
owner: (none)
priority: P2
# cosmetic | refactor | feature | bugfix | security | financial-critical
severity: feature
due_date: (none)
precondition: (none)
blocked_reason: "Draft authored for review. The concrete schema contract (policy shape, supported version set, limit and window bounds, error-code names) is proposed here, not stated by the blueprint; see Open Questions. Confirm or replace those decisions at review before sign-off."
security_class: (none)
source_action_item: (none)
# optional vendor-neutral backlink: <tracker>:<reference>
tracker_ref: (none)
# OPEN STRING naming the executor. L must use a backend listed in TASKSPEC_LONG_HORIZON_BACKENDS.
execution_backend: any
# flipped true by safe-to-delegate.sh — the autonomy contract; nothing runs unattended without it
signed_off: false
# who/what signed off (e.g. luan, safe-to-delegate.sh)
signed_off_by: (none)
# ISO-8601 timestamp of sign-off
signed_off_at: (none)
# flipped true by accept-task.sh AFTER execution — closes the loop (evals re-run from clean checkout + blast-radius + envelope)
accepted: false
accepted_by: (none)
accepted_at: (none)
evidence_refs: []

---

# "Add a versioned rate-limit policy schema that rejects invalid limits and windows"

> **Why:** Steel thread step 1 of the rate-limiting blueprint. Every later step — policy
> resolution, the 101st-request denial, denial telemetry — reads a policy, so without a
> versioned schema that rejects invalid limits and windows each of those steps would have
> to re-validate its input and would otherwise inherit malformed policies.

---

## Goal

Add a versioned rate-limit policy schema module that validates one policy document in
memory. `src/rate_limiting/policy_schema.py` exposes `SUPPORTED_SCHEMA_VERSIONS` and
`validate_policy(policy) -> {"valid": bool, "errors": [{"code": str, "field": str}]}`.
A well-formed policy at a supported schema version is accepted; an invalid limit, an
invalid window, an unsupported or missing schema version, and a non-mapping input are
each rejected with a named machine-readable error code rather than a raised exception.
Validation reports every applicable fault, not just the first.

---

## Context

Source: `tests/fixtures/toolkit/blueprint.md` (sha256 `f40ed16c…7af445`), steel thread
step 1: "A versioned policy schema rejects invalid limits and windows."

This repository has no rate-limiting source yet; this task creates its first module under
`src/rate_limiting/`. Python 3 and bash are available. No third-party dependency may be
added — the standard library covers this shape. `src/rate_limiting` is an implicit
namespace package: do not add `__init__.py`, so the write surface stays at the two
declared files.

Scope is validation of a single policy document in memory. Steel thread steps 2–4
(resolving exactly one effective policy per organization, denying request 101 in a
window, and the stable denial reason plus decision telemetry) are separate leaves that
depend on this one. Provider-owned usage metering and production storage/deployment are
declared out of scope by the blueprint itself.

The blueprint states that the schema is versioned and rejects invalid limits and windows,
but does not state the concrete contract. The shape, bounds, and error-code names below
are **proposed by this draft** and are listed in Open Questions for review.

For the feature-level PRD/design this task decomposes from, see the `parent:`
frontmatter field — that document is REFERENCED, never copied here. Zone 1 carries
only the one-paragraph distillation needed to execute this atomic unit.

---

## Behavior

Given/When/Then scenarios the implementation must satisfy. Each scenario has a
stable `B-N` id; every eval in the Validation Card declares which behavior(s) it
`verifies:`, and the validator enforces the chain both ways (no orphan behavior,
no orphan eval). Lite-profile specs may omit this section.

- **B-1** — GIVEN a policy declaring a supported `schema_version` with a valid `limit` and
  `window_seconds` WHEN `validate_policy` is called on it THEN it returns `valid: true`
  with an empty `errors` list.
- **B-2** — GIVEN a policy whose `limit` is zero, negative, above the maximum, a string, a
  float, or a bool WHEN `validate_policy` is called on it THEN it returns `valid: false`
  with an error whose `code` is `invalid_limit` and whose `field` is `limit`, without raising.
- **B-3** — GIVEN a policy whose `window_seconds` is zero, negative, above the maximum, a
  string, a float, or a bool WHEN `validate_policy` is called on it THEN it returns
  `valid: false` with an error whose `code` is `invalid_window` and whose `field` is
  `window_seconds`, without raising.
- **B-4** — GIVEN a policy whose `schema_version` is absent, or is present but not in
  `SUPPORTED_SCHEMA_VERSIONS` WHEN `validate_policy` is called on it THEN it returns
  `valid: false` with code `missing_field` when absent and `unsupported_schema_version`
  when unrecognized, and never falls back to a default version.
- **B-5** — GIVEN an input that is not a mapping, or a mapping carrying several independent
  faults WHEN `validate_policy` is called on it THEN it returns `valid: false` reporting
  `invalid_policy` for the non-mapping case and every applicable error code for the
  multi-fault case, rather than raising or stopping at the first fault.
- **B-6** — GIVEN any input WHEN `validate_policy` is called on it THEN the caller's policy
  object is not mutated and the function performs no file, network, or clock access.

---

## Success Criteria

Each criterion is a runnable bash function returning 0 (pass) or non-zero (fail).
Each MUST be terminal (deterministic, idempotent, non-flaky).

```bash
# eval-1: the task-authored contract test for the policy schema passes
eval_1() {
  test -f tests/test-policy-schema.sh || { echo "FAIL: tests/test-policy-schema.sh missing"; return 1; }
  bash tests/test-policy-schema.sh
}

# eval-2: discrimination check run directly against the module API, independent of the
# task-authored test file — an accept-everything stub, a reject-everything stub, and a
# stub that raises on malformed input all fail this eval
eval_2() {
  python3 - <<'PY'
import sys
sys.path.insert(0, "src")
from rate_limiting.policy_schema import validate_policy, SUPPORTED_SCHEMA_VERSIONS

assert "1.0.0" in SUPPORTED_SCHEMA_VERSIONS, SUPPORTED_SCHEMA_VERSIONS
assert "0.9.0" not in SUPPORTED_SCHEMA_VERSIONS, SUPPORTED_SCHEMA_VERSIONS

good = {"schema_version": "1.0.0", "limit": 100, "window_seconds": 60}
res = validate_policy(good)
assert res["valid"] is True and res["errors"] == [], ("valid policy rejected", res)
assert validate_policy({**good, "limit": 1})["valid"] is True, "lower bound limit rejected"
assert validate_policy({**good, "limit": 1000000})["valid"] is True, "upper bound limit rejected"
assert validate_policy({**good, "window_seconds": 1})["valid"] is True, "lower bound window rejected"
assert validate_policy({**good, "window_seconds": 86400})["valid"] is True, "upper bound window rejected"

cases = [
    ({**good, "limit": 0}, "invalid_limit"),
    ({**good, "limit": -1}, "invalid_limit"),
    ({**good, "limit": 1000001}, "invalid_limit"),
    ({**good, "limit": "100"}, "invalid_limit"),
    ({**good, "limit": 100.0}, "invalid_limit"),
    ({**good, "limit": True}, "invalid_limit"),
    ({**good, "window_seconds": 0}, "invalid_window"),
    ({**good, "window_seconds": -60}, "invalid_window"),
    ({**good, "window_seconds": 86401}, "invalid_window"),
    ({**good, "window_seconds": "60"}, "invalid_window"),
    ({**good, "window_seconds": 60.0}, "invalid_window"),
    ({**good, "window_seconds": False}, "invalid_window"),
    ({**good, "schema_version": "0.9.0"}, "unsupported_schema_version"),
    ({"limit": 100, "window_seconds": 60}, "missing_field"),
    (None, "invalid_policy"),
    ([], "invalid_policy"),
]
for policy, code in cases:
    res = validate_policy(policy)
    assert res["valid"] is False, ("accepted invalid policy", policy, res)
    codes = [e["code"] for e in res["errors"]]
    assert code in codes, ("expected", code, "for", policy, "got", res)

multi = validate_policy({"schema_version": "0.9.0", "limit": 0, "window_seconds": 0})
assert {e["code"] for e in multi["errors"]} >= {
    "unsupported_schema_version", "invalid_limit", "invalid_window",
}, ("multi-fault policy did not report every fault", multi)

print("POLICY_SCHEMA_DISCRIMINATION=OK")
PY
}

# eval-3: validation is pure and stays in scope — the caller's policy is not mutated, the
# module performs no I/O, and the read-only evidence fixture is unchanged
eval_3() {
  python3 - <<'PY'
import copy, hashlib, pathlib, sys
sys.path.insert(0, "src")
from rate_limiting.policy_schema import validate_policy

BLUEPRINT = "f40ed16c2898b8363dfce1c19e7c3fd539d52810d52b21faeaf59323117af445"
digest = hashlib.sha256(pathlib.Path("tests/fixtures/toolkit/blueprint.md").read_bytes()).hexdigest()
assert digest == BLUEPRINT, ("read-only blueprint fixture was modified", digest)

policy = {"schema_version": "1.0.0", "limit": 0, "window_seconds": 60, "extra": {"a": [1]}}
before = copy.deepcopy(policy)
validate_policy(policy)
assert policy == before, ("validate_policy mutated its input", policy, before)

src = pathlib.Path("src/rate_limiting/policy_schema.py").read_text()
for banned in ("import requests", "import sqlite3", "import socket", "import urllib",
               "open(", "time.sleep", "datetime.now"):
    assert banned not in src, ("out-of-scope dependency or side effect in validator", banned)

print("POLICY_SCHEMA_SCOPE=OK")
PY
}
```

---

## Validation Card

```yaml
success_criteria:
  # check_type: deterministic (default, bash-checked, preferred) | llm_judge
  # (subjective criteria graded by a fast LLM via judge_prompt — deterministic-first).
  # verifies: the behavior id(s) this eval proves. Standard/full profiles require
  # every B-N to be covered by >=1 eval and every eval to map to a behavior.
  - id: eval_1
    description: the task-authored contract test for the policy schema passes
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2, B-3, B-4, B-5]
    terminal: true
    expected_duration_sec: 20
  - id: eval_2
    description: discrimination check against the module API, independent of the task-authored test file
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2, B-3, B-4, B-5]
    terminal: true
    expected_duration_sec: 20
  - id: eval_3
    description: validation is pure, does not mutate its input, and leaves the read-only evidence fixture unchanged
    runnable: bash
    check_type: deterministic
    verifies: [B-6]
    terminal: true
    expected_duration_sec: 10

retry_policy:
  max_iterations: 15
  circuit_breaker_no_progress: 3
  on_terminal_failure: park_with_context

agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails, operations]
  produce:
    - code
    - tests
  required_tools: [git, bash, python3]
  timeout_minutes: 30
  sandbox_type: host  # host | isolated | ephemeral
  output_artifacts:
    - src/rate_limiting/policy_schema.py
    - tests/test-policy-schema.sh
  mcp_dependencies: []
  emit:
    - pass
    - fail
    - retry_with_reason
    - parked_with_context
  backend_metadata: {}
```

---

## Exit Check

```bash
# Final proof-of-done. Returns 0 only when ALL evals pass.
eval_1 && eval_2 && eval_3
```

---

## Rollback Plan

If execution fails mid-task, revert to the pre-task state:

1. **Git revert** — `git revert --no-commit HEAD` (if commits were made)
2. **File restore** — `git checkout -- <paths>` for any modified files not yet committed
3. **State reset** — update task status to `parked` and record `blocked_reason`

Task-specific: this task is purely additive — it creates `src/rate_limiting/policy_schema.py`
and `tests/test-policy-schema.sh` and modifies no existing file. To revert completely,
delete `src/rate_limiting/` and `tests/test-policy-schema.sh`. No downstream task depends
on this module yet, so removal cannot break steel thread steps 2–4.

(Replace with `(none — this task is append-only or additive with no destructive changes)` if no rollback is needed. Full profile requires concrete steps.)

---

## Observability Hooks

What to watch during execution and after deployment:

(none — this task adds a pure in-memory validation function with no runtime surface.
Decision telemetry is steel thread step 4 and is a separate leaf.)

(Replace with `(none — no runtime observability required)` if not applicable. Full profile requires real hooks.)

---

## Anti-Patterns

- **Don't implement policy resolution, request counting, denial reasons, or decision
  telemetry** — those are steel thread steps 2–4 and are separate leaves with their own
  acceptance. Keep this task to validating one policy document.
- **Don't raise on malformed input as the rejection mechanism** — callers in later steps
  need a structured result they can inspect. Return `valid: false` with error codes.
- **Don't default a missing or unrecognized `schema_version` to the latest supported
  version** — silent version coercion is how an invalid policy reaches enforcement.
  Reject it and name the fault.
- **Don't add a third-party validation dependency** — the standard library covers this
  shape. Use plain type and range checks.
- **Don't treat `bool` as a valid integer** — `True` is an `int` in Python, so an
  `isinstance(v, int)` check alone silently accepts `limit: True`. Exclude `bool` explicitly.
- **Don't add `src/rate_limiting/__init__.py`** — the namespace package already imports,
  and the extra file puts the write surface over the advisory budget for an S leaf.

---

## Do-Not-Touch

Files the executor MUST NOT modify:

- `tests/fixtures/toolkit/blueprint.md` — read-only evidence fixture; `eval_3` pins its digest
- `.taskspec/` — toolkit state and configuration
- `tasks/` — this backlog, including this spec and its evals
- `AGENTS.md`, `CLAUDE.md` — repository instructions

---

## Open Questions

Things the executor should resolve DURING build, not assume:

**These are review decisions, not executor decisions.** The blueprint states only that the
schema is versioned and rejects invalid limits and windows; the concrete contract below is
proposed by this draft. The evals encode these proposals, so changing one means re-authoring
this spec — not editing a sealed eval afterwards. This spec is `status: blocked` until they
are confirmed or replaced at review.

1. **Policy shape** — proposed `{schema_version, limit, window_seconds}`. A fixed-seconds
   window is the simplest representation that satisfies step 1, but step 3 ("request 101
   denied in the same window") may want a `{unit, count}` window instead. Least grounded of
   the decisions here; confirm against step 3 before sealing.
2. **Supported version set** — proposed `SUPPORTED_SCHEMA_VERSIONS == {"1.0.0"}`, with no
   forward compatibility and no default.
3. **Limit bounds** — proposed non-bool `int`, `1 <= limit <= 1000000`. The lower bound
   follows from "invalid limits"; the upper bound is a proposed guard with no source in
   the blueprint.
4. **Window bounds** — proposed non-bool `int`, `1 <= window_seconds <= 86400`. Same status
   as the limit upper bound: proposed, not sourced.
5. **Error codes** — proposed `invalid_limit`, `invalid_window`, `unsupported_schema_version`,
   `missing_field`, `invalid_policy`. Step 4 requires a *stable denial reason*; if that
   vocabulary is shared with these validation codes, it should be decided once, here.
6. **Missing vs. unrecognized version** — proposed `missing_field` when `schema_version` is
   absent and `unsupported_schema_version` when present but unknown, rather than one code
   for both.
