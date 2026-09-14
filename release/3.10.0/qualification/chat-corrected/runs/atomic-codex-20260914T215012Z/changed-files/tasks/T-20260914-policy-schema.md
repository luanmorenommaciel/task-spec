---
id: T-20260914-policy-schema
title: "Define and validate the version-one rate-limit policy schema"
status: ready
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
  - src/policy_schema.py
source_note: "tests/fixtures/toolkit/blueprint.md"
created: 2026-09-14T21:51:01Z
tags: []
owner: (none)
priority: P2
severity: feature
due_date: (none)
precondition: (none)
blocked_reason: (none)
security_class: (none)
source_action_item: (none)
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

# Define and validate the version-one rate-limit policy schema

> **Why:** The first steel-thread step needs an independently testable policy boundary that rejects invalid limits and windows before later resolution or enforcement consumes them.

## Goal

Create `src/policy_schema.py` with `SCHEMA_VERSION = 1` and a pure
`validate_policy(policy)` function implementing the version-one record contract
below. Completion means all three embedded behavioral evals pass against that
module. This is one S-sized leaf: defining the record and validating it share
one outcome, write surface, and acceptance boundary; no downstream task is needed
to assess this boundary.

## Context

Source: `tests/fixtures/toolkit/blueprint.md`, Steel thread order, item 1:
“A versioned policy schema rejects invalid limits and windows.” The source is
synthetic fixture evidence, not a statement of shipped behavior. Items 2–4
(resolution, request enforcement, denial reasons, and telemetry) are out of scope.
Provider-owned usage metering, production storage, and deployment are also excluded.

The repository currently has no application implementation or selected language.
For this review draft, propose a dependency-free Python 3 module and a JSON-shaped
record; this does not claim that the blueprint chose Python or these field names.
No JSON Schema standard document or external validation package is required.

Proposed contract for review:

- Input is a dictionary with exactly `schema_version`, `limit`, and `window_seconds`.
- `schema_version` is an integer equal to `SCHEMA_VERSION`, which is integer `1`.
- `limit` and `window_seconds` are strictly positive integers. Units are requests
  per window and seconds per window. There is no additional product maximum in v1.
- Booleans, floating-point values (including integral floats), numeric strings,
  nulls, missing fields, unknown fields, and non-dictionary inputs are invalid.
- Success returns an equal, separate dictionary. Validation does not change input.
- Invalid input raises `ValueError`; exception text is not a public contract.
  Do not coerce values, supply defaults, silently discard fields, or migrate versions.

Only the TaskSpec is authored now. The module remains absent until a separately
authorized implementation. `status: ready` describes a complete draft;
`signed_off: false` and `accepted: false` preserve its review-only authority state.

## Behavior

- **B-1** — GIVEN a v1 record with positive integer limits and windows WHEN validated THEN return an equal independent dictionary without changing the input; accept minimum values, ordinary values, and large positive values.
- **B-2** — GIVEN zero, negative, or non-integer limits or windows WHEN validated THEN raise `ValueError` without changing the input.
- **B-3** — GIVEN a missing or unsupported version, malformed record shape, or unknown field WHEN validated THEN raise `ValueError` without changing dictionary inputs.

## Success Criteria

Run from the repository root with Bash and Python 3. Each eval reads the actual
module using the standard library, runs without network access, and writes no
bytecode. An absent implementation fails with an explicit assertion. Constant
success, constant rejection, and coercion cannot satisfy these checks.

```bash
# eval-1: Accept valid v1 records and preserve input
eval_1() {
  python3 -B - <<'PY_EVAL'
from pathlib import Path
import copy
import runpy

path = Path("src/policy_schema.py")
assert path.is_file(), "policy-schema implementation is absent"
module = runpy.run_path(str(path))
validate = module.get("validate_policy")
assert callable(validate), "validate_policy must be callable"
assert type(module.get("SCHEMA_VERSION")) is int
assert module["SCHEMA_VERSION"] == 1
for limit, window in [(1, 1), (100, 60), (7, 3600), (2**63, 2**32)]:
    policy = {"schema_version": 1, "limit": limit, "window_seconds": window}
    before = copy.deepcopy(policy)
    result = validate(policy)
    assert type(result) is dict and result == before, (policy, result)
    assert result is not policy, "result must be an independent record"
    result["limit"] = 999
    assert policy == before, "validation or result mutation changed input"
print("B-1: valid policy boundaries passed")
PY_EVAL
}

# eval-2: Reject invalid limit and window values
eval_2() {
  python3 -B - <<'PY_EVAL'
from pathlib import Path
import copy
import runpy

path = Path("src/policy_schema.py")
assert path.is_file(), "policy-schema implementation is absent"
module = runpy.run_path(str(path))
validate = module.get("validate_policy")
assert callable(validate), "validate_policy must be callable"
invalid = [0, -1, -100, True, False, 1.0, 1.5, float("inf"), "1", "", None, [], {}]
for field in ("limit", "window_seconds"):
    for value in invalid:
        policy = {"schema_version": 1, "limit": 100, "window_seconds": 60}
        policy[field] = value
        before = copy.deepcopy(policy)
        try:
            validate(policy)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid {field}: {value!r}")
        assert policy == before, "invalid input was changed"
    # NaN needs a separate comparison because NaN is unequal to itself.
    policy = {"schema_version": 1, "limit": 100, "window_seconds": 60}
    nan = float("nan")
    policy[field] = nan
    before = dict(policy)
    try:
        validate(policy)
    except ValueError:
        pass
    else:
        raise AssertionError(f"accepted NaN {field}")
    assert policy.keys() == before.keys()
    assert policy[field] is nan
    assert all(policy[k] == before[k] for k in before if k != field)
print("B-2: invalid limit and window matrix passed")
PY_EVAL
}

# eval-3: Reject malformed records and unsupported versions
eval_3() {
  python3 -B - <<'PY_EVAL'
from pathlib import Path
import copy
import runpy

path = Path("src/policy_schema.py")
assert path.is_file(), "policy-schema implementation is absent"
module = runpy.run_path(str(path))
validate = module.get("validate_policy")
assert callable(validate), "validate_policy must be callable"
base = {"schema_version": 1, "limit": 100, "window_seconds": 60}
cases = [None, [], "policy", 1, True, {}, dict(base, unexpected="value")]
for field in base:
    cases.append({key: value for key, value in base.items() if key != field})
for version in [0, -1, 2, 100, True, False, 1.0, "1", "v1", None, [], {}]:
    cases.append(dict(base, schema_version=version))
for policy in cases:
    before = copy.deepcopy(policy)
    try:
        validate(policy)
    except ValueError:
        pass
    else:
        raise AssertionError(f"accepted malformed policy: {policy!r}")
    assert policy == before, "malformed input was changed"
print("B-3: record shape and version matrix passed")
PY_EVAL
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: Accept valid v1 records and preserve input
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 1
  - id: eval_2
    description: Reject invalid limit and window values
    runnable: bash
    check_type: deterministic
    verifies: [B-2]
    terminal: true
    expected_duration_sec: 1
  - id: eval_3
    description: Reject malformed records and unsupported versions
    runnable: bash
    check_type: deterministic
    verifies: [B-3]
    terminal: true
    expected_duration_sec: 1
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
    - path: src/policy_schema.py
      type: code
  mcp_dependencies: []
  emit: [pass, fail, retry_with_reason, parked_with_context]
  backend_metadata: {}
```

## Exit Check

```bash
eval_1 && eval_2 && eval_3
```

## Rollback Plan

The proposed implementation only adds `src/policy_schema.py`. If an authorized
attempt must be rolled back, remove that file only if it was created by that
attempt, preserving unrelated work. There is no persistent-data migration.
Authoring this draft does not require an implementation rollback.

## Observability Hooks

Each eval emits its behavior ID on success and an assertion or exception on
failure, with an expected runtime below one second. No runtime telemetry is part
of this schema boundary; denial telemetry belongs to a later steel-thread step.

## Anti-Patterns

- Do not treat booleans as integers or coerce strings/floats into accepted values.
- Do not replace validation with fixed success or rejection; both positive and
  negative behavioral matrices must pass against the delivered module.
- Do not introduce policy resolution, counters, storage, providers, API handlers,
  enforcement, or telemetry to satisfy this leaf.
- Do not modify this contract or weaken its evals to make implementation pass.

## Do-Not-Touch

- `tests/fixtures/toolkit/blueprint.md` (read-only source evidence).
- `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/`, `.codex/`, `.taskspec/`, and the installed TaskSpec engine.
- `tasks/T-20260914-policy-schema.md` and its acceptance checks during implementation.
- Every implementation path outside the sole declared create path.
- No commits, publication, deployment, authorization stamps, or acceptance records
  are permitted by this authoring request.

## Open Questions

(none — this draft specifies a complete proposed contract for review.)
The reviewer can revise the proposed language, field names, units, and strictness
before authorization. These choices are proposals derived to make the sparse
fixture executable, not prior product decisions recorded by the blueprint.
