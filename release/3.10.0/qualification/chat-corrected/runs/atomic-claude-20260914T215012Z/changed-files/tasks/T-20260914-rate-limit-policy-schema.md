---
id: T-20260914-rate-limit-policy-schema
title: "Add a versioned rate-limit policy schema that rejects invalid limits and windows"
status: ready
format_version: 3
profile: standard  # lite | standard | full — scales required zones to effort/blast-radius (see docs/concepts/profiles.md)
effort: S  # LEAF: XS|S|M|L. NODE: XL|XXL (must declare children; never delegated directly).
budget_iterations: 15
agent: any
parent: (none)  # FEATURE-altitude PRD/SDD this task decomposes from (path or url); the task DISTILLS it, never embeds it
depends_on: []
supersedes: (none)

touches_paths: []
creates_paths:
  - src/policy/schema.py
  - tests/test_policy_schema.py
source_note: "tests/fixtures/toolkit/blueprint.md"
created: 2026-09-14T21:53:42Z
tags: [rate-limiting, schema, validation]
owner: (none)
priority: P2
severity: feature  # cosmetic | refactor | feature | bugfix | security | financial-critical
due_date: (none)
precondition: (none)
blocked_reason: (none)
security_class: (none)
source_action_item: (none)
tracker_ref: (none)  # optional vendor-neutral backlink: <tracker>:<reference>
execution_backend: any  # OPEN STRING naming the executor. L must use a backend listed in TASKSPEC_LONG_HORIZON_BACKENDS.
signed_off: false  # flipped true by safe-to-delegate.sh — the autonomy contract; nothing runs unattended without it
signed_off_by: (none)  # who/what signed off (e.g. luan, safe-to-delegate.sh)
signed_off_at: (none)  # ISO-8601 timestamp of sign-off
accepted: false  # flipped true by accept-task.sh AFTER execution — closes the loop (evals re-run from clean checkout + blast-radius + envelope)
accepted_by: (none)
accepted_at: (none)
evidence_refs: []

---

# "Add a versioned rate-limit policy schema that rejects invalid limits and windows"

> **Why:** This is step 1 of the rate-limiting steel thread, and every later step
> (resolution, denial, decision telemetry) reads a policy document. A malformed
> limit or window accepted here becomes a wrong allow/deny decision downstream
> with no local signal, so rejection has to happen at the schema boundary — and
> that boundary has to be versioned, so a future policy shape is a named
> rejection rather than a silent reinterpretation of today's fields.

---

## Goal

Add a stdlib-only policy schema module that parses one rate-limit policy
document and either returns a normalized policy — for a supported schema version
with an in-domain limit and window — or raises `PolicySchemaError` carrying a
stable machine-readable `code` and `field`. Unsupported or absent schema
versions, out-of-domain limits, and out-of-domain windows are all rejections.
Done means the evals below pass: a well-formed document normalizes, and every
declared invalid version, limit, and window is rejected with the declared code
and field.

---

## Context

The source of intent is `tests/fixtures/toolkit/blueprint.md`, whose steel thread
orders: (1) versioned schema rejects invalid limits and windows, (2) resolution
produces one effective policy per organization, (3) request 101 is denied after
100 allowed, (4) denial returns a stable reason with matching telemetry. This
task is step 1 only.

This repository has no application source yet, so the atom creates its own module
and tests — the vertical cut is schema definition → validation → normalized
output, exercised end-to-end by the evals.

Authoring assumptions, all open to change in review:

- **Runtime:** Python 3 stdlib only. No YAML, `pydantic`, or `jsonschema`
  dependency, so the evals run offline with nothing installed.
- **Input:** the policy document is a plain `dict`; parsing a file format is not
  in scope.
- **Layout:** `src/` is on `PYTHONPATH` and `src/policy/` is an implicit
  namespace package — no `__init__.py`, which is why the write surface is two
  files.
- **Domain:** `limit` is an `int` in `1..1000000`; `window_seconds` is an `int`
  in `1..86400`; `bool` is not an acceptable `int`; numeric strings and floats
  are not coerced.
- **Versioning:** `SUPPORTED_SCHEMA_VERSIONS == ("1.0",)`, `schema_version` is
  required, and there is no default.
- The blueprint's "100 requests" figure is policy *data*, not a schema constant.

For the feature-level PRD/design this task decomposes from, see the `parent:`
frontmatter field — that document is REFERENCED, never copied here. Zone 1 carries
only the one-paragraph distillation needed to execute this atomic unit.

---

## Behavior

Given/When/Then scenarios the implementation must satisfy. Each scenario has a
stable `B-N` id; every eval in the Validation Card declares which behavior(s) it
`verifies:`, and the validator enforces the chain both ways (no orphan behavior,
no orphan eval). Lite-profile specs may omit this section.

- **B-1** — GIVEN a policy document whose `schema_version` is supported and whose limit and window are in domain WHEN `validate_policy` is called with it THEN it returns a normalized policy exposing `schema_version`, `org_id`, `limit`, and `window_seconds`
- **B-2** — GIVEN a policy document whose `limit` is not an `int` in `1..1000000`, including `bool` and numeric strings WHEN `validate_policy` is called with it THEN it raises `PolicySchemaError` with `code == "invalid_limit"` and `field == "limit"`
- **B-3** — GIVEN a policy document whose `window_seconds` is not an `int` in `1..86400`, including `bool` and numeric strings WHEN `validate_policy` is called with it THEN it raises `PolicySchemaError` with `code == "invalid_window"` and `field == "window_seconds"`
- **B-4** — GIVEN a policy document whose `schema_version` is missing, empty, or outside the supported set WHEN `validate_policy` is called with it THEN it raises `PolicySchemaError` with `code == "unsupported_schema_version"` and `field == "schema_version"`, without defaulting to the current version

---

## Success Criteria

Each criterion is a runnable bash function returning 0 (pass) or non-zero (fail).
Each MUST be terminal (deterministic, idempotent, non-flaky).

```bash
# eval-1: a supported-version document with an in-domain limit and window normalizes
eval_1() {
  PYTHONPATH=src python3 - <<'PY'
from policy.schema import validate_policy

policy = validate_policy({
    "schema_version": "1.0",
    "org_id": "org-123",
    "limit": 100,
    "window_seconds": 60,
})
actual = (
    policy.schema_version,
    policy.org_id,
    policy.limit,
    policy.window_seconds,
)
assert actual == ("1.0", "org-123", 100, 60), actual
PY
}

# eval-2: every out-of-domain limit is rejected with code invalid_limit on field limit
eval_2() {
  PYTHONPATH=src python3 - <<'PY'
from policy.schema import PolicySchemaError, validate_policy

for value in [0, -1, 1000001, True, False, "100", 1.5, None]:
    doc = {
        "schema_version": "1.0",
        "org_id": "org-123",
        "limit": value,
        "window_seconds": 60,
    }
    try:
        validate_policy(doc)
    except PolicySchemaError as err:
        assert err.code == "invalid_limit", (value, err.code)
        assert err.field == "limit", (value, err.field)
    else:
        raise AssertionError("accepted invalid limit: %r" % (value,))
PY
}

# eval-3: every out-of-domain window is rejected with code invalid_window on field window_seconds
eval_3() {
  PYTHONPATH=src python3 - <<'PY'
from policy.schema import PolicySchemaError, validate_policy

for value in [0, -60, 86401, True, False, "60", 60.5, None]:
    doc = {
        "schema_version": "1.0",
        "org_id": "org-123",
        "limit": 100,
        "window_seconds": value,
    }
    try:
        validate_policy(doc)
    except PolicySchemaError as err:
        assert err.code == "invalid_window", (value, err.code)
        assert err.field == "window_seconds", (value, err.field)
    else:
        raise AssertionError("accepted invalid window: %r" % (value,))
PY
}

# eval-4: missing, empty, and unsupported schema versions are rejected instead of defaulted
eval_4() {
  PYTHONPATH=src python3 - <<'PY'
from policy.schema import (
    SUPPORTED_SCHEMA_VERSIONS,
    PolicySchemaError,
    validate_policy,
)

assert tuple(SUPPORTED_SCHEMA_VERSIONS) == ("1.0",), SUPPORTED_SCHEMA_VERSIONS

MISSING = object()
for value in ["", "0.9", "2.0", "1", 1.0, None, MISSING]:
    doc = {"org_id": "org-123", "limit": 100, "window_seconds": 60}
    if value is not MISSING:
        doc["schema_version"] = value
    try:
        validate_policy(doc)
    except PolicySchemaError as err:
        assert err.code == "unsupported_schema_version", (value, err.code)
        assert err.field == "schema_version", (value, err.field)
    else:
        raise AssertionError("accepted schema version: %r" % (value,))
PY
}

# eval-5: the module's own unit tests exist and pass
eval_5() {
  test -f tests/test_policy_schema.py || return 1
  PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_policy_schema*.py'
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
    description: a supported-version document with an in-domain limit and window normalizes
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 10
  - id: eval_2
    description: every out-of-domain limit is rejected with code invalid_limit on field limit
    runnable: bash
    check_type: deterministic
    verifies: [B-2]
    terminal: true
    expected_duration_sec: 10
  - id: eval_3
    description: every out-of-domain window is rejected with code invalid_window on field window_seconds
    runnable: bash
    check_type: deterministic
    verifies: [B-3]
    terminal: true
    expected_duration_sec: 10
  - id: eval_4
    description: missing, empty, and unsupported schema versions are rejected instead of defaulted
    runnable: bash
    check_type: deterministic
    verifies: [B-4]
    terminal: true
    expected_duration_sec: 10
  - id: eval_5
    description: the module's own unit tests exist and pass
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2, B-3, B-4]
    terminal: true
    expected_duration_sec: 30

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
  output_artifacts: []
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
eval_1 && eval_2 && eval_3 && eval_4 && eval_5
```

---

## Rollback Plan

If execution fails mid-task, revert to the pre-task state:

1. **Git revert** — `git revert --no-commit HEAD` (if commits were made)
2. **File restore** — `git checkout -- <paths>` for any modified files not yet committed
3. **State reset** — update task status to `parked` and record `blocked_reason`

This task is purely additive: `rm -rf src/policy tests/test_policy_schema.py`
restores the prior state exactly, because nothing else in the repository imports
the module.

---

## Observability Hooks

(none — no runtime observability required. This atom is a pure validation
boundary with no runtime emission; decision telemetry is step 4 of the steel
thread.)

---

## Anti-Patterns

- **Don't default an absent or empty `schema_version` to the current version** — a document with no declared version would then be silently reinterpreted whenever the schema changes, which is exactly the failure versioning exists to prevent. Reject it with `unsupported_schema_version`.
- **Don't accept `bool` as an `int` limit or window** — `isinstance(True, int)` is `True` in Python, so a naive type check admits `True` as the limit `1`. Exclude `bool` explicitly before the range check.
- **Don't coerce numeric strings or floats** — calling `int("100")` or `int(1.5)` turns a malformed document into a plausible-looking policy. `"100"` and `1.5` are rejections, not inputs.
- **Don't raise bare `ValueError` or return a bool** — later steel-thread steps branch on the stable `code` and `field`, so the error type must carry both attributes.
- **Don't add a YAML, `pydantic`, or `jsonschema` dependency** — the evals must run offline against the stdlib in a repository with no package manifest.
- **Don't widen into policy resolution, request counting, denial, or decision telemetry** — those are steps 2–4 of the steel thread and belong to separate atoms.

---

## Do-Not-Touch

Files the executor MUST NOT modify:

- `tests/fixtures/toolkit/blueprint.md` (the sealed evidence fixture — it is hashed)
- `.taskspec/`
- `.agents/`
- `.claude/`
- `tasks/`

---

## Open Questions

Things the executor should resolve DURING build, not assume:

(none — this task is fully specified. The domain bounds, supported version set,
and error codes are declared in Context and pinned by the evals; anything the
reviewer wants changed should change this spec before the gate, not during
execution.)
