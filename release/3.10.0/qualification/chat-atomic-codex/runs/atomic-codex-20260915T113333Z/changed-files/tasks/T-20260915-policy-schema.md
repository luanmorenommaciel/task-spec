---
id: T-20260915-policy-schema
title: Validate a versioned rate-limit policy schema
status: blocked
format_version: 3
profile: standard
effort: S
budget_iterations: 3
agent: any
parent: (none)
depends_on: []
supersedes: (none)
touches_paths: []
creates_paths:
  - tests/fixtures/toolkit/policy_schema.py
source_note: "tests/fixtures/toolkit/blueprint.md"
created: 2026-09-15T11:34:26Z
tags: []
owner: (none)
priority: P2
severity: feature
due_date: (none)
precondition: (none)
blocked_reason: "Review required for proposed schema fields, numeric domain, version policy, and Python interface; blueprint does not specify these decisions."
security_class: (none)
source_action_item: "Steel thread order, item 1"
tracker_ref: (none)
execution_backend: any
signed_off: false
signed_off_by: (none)
signed_off_at: (none)
accepted: false
accepted_by: (none)
accepted_at: (none)
evidence_refs: []
---

# Validate a versioned rate-limit policy schema

> **Why:** The first blueprint step needs a testable schema boundary so invalid limits and windows cannot enter later policy resolution or enforcement.

## Goal

Deliver one independently testable, versioned policy validator. Completion means
valid inputs are accepted and invalid numeric values, shapes, and versions are
rejected through the same public interface. This is one S-sized leaf with one
write surface and one completion condition; its checks are internal proof, not
separate tasks.

## Context

Source: `tests/fixtures/toolkit/blueprint.md`, **Steel thread order**, item 1:
“A versioned policy schema rejects invalid limits and windows.”

Source SHA-256: `f40ed16c2898b8363dfce1c19e7c3fd539d52810d52b21faeaf59323117af445`.

The source is synthetic fixture evidence, not shipped behavior. The repository
contains no application implementation, schema convention, dependency manifest,
or existing tasks. The referenced `rate-limiting-recipe.yaml` is not present.
The schema module path and Python interface below are proposed fixture-local
choices, not discovered architecture. Python standard library suffices for the
checks; no package installation or network access is required.

### Proposed contract — unresolved until review

- **P-1 (shape/version):** A policy is a plain dictionary with exactly `version`,
  `limit`, and `window_seconds`. Only integer `version: 1` is supported. Missing
  and extra fields, non-dictionaries, booleans, and coerced version values fail.
- **P-2 (numeric domain):** `limit` and `window_seconds` are strictly positive
  Python integers, excluding booleans. Windows use whole seconds. Zero, negative,
  fractional, string, null, and non-finite values fail without coercion. No upper
  bound is proposed; checks include a large integer. `100` and `60` are test
  examples, not defaults or required production thresholds.
- **P-3 (interface/location):** Create only
  `tests/fixtures/toolkit/policy_schema.py`, exposing
  `validate_policy(policy) -> dict`. Valid input returns an equal dictionary;
  invalid input raises `ValueError`. Validation never mutates its input. No
  defaulting, migration, external IO, storage, clock, or service dependency.

All behaviors and executable checks below instantiate these **proposals**.
`status: blocked` preserves the unresolved decisions. Review must settle P-1
through P-3 and revise the contract and checks together before any authorization.
This authoring request grants no implementation, signing, or acceptance authority.

### Scope and sequence for a future authorized attempt

1. Read the reviewed contract and immutable evals; confirm the sole output path.
2. Implement the public validator within that file and without external dependencies.
3. Run all three evals and their Exit Check; report failures and stop at the budget.

Blueprint items 2–4 (organization resolution, request counting/denial, stable denial
reason and decision telemetry), provider-owned usage metering, production storage,
and deployment infrastructure are outside this leaf. Passing its checks proves
only the schema boundary, not the complete rate-limiting steel thread.

## Behavior

- **B-1** — GIVEN a policy satisfying proposed P-1/P-2, WHEN `validate_policy` runs, THEN it returns an equal dictionary without modifying input (P-3).
- **B-2** — GIVEN an invalid limit or window under P-2, WHEN `validate_policy` runs, THEN it raises `ValueError` without modifying input (P-3).
- **B-3** — GIVEN an unsupported version, missing/extra field, or invalid top-level shape under P-1, WHEN `validate_policy` runs, THEN it raises `ValueError` without modifying input (P-3).

## Success Criteria

Run from the repository root using Bash and Python 3. Every eval imports and calls
the proposed public interface; presence checks alone never count as success.
Missing implementation produces a deliberate assertion failure. No check writes
files or needs application infrastructure. Each eval runs in a fresh interpreter.

```bash
eval_1() {
  python3 -B - <<'PY_EVAL_1'
import copy
import importlib.util
from pathlib import Path

path = Path("tests/fixtures/toolkit/policy_schema.py")
assert path.is_file(), "policy schema module is missing (implementation not authored)"
spec = importlib.util.spec_from_file_location("policy_schema_under_test", path)
assert spec is not None and spec.loader is not None, "module cannot be loaded"
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
validate = getattr(module, "validate_policy", None)
assert callable(validate), "validate_policy must be callable"

for limit in (1, 2, 100, 101, 10**30):
    for window in (1, 2, 60, 3600, 10**30):
        value = {"version": 1, "limit": limit, "window_seconds": window}
        before = copy.deepcopy(value)
        for _ in range(2):
            result = validate(value)
            assert type(result) is dict and result == before, (before, result)
            assert value == before, f"mutated valid policy: {before!r}"
PY_EVAL_1
}

eval_2() {
  python3 -B - <<'PY_EVAL_2'
import copy
import importlib.util
from pathlib import Path

path = Path("tests/fixtures/toolkit/policy_schema.py")
assert path.is_file(), "policy schema module is missing (implementation not authored)"
spec = importlib.util.spec_from_file_location("policy_schema_under_test", path)
assert spec is not None and spec.loader is not None, "module cannot be loaded"
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
validate = getattr(module, "validate_policy", None)
assert callable(validate), "validate_policy must be callable"


def expect_invalid(value):
    before = copy.deepcopy(value)
    try:
        validate(value)
    except ValueError:
        pass
    else:
        raise AssertionError(f"accepted invalid policy: {value!r}")
    assert value == before, f"mutated invalid policy: {before!r}"

for field in ("limit", "window_seconds"):
    for invalid in (0, -1, -100, 0.5, 1.0, "1", "", None, True, False,
                    float("nan"), float("inf"), float("-inf"), [], {}):
        value = {"version": 1, "limit": 100, "window_seconds": 60}
        value[field] = invalid
        expect_invalid(value)
PY_EVAL_2
}

eval_3() {
  python3 -B - <<'PY_EVAL_3'
import copy
import importlib.util
from pathlib import Path

path = Path("tests/fixtures/toolkit/policy_schema.py")
assert path.is_file(), "policy schema module is missing (implementation not authored)"
spec = importlib.util.spec_from_file_location("policy_schema_under_test", path)
assert spec is not None and spec.loader is not None, "module cannot be loaded"
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
validate = getattr(module, "validate_policy", None)
assert callable(validate), "validate_policy must be callable"


def expect_invalid(value):
    before = copy.deepcopy(value)
    try:
        validate(value)
    except ValueError:
        pass
    else:
        raise AssertionError(f"accepted invalid policy: {value!r}")
    assert value == before, f"mutated invalid policy: {before!r}"

base = {"version": 1, "limit": 100, "window_seconds": 60}
for version in (0, -1, 2, 999, "1", 1.0, True, False, None, [], {}):
    expect_invalid(dict(base, version=version))
for field in base:
    value = dict(base)
    del value[field]
    expect_invalid(value)
expect_invalid(dict(base, extra="unexpected"))
for value in ({}, None, [], [base], "policy", 1, True):
    expect_invalid(value)
PY_EVAL_3
}
```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: Accept valid policies at lower, ordinary, and large integer values without mutation
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 2
  - id: eval_2
    description: Reject invalid limits and windows without coercion or mutation
    runnable: bash
    check_type: deterministic
    verifies: [B-2]
    terminal: true
    expected_duration_sec: 2
  - id: eval_3
    description: Reject unsupported versions and malformed policy shapes without mutation
    runnable: bash
    check_type: deterministic
    verifies: [B-3]
    terminal: true
    expected_duration_sec: 2
retry_policy:
  max_iterations: 3
  circuit_breaker_no_progress: 2
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails, operations]
  produce: [code]
  required_tools: [git, bash, python3]
  timeout_minutes: 30
  sandbox_type: host
  output_artifacts:
    - tests/fixtures/toolkit/policy_schema.py
  mcp_dependencies: []
  emit: [pass, fail, retry_with_reason, parked_with_context]
  backend_metadata: {}
```

## Exit Check

```bash
eval_1 && eval_2 && eval_3
```

## Rollback Plan

The implementation is additive. A future attempt may remove only its newly
created `tests/fixtures/toolkit/policy_schema.py` after confirming it did not
preexist; otherwise stop and report the conflicting file. Preserve other changes.
Record failure context through the lifecycle CLI. Do not commit or alter the
blueprint as part of this task.

## Observability Hooks

The local eval process returns zero only for passing assertions and prints a
traceback with the failing input otherwise. All three checks should finish in
six seconds total on an ordinary workstation. No production telemetry is needed
for this fixture validator; decision telemetry belongs to blueprint item 4.

## Anti-Patterns

- Do not satisfy checks with a file-existence test, canned output, or a no-op;
  the oracle exercises actual valid and invalid policies.
- Do not coerce strings/floats/bools, silently default fields, or ignore unknown
  versions under the proposed contract.
- Do not implement resolution, counters, denial responses, metering, or telemetry
  to make this schema task look like the full steel thread.
- Do not treat proposal values as source requirements or edit sealed evals to
  match an implementation. Resolve proposals before sealing.

## Do-Not-Touch

- `tests/fixtures/toolkit/blueprint.md` (read-only evidence).
- `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/`, `.codex/`, `.taskspec/`, `.git/`.
- Installed TaskSpec engine and signing/acceptance artifacts.
- This TaskSpec's acceptance contract during future execution.
- Every implementation path outside the sole declared `creates_paths` entry.

## Open Questions

These are review blockers, not decisions for an executor to make silently:

1. **P-1:** Confirm or revise the three field names, strict shape, version `1`,
   and rejection of unsupported versions and unknown fields.
2. **P-2:** Confirm or revise whole-second windows, positive-only integer values,
   treatment of zero, and absence of an upper bound. The source gives no ranges.
3. **P-3:** Confirm or revise the fixture-local Python API, return/error contract,
   and input immutability. No existing implementation constrains these choices.

The next action is review of these proposals and the evals. This draft remains
unsigned and unaccepted; no gate, handoff, executor, or acceptance is requested.
