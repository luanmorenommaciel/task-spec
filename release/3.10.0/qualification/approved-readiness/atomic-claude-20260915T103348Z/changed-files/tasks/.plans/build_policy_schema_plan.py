#!/usr/bin/env python3
"""Author tasks/.plans/policy-schema.json.

The TaskPlan is written as JSON so each eval can carry a real multi-line
script: the portable YAML manifest reader does not accept block scalars.

Two rendering constraints shape the eval bodies:
  * the spec renderer indents every command line by two spaces inside the
    generated ``eval_N()`` function, so the script is wrapped in
    ``python3 -c 'if 1: ...'`` — a uniform extra indent stays valid Python,
    while a heredoc terminator would not survive the shift;
  * the script is single-quoted for bash, so it must contain no apostrophe.
"""

import json
import pathlib

PREAMBLE = """set -euo pipefail
python3 -c 'if 1:
    import sys

    sys.path.insert(0, "src")
    from ratelimit.policy_schema import (
        SCHEMA_VERSION,
        PolicyValidationError,
        parse_policy,
    )

    VALID = {"schema_version": 1, "org_id": "acme", "limit": 100, "window_seconds": 60}
"""

CLOSE = "'\n"


def eval_body(body: str) -> str:
    if "'" in body:
        raise SystemExit("eval body must not contain an apostrophe: it is bash-single-quoted")
    return PREAMBLE + body + CLOSE


EVAL_1 = eval_body("""
    assert SCHEMA_VERSION == 1, "SCHEMA_VERSION must be the supported integer version 1"

    policy = parse_policy(VALID)
    assert isinstance(policy, dict), "parse_policy must return a normalized mapping"
    for key, want in VALID.items():
        assert policy[key] == want, f"{key} must round-trip unchanged, got {policy.get(key)!r}"

    # Normalization is idempotent: re-parsing an accepted policy is a no-op.
    assert parse_policy(policy) == policy, "parse_policy must be idempotent on accepted policies"

    # The accepted policy must not alias caller-owned state.
    mutated = dict(VALID)
    parsed = parse_policy(mutated)
    mutated["limit"] = 999
    assert parsed["limit"] == 100, "parse_policy must not alias the caller mapping"
    print("eval_1 ok")
""")

EVAL_2 = eval_body("""
    # Guard: a reject-everything stub must not pass this eval.
    assert parse_policy(VALID)["limit"] == 100, "the canonical valid policy must still be accepted"

    cases = [
        ("zero", 0),
        ("negative", -1),
        ("float", 1.5),
        ("string", "100"),
        ("none", None),
        ("bool", True),
        ("above_max", 1_000_001),
    ]
    codes = {}
    for label, bad in cases:
        try:
            parse_policy(dict(VALID, limit=bad))
        except PolicyValidationError as err:
            assert err.field == "limit", f"limit={bad!r} must report field limit, got {err.field!r}"
            assert isinstance(err.code, str) and err.code, f"limit={bad!r} must carry a stable code"
            codes[label] = err.code
        else:
            raise AssertionError(f"limit={bad!r} must be rejected")

    # Distinct failure kinds carry distinct codes, so one blanket code fails here.
    assert codes["zero"] != codes["float"], "non-positive and non-integer limits need distinct codes"
    assert codes["above_max"] not in (codes["zero"], codes["float"]), (
        "an above-maximum limit needs its own stable code"
    )
    # The same failure kind reuses one stable code.
    assert codes["zero"] == codes["negative"], "every non-positive limit must share one code"
    assert codes["float"] == codes["string"] == codes["none"] == codes["bool"], (
        "every non-integer limit must share one code"
    )
    print("eval_2 ok")
""")

EVAL_3 = eval_body("""
    # Guard: a reject-everything stub must not pass this eval.
    assert parse_policy(VALID)["window_seconds"] == 60, "the canonical valid policy must still be accepted"

    cases = [
        ("zero", 0),
        ("negative", -5),
        ("float", 1.5),
        ("string", "60"),
        ("none", None),
        ("bool", True),
        ("above_max", 86_401),
    ]
    codes = {}
    for label, bad in cases:
        try:
            parse_policy(dict(VALID, window_seconds=bad))
        except PolicyValidationError as err:
            assert err.field == "window_seconds", (
                f"window_seconds={bad!r} must report field window_seconds, got {err.field!r}"
            )
            assert isinstance(err.code, str) and err.code, (
                f"window_seconds={bad!r} must carry a stable code"
            )
            codes[label] = err.code
        else:
            raise AssertionError(f"window_seconds={bad!r} must be rejected")

    assert codes["zero"] != codes["float"], "non-positive and non-integer windows need distinct codes"
    assert codes["above_max"] not in (codes["zero"], codes["float"]), (
        "an above-maximum window needs its own stable code"
    )

    # The schema is versioned: an unsupported version is rejected by version, not by field values.
    try:
        parse_policy(dict(VALID, schema_version=999))
    except PolicyValidationError as err:
        assert err.field == "schema_version", f"expected field schema_version, got {err.field!r}"
        assert err.code == "unsupported_schema_version", f"unexpected code {err.code!r}"
    else:
        raise AssertionError("schema_version=999 must be rejected")

    # Rejection is deterministic: identical input yields an identical code.
    def code_for(candidate):
        try:
            parse_policy(candidate)
        except PolicyValidationError as err:
            return err.code
        raise AssertionError(f"{candidate!r} must be rejected")

    first = code_for(dict(VALID, window_seconds=0))
    second = code_for(dict(VALID, window_seconds=0))
    assert first == second, "rejection codes must be deterministic across calls"
    print("eval_3 ok")
""")

plan = {
    "api_version": "taskspec.dev/v1",
    "kind": "TaskPlan",
    "approved": True,
    "metadata": {
        "name": "versioned-rate-limit-policy-schema",
        "source": "tests/fixtures/toolkit/blueprint.md",
    },
    "units": [
        {
            "id": "T-20260915-policy-schema-versioned",
            "title": "Add a versioned rate-limit policy schema that rejects invalid limits and windows",
            "effort": "S",
            "profile": "standard",
            "agent": "any",
            "execution_backend": "any",
            "required_tools": ["python3"],
            "depends_on": [],
            "touches_paths": [],
            "creates_paths": [
                "src/ratelimit/__init__.py",
                "src/ratelimit/policy_schema.py",
            ],
            "source_note": "tests/fixtures/toolkit/blueprint.md",
            "why": (
                "Step 1 of the rate-limiting steel thread. Policy resolution, enforcement, "
                "and decision telemetry all read a policy; without a versioned schema that "
                "rejects invalid limits and windows at the boundary, every later step "
                "inherits unvalidated input and there is no stable rejection contract to "
                "build resolution on."
            ),
            "goal": (
                "Ship src/ratelimit/policy_schema.py exposing SCHEMA_VERSION, "
                "PolicyValidationError(field, code), and parse_policy(mapping) -> dict. "
                "parse_policy accepts a well-formed versioned policy and returns it "
                "normalized; it raises PolicyValidationError with a stable field and code "
                "for an unsupported schema version, a non-positive / non-integer / "
                "above-maximum limit, or a non-positive / non-integer / above-maximum "
                "window_seconds."
            ),
            "done_condition": (
                "parse_policy accepts the canonical valid policy and rejects every declared "
                "invalid limit, window, and schema version with a stable field and code, "
                "proven by eval_1 through eval_3."
            ),
            "context": (
                "The blueprint fixture (tests/fixtures/toolkit/blueprint.md) orders the steel "
                "thread: (1) versioned schema, (2) one effective policy per organization, "
                "(3) request 101 denied after 100 allowed, (4) stable denial reason plus "
                "decision telemetry. This task owns step 1 only. Bounds: limit is an int in "
                "1..1_000_000; window_seconds is an int in 1..86_400; bool is not an integer "
                "here. The repository has no application code yet, so this task creates the "
                "src/ratelimit package. Python 3 with the standard library only — no "
                "dependency may be added. Accepted policy fields are schema_version, org_id, "
                "limit, window_seconds."
            ),
            "behaviors": [
                {
                    "id": "B-1",
                    "given": "a policy mapping with a supported schema_version and in-range limit and window",
                    "when": "parse_policy is called with it",
                    "then": "it returns a normalized policy whose fields round-trip unchanged, and re-parsing that result is a no-op",
                },
                {
                    "id": "B-2",
                    "given": "a policy whose limit is non-positive, non-integer, or above the maximum",
                    "when": "parse_policy is called with it",
                    "then": "it raises PolicyValidationError with field 'limit' and a stable code that distinguishes the failure kind",
                },
                {
                    "id": "B-3",
                    "given": "a policy whose window_seconds is non-positive, non-integer, or above the maximum, or whose schema_version is unsupported",
                    "when": "parse_policy is called with it",
                    "then": "it raises PolicyValidationError naming the offending field with a stable, deterministic code",
                },
            ],
            "evals": [
                {
                    "id": "eval_1",
                    "description": "a well-formed versioned policy is accepted, normalized, and idempotent under re-parse",
                    "command": EVAL_1,
                    "verifies": ["B-1"],
                    "expected_duration_sec": 10,
                },
                {
                    "id": "eval_2",
                    "description": "invalid limits are rejected with field 'limit' and stable per-kind codes, while the valid policy is still accepted",
                    "command": EVAL_2,
                    "verifies": ["B-2"],
                    "expected_duration_sec": 10,
                },
                {
                    "id": "eval_3",
                    "description": "invalid windows and unsupported schema versions are rejected with stable deterministic codes, while the valid policy is still accepted",
                    "command": EVAL_3,
                    "verifies": ["B-3"],
                    "terminal": True,
                    "expected_duration_sec": 10,
                },
            ],
            "anti_patterns": [
                "Do not implement policy resolution, precedence, or an effective-policy lookup — that is steel-thread step 2, a separate task.",
                "Do not implement counting, quota enforcement, or the request-101 denial — that is step 3.",
                "Do not emit decision telemetry or define the denial reason surface — that is step 4.",
                "Do not model provider-owned usage metering, storage backends, or deployment infrastructure; the blueprint puts them out of scope.",
                "Do not add a third-party dependency (pydantic, jsonschema, attrs); standard library only.",
                "Do not raise bare ValueError, KeyError, or TypeError out of parse_policy — every rejection must be a PolicyValidationError carrying field and code.",
                "Do not accept bool as an integer limit or window; True must be rejected as non-integer.",
                "Do not weaken or edit the sealed evals to make an attempt pass.",
            ],
            "do_not_touch": [
                "tests/fixtures/toolkit/blueprint.md",
                "tasks/",
                ".taskspec/",
            ],
            "rollback": (
                "Delete the created src/ratelimit package. The task adds new files only and "
                "no existing file or caller depends on them yet, so removal restores the "
                "prior tree exactly."
            ),
            "observability": (
                "None in this task. Rejections surface only as PolicyValidationError with a "
                "stable field and code; wiring those codes into decision telemetry is "
                "steel-thread step 4."
            ),
        }
    ],
}

out = pathlib.Path(__file__).resolve().parent / "policy-schema.json"
out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
print(f"wrote {out}")
