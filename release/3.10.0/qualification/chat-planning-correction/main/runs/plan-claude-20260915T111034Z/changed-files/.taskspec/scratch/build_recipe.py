import json

SRC = {
    "uri": "tests/fixtures/toolkit/blueprint.md",
    "captured_at": "2026-09-15T00:00:00Z",
    "sha256": "f40ed16c2898b8363dfce1c19e7c3fd539d52810d52b21faeaf59323117af445",
}
UNOWNED = "UNASSIGNED (no owner named in tests/fixtures/toolkit/blueprint.md)"

NO_METERING = "provider-owned usage metering: do not read, wrap, reimplement, or correct it"
NO_INFRA = "production storage and deployment infrastructure selection"
NO_FIXTURE = "tests/fixtures/toolkit/blueprint.md (evidence source, not an editable artifact)"

def guard_eval(eid, path, verifies):
    return {
        "id": eid,
        "description": "Metering boundary holds: no usage-metering symbol is referenced from the new code.",
        "bash": "! grep -rniE 'meter|metering|usage_record|usage_event' " + path,
        "verifies": verifies,
    }

def unit(eid, desc, pattern, verifies):
    return {
        "id": eid,
        "description": desc,
        "bash": "python3 -m unittest discover -s tests/ratelimit -p '" + pattern + "' -v",
        "verifies": verifies,
    }

def task(tid, title, goal, done, effort, deps, touches, creates, behaviors, evals,
         anti, dnt, recipe, shared=None, proves=None, stages=None, rollback=None, obs=None):
    t = {
        "id": tid, "title": title, "goal": goal, "done_condition": done,
        "effort": effort, "profile": "standard", "execution_backend": "local",
        "required_tools": ["python3"], "depends_on": deps,
        "touches_paths": touches, "creates_paths": creates,
        "behavior": behaviors, "evals": evals, "anti_patterns": anti,
        "do_not_touch": dnt, "execution_recipe": recipe,
    }
    if shared: t["shared_resources"] = shared
    if proves: t["proves_capabilities"] = proves
    if stages: t["sdlc_stages"] = stages
    if rollback: t["rollback"] = rollback
    if obs: t["observability"] = obs
    return t

AP_METER = {
    "action": "Call or emulate the provider usage-metering API to obtain counts.",
    "reason": "The blueprint places provider-owned usage metering outside this scope; consuming it silently moves the boundary.",
    "instead": "Count only within this component's own window store and leave metering untouched.",
}
AP_INFRA = {
    "action": "Select a production database, cache, or deployment target to satisfy an eval.",
    "reason": "The blueprint states production storage and deployment infrastructure are not selected here.",
    "instead": "Prove the behavior against the in-process store behind the declared boundary and leave selection to a later authorized decision.",
}
AP_FIXTURE = {
    "action": "Edit tests/fixtures/toolkit/blueprint.md to match the implementation.",
    "reason": "The blueprint is the hashed evidence source; editing it invalidates the recipe digest and the intent-to-leaf chain.",
    "instead": "Raise an objection and request an explicit decision when implementation and evidence disagree.",
}
AP_WINDOW = {
    "action": "Pick fixed or sliding window semantics unilaterally to make the 101st-request eval pass.",
    "reason": "Window semantics is an unresolved product decision recorded as OPEN objection OBJ-WINDOW-SEMANTICS.",
    "instead": "Stop and surface the decision to the seam owner once one is assigned.",
}
AP_SCHEMA_SKIP = {
    "action": "Accept an unversioned policy payload so downstream tasks can start earlier.",
    "reason": "The first steel-thread step requires a versioned schema that rejects invalid limits and windows.",
    "instead": "Keep rejection strict and let downstream work depend on the sealed schema.",
}
AP_MULTI = {
    "action": "Return the first matching policy and ignore the rest when several apply to one organization.",
    "reason": "Step 2 requires exactly one effective policy, so ambiguity must fail loudly rather than resolve arbitrarily.",
    "instead": "Raise a deterministic ambiguity error and record the conflicting policy identifiers.",
}
AP_REASON = {
    "action": "Return a formatted human message as the denial reason.",
    "reason": "Step 4 requires a stable reason that telemetry can be matched against; prose drifts between releases.",
    "instead": "Return a stable machine reason code and keep any human text as a separate field.",
}
AP_TELEMETRY_DRIFT = {
    "action": "Emit telemetry from a second code path that recomputes the decision.",
    "reason": "A recomputed event can disagree with the returned denial, breaking the 'matching' requirement.",
    "instead": "Emit from the single decision result so reason and telemetry cannot diverge.",
}
AP_PROOF_STUB = {
    "action": "Stub a lower layer inside the end-to-end proof to keep it green.",
    "reason": "The proof leaf exists to evaluate the assembled legs; stubbing removes the only integration evidence.",
    "instead": "Let the proof fail and repair the responsible leg.",
}

tasks = {}

tasks["schema"] = task(
    "T-20260915-policy-schema-validation",
    "Versioned rate-limit policy schema rejecting invalid limits and windows",
    "Define a versioned policy schema and a validator that rejects invalid limit and window values, establishing steel-thread step 1.",
    "A versioned schema module exists, accepts a documented valid policy, and rejects non-positive, non-integer, and missing limit or window values with a deterministic error naming the offending field.",
    "M", [],
    [],
    ["src/ratelimit/__init__.py", "src/ratelimit/policy_schema.py", "tests/ratelimit/test_policy_schema.py"],
    [
        {"id": "B-1", "given": "a policy payload declaring a supported schema version with a positive integer limit and a positive window",
         "when": "the validator runs", "then": "validation succeeds and the parsed policy reports its schema version"},
        {"id": "B-2", "given": "a policy payload whose limit or window is zero, negative, non-integer, or absent",
         "when": "the validator runs", "then": "validation fails with a deterministic error identifying the offending field, and no policy object is produced"},
    ],
    [
        unit("eval_1", "Valid versioned policies parse and report their schema version.", "test_policy_schema*.py", ["B-1"]),
        unit("eval_2", "Invalid limits and windows are rejected with field-identifying errors.", "test_policy_schema_rejects*.py", ["B-2"]),
        guard_eval("eval_3", "src/ratelimit/policy_schema.py", ["B-1", "B-2"]),
    ],
    [AP_SCHEMA_SKIP, AP_FIXTURE, AP_METER],
    [NO_METERING, NO_INFRA, NO_FIXTURE],
    "test-first", shared=["src/ratelimit/__init__.py"], stages=["design", "build", "test"],
    rollback="Delete src/ratelimit/policy_schema.py and tests/ratelimit/test_policy_schema.py; no other module imports them yet.",
)

tasks["resolve"] = task(
    "T-20260915-effective-policy-resolution",
    "Resolution to exactly one effective policy per organization",
    "Resolve any set of candidate policies for an organization to exactly one effective policy, establishing steel-thread step 2.",
    "Resolution returns exactly one validated effective policy for an organization, fails deterministically when candidates are ambiguous, and fails deterministically when none apply.",
    "M", ["T-20260915-policy-schema-validation"],
    ["src/ratelimit/__init__.py"],
    ["src/ratelimit/resolution.py", "tests/ratelimit/test_resolution.py"],
    [
        {"id": "B-1", "given": "one or more candidate policies that validate against the versioned schema for a single organization",
         "when": "resolution runs for that organization", "then": "exactly one effective policy is returned and the same input always yields the same result"},
        {"id": "B-2", "given": "candidate policies that leave the organization with no applicable policy or with two equally applicable policies",
         "when": "resolution runs", "then": "resolution fails with a distinct deterministic error per case and never returns an arbitrary winner"},
    ],
    [
        unit("eval_1", "Resolution yields exactly one effective policy and is deterministic across repeated runs.", "test_resolution*.py", ["B-1"]),
        unit("eval_2", "Empty and ambiguous candidate sets fail with distinct deterministic errors.", "test_resolution_conflicts*.py", ["B-2"]),
        guard_eval("eval_3", "src/ratelimit/resolution.py", ["B-1", "B-2"]),
    ],
    [AP_MULTI, AP_METER, AP_INFRA],
    [NO_METERING, NO_INFRA, NO_FIXTURE, "src/ratelimit/policy_schema.py (sealed by the upstream leaf)"],
    "test-first", shared=["src/ratelimit/__init__.py"], stages=["build", "test"],
    rollback="Delete src/ratelimit/resolution.py and tests/ratelimit/test_resolution.py; the schema leaf remains independently proven.",
)

tasks["store"] = task(
    "T-20260915-window-counter-store",
    "In-process window counter behind a substitutable store boundary",
    "Provide a window-scoped request counter behind an explicit store interface so the steel thread proves without selecting production storage.",
    "A store interface and an in-process implementation exist, count requests within a window key, and no production storage backend is introduced or configured.",
    "M", ["T-20260915-policy-schema-validation"],
    ["src/ratelimit/__init__.py"],
    ["src/ratelimit/store.py", "tests/ratelimit/test_store.py"],
    [
        {"id": "B-1", "given": "an in-process store and a window key",
         "when": "requests are recorded against that key", "then": "the observed count increases by exactly one per recorded request and is readable without mutating it"},
        {"id": "B-2", "given": "two distinct window keys",
         "when": "requests are recorded against one of them", "then": "the other key's count is unchanged, so windows and organizations do not share counters"},
    ],
    [
        unit("eval_1", "Recording requests increments the window count exactly once per request.", "test_store*.py", ["B-1"]),
        unit("eval_2", "Counts are isolated across distinct window keys.", "test_store_isolation*.py", ["B-2"]),
        guard_eval("eval_3", "src/ratelimit/store.py", ["B-1", "B-2"]),
    ],
    [AP_INFRA, AP_METER, AP_FIXTURE],
    [NO_METERING, NO_INFRA, NO_FIXTURE],
    "test-first", shared=["src/ratelimit/__init__.py"], stages=["design", "build", "test"],
    rollback="Delete src/ratelimit/store.py and tests/ratelimit/test_store.py.",
    obs="Store exposes read-only count inspection for the decision leaf; it emits no telemetry of its own.",
)

tasks["decide"] = task(
    "T-20260915-limit-decision-boundary",
    "Allow the first 100 requests and deny request 101 in the same window",
    "Combine the effective policy and the window counter into a decision function that allows up to the limit and denies the next request in the same window, establishing steel-thread step 3.",
    "Given an effective policy with limit 100, the first 100 requests in one window are allowed and the 101st in that same window is denied, with the decision returning a structured result rather than raising.",
    "M", ["T-20260915-effective-policy-resolution", "T-20260915-window-counter-store"],
    ["src/ratelimit/__init__.py"],
    ["src/ratelimit/decision.py", "tests/ratelimit/test_decision.py"],
    [
        {"id": "B-1", "given": "an effective policy with limit 100 and an empty window",
         "when": "100 requests are evaluated in that window", "then": "every one is allowed and the recorded count reaches exactly 100"},
        {"id": "B-2", "given": "a window in which 100 requests have already been allowed under a limit of 100",
         "when": "request 101 is evaluated in the same window", "then": "it is denied and the allowed count does not increase past the limit"},
    ],
    [
        unit("eval_1", "The first 100 requests in a window are allowed under a limit of 100.", "test_decision_allows*.py", ["B-1"]),
        unit("eval_2", "Request 101 in the same window is denied and the count does not exceed the limit.", "test_decision*.py", ["B-1", "B-2"]),
        guard_eval("eval_3", "src/ratelimit/decision.py", ["B-1", "B-2"]),
    ],
    [AP_WINDOW, AP_METER, AP_INFRA],
    [NO_METERING, NO_INFRA, NO_FIXTURE, "src/ratelimit/resolution.py and src/ratelimit/store.py (sealed by upstream leaves)"],
    "test-first", shared=["src/ratelimit/__init__.py"], stages=["build", "test"],
    rollback="Delete src/ratelimit/decision.py and tests/ratelimit/test_decision.py; upstream leaves stay proven.",
)

tasks["telemetry"] = task(
    "T-20260915-denial-reason-telemetry",
    "Stable denial reason with matching decision telemetry",
    "Give every denial a stable machine reason code and emit one decision telemetry event carrying that same code, establishing steel-thread step 4.",
    "Each denial returns a stable reason code from a closed set, and exactly one decision telemetry event is emitted per evaluated request whose reason field equals the returned code.",
    "M", ["T-20260915-limit-decision-boundary"],
    ["src/ratelimit/decision.py"],
    ["src/ratelimit/telemetry.py", "tests/ratelimit/test_telemetry.py"],
    [
        {"id": "B-1", "given": "a request denied because the window limit is exhausted",
         "when": "the decision is returned", "then": "the reason is a stable code from a closed documented set and does not vary with formatting, locale, or message text"},
        {"id": "B-2", "given": "any evaluated request, allowed or denied",
         "when": "the decision completes", "then": "exactly one decision telemetry event is emitted whose outcome and reason fields equal the returned decision's own fields"},
    ],
    [
        unit("eval_1", "Denial reasons are stable codes drawn from the closed documented set.", "test_telemetry_reason*.py", ["B-1"]),
        unit("eval_2", "Exactly one telemetry event per decision, with fields matching the returned decision.", "test_telemetry*.py", ["B-2"]),
        guard_eval("eval_3", "src/ratelimit/telemetry.py", ["B-1", "B-2"]),
    ],
    [AP_REASON, AP_TELEMETRY_DRIFT, AP_METER],
    [NO_METERING, NO_INFRA, NO_FIXTURE],
    "test-first", stages=["build", "test"],
    rollback="Delete src/ratelimit/telemetry.py and tests/ratelimit/test_telemetry.py and revert the emission call in decision.py.",
    obs="Decision telemetry is this component's own event stream and is explicitly not a usage-metering feed.",
)

tasks["proof"] = task(
    "T-20260915-steel-thread-proof",
    "End-to-end proof of the four-step steel thread in declared order",
    "Evaluate the assembled steel thread in the blueprint's stated order so the four legs are proven together, not only in isolation.",
    "One end-to-end test drives schema validation, resolution, the 100-allow/101-deny boundary, and the matching denial telemetry in order against the in-process store, with no component stubbed.",
    "S", ["T-20260915-denial-reason-telemetry"],
    [],
    ["tests/ratelimit/test_steel_thread.py"],
    [
        {"id": "B-1", "given": "a validated versioned policy with limit 100 resolved to exactly one effective policy for one organization",
         "when": "101 requests are evaluated in one window end to end", "then": "the first 100 are allowed, the 101st is denied, and no component is replaced by a stub"},
        {"id": "B-2", "given": "the denial produced by that end-to-end run",
         "when": "the emitted telemetry is inspected", "then": "its reason equals the stable code returned by the denial, closing the thread from schema to telemetry"},
    ],
    [
        unit("eval_1", "The four steel-thread steps pass in the blueprint's declared order with no stubs.", "test_steel_thread*.py", ["B-1"]),
        unit("eval_2", "End-to-end denial reason and emitted telemetry reason agree.", "test_steel_thread_telemetry*.py", ["B-2"]),
        guard_eval("eval_3", "src/ratelimit/", ["B-1", "B-2"]),
    ],
    [AP_PROOF_STUB, AP_INFRA, AP_METER],
    [NO_METERING, NO_INFRA, NO_FIXTURE, "src/ratelimit/ (the proof observes the assembled legs and does not modify them)"],
    "plan-execute-verify",
    proves=["LEG-SCHEMA-VALIDATION", "LEG-EFFECTIVE-POLICY", "LEG-WINDOW-COUNTER", "LEG-LIMIT-DECISION", "LEG-DENIAL-CONTRACT"],
    stages=["test"],
    rollback="Delete tests/ratelimit/test_steel_thread.py; the individual legs remain independently proven.",
)

recipe = {
  "schema_version": 1,
  "intent": {
    "id": "INT-RATE-LIMITING",
    "title": "Rate-limiting steel thread",
    "summary": ("Deliver the four ordered behaviors the blueprint names: a versioned policy schema that "
                "rejects invalid limits and windows, resolution to exactly one effective policy per "
                "organization, denial of request 101 after 100 allowed requests in the same window, and a "
                "stable denial reason with matching decision telemetry. Provider-owned usage metering "
                "remains outside this work and production storage and deployment infrastructure are not "
                "selected here."),
    "claim": "proposed",
    "source": SRC,
    "success": [
      "A versioned policy schema rejects invalid limits and windows with deterministic, field-identifying errors.",
      "Resolution produces exactly one effective policy for an organization, or fails deterministically rather than choosing arbitrarily.",
      "Request 101 is denied after 100 allowed requests in the same window.",
      "The denial returns a stable reason code and emits matching decision telemetry.",
      "The four steps are proven together in the blueprint's declared order against a substitutable in-process store.",
    ],
    "out_of_scope": [
      "Provider-owned usage metering, which the blueprint places outside this work and which this plan does not read, wrap, reimplement, or correct.",
      "Selection of production storage, which the blueprint explicitly does not decide here.",
      "Selection of deployment infrastructure, which the blueprint explicitly does not decide here.",
      "Any claim that the blueprint documents shipped behavior; it declares itself fixture input.",
    ],
  },
  "system_map": {
    "claim": "derived",
    "components": [
      "Versioned rate-limit policy schema and validator",
      "Policy resolution producing one effective policy per organization",
      "Window counter behind a substitutable in-process store boundary",
      "Limit decision function returning allow or deny with a stable reason",
      "Decision telemetry emitter owned by this component",
    ],
    "external_dependencies": [
      "Provider-owned usage metering (out of scope boundary; not called, not depended on, and not a source of counts)",
    ],
    "unknowns": [
      "No responsible owner is named anywhere in the evidence source for any seam or swimlane of this work.",
      "Window semantics are unspecified: the blueprint says 'the same window' without stating fixed or sliding.",
      "The counting key is unspecified: organization alone, or organization combined with a caller, route, or credential.",
      "Implementation language and test runner are not stated; python3 is proposed only because it is the verified runtime in this repository.",
      "The persistence contract that a later production store must satisfy (durability, atomic increment, concurrent callers) is undecided because storage selection is explicitly deferred.",
      "Whether allowed requests also emit decision telemetry, or only denials, is not stated.",
    ],
  },
  "evidence": [
    {"id": "EV-STEEL-THREAD", "claim": "proposed", "source": SRC, "confidence": 0.9,
     "summary": "The blueprint states four ordered steel-thread steps: versioned schema rejecting invalid limits and windows, resolution to exactly one effective policy per organization, denial of request 101 after 100 allowed in the same window, and a stable denial reason with matching decision telemetry."},
    {"id": "EV-SCOPE-BOUNDARY", "claim": "proposed", "source": SRC, "confidence": 0.95,
     "summary": "The blueprint's Boundaries section places provider-owned usage metering out of scope and states that production storage and deployment infrastructure are not selected here."},
    {"id": "EV-FIXTURE-STATUS", "claim": "proposed", "source": SRC, "confidence": 0.95,
     "summary": "The blueprint declares itself fixture input and explicitly not documentation of shipped behavior, so its steps are proposed requirements and no current-state behavior may be claimed from it."},
    {"id": "EV-OWNER-ABSENT", "claim": "derived", "source": SRC, "confidence": 0.9,
     "summary": "Derived by reading the whole evidence source: it names the provider as owner of out-of-scope metering but names no responsible owner for the rate-limiting work, so seam and swimlane ownership is unresolved."},
    {"id": "EV-NO-IMPLEMENTATION", "claim": "derived", "source": SRC, "confidence": 0.85,
     "summary": "Derived from repository inspection alongside the fixture: the backlog is empty and no rate-limiting source exists, so all four steps are greenfield and no current behavior is being modified."},
  ],
  "decisions": [
    {"id": "DEC-SUBSTITUTABLE-STORE", "status": "proposed", "owner": UNOWNED,
     "rationale": "Prove the window counter against an in-process store behind an explicit interface. This is the minimum that lets steps 3 and 4 be proven while honoring the blueprint's statement that production storage is not selected here; it commits to no backend."},
    {"id": "DEC-STABLE-REASON-CODE", "status": "proposed", "owner": UNOWNED,
     "rationale": "Represent the denial reason as a machine code from a closed set, with human text as a separate field, because step 4 requires the reason to be stable and to match telemetry."},
    {"id": "DEC-PYTHON-TEST-RUNNER", "status": "proposed", "owner": UNOWNED,
     "rationale": "Evals are written for python3 unittest because python3 is the only runtime verified present in this repository. No language decision is recorded in the evidence source, so this must be confirmed or replaced before any leaf is sealed."},
  ],
  "seams": [
    {
      "id": "SEAM-POLICY-SCHEMA", "name": "Policy schema and validation",
      "description": "Owns the versioned representation of a rate-limit policy and the rejection of invalid limits and windows. This is step 1 of the steel thread and the only seam that defines what a policy is.",
      "evidence": ["EV-STEEL-THREAD", "EV-FIXTURE-STATUS", "EV-NO-IMPLEMENTATION"],
      "responsibility": "Define and version the policy shape and reject invalid limit and window values deterministically.",
      "consumes": ["candidate policy payloads supplied by callers"],
      "produces": ["validated versioned policy objects", "deterministic field-identifying validation errors"],
      "owner": UNOWNED,
      "independent_proof": "Feed valid and invalid policy payloads directly to the validator; acceptance needs no resolution, counter, or telemetry.",
      "rejected_alternatives": [
        {"alternative": "Validate policies inline at the decision site instead of in a dedicated schema.", "reason": "Step 1 is a distinct steel-thread behavior and would become unprovable without its own rejection surface."},
        {"alternative": "Skip schema versioning and validate shape only.", "reason": "The blueprint names a versioned schema, and unversioned policies cannot later migrate safely."},
      ],
      "swimlane": {"id": "SL-POLICY-SCHEMA", "name": "Policy schema", "owner": UNOWNED, "legs": [
        {"id": "LEG-SCHEMA-VALIDATION",
         "observable_state": "A versioned policy schema accepts valid policies and rejects invalid limits and windows with deterministic, field-identifying errors.",
         "proof": "Unit evals over valid and invalid policy payloads, plus a grep guard proving no metering symbol is referenced.",
         "requires": [], "produces": ["validated versioned policy objects", "deterministic validation errors"],
         "tasks": [tasks["schema"]]},
      ]},
    },
    {
      "id": "SEAM-POLICY-RESOLUTION", "name": "Effective policy resolution",
      "description": "Owns the reduction of candidate policies to exactly one effective policy for an organization. This is step 2 and the only seam that decides which policy applies.",
      "evidence": ["EV-STEEL-THREAD", "EV-FIXTURE-STATUS"],
      "responsibility": "Produce exactly one effective policy per organization, or fail deterministically when none or several apply.",
      "consumes": ["validated versioned policy objects", "an organization identifier"],
      "produces": ["exactly one effective policy per organization", "deterministic ambiguity and no-policy errors"],
      "owner": UNOWNED,
      "independent_proof": "Resolve fixed candidate sets for a fixed organization and assert exactly-one, ambiguous, and empty outcomes; no counting or telemetry is involved.",
      "rejected_alternatives": [
        {"alternative": "Merge overlapping policies into a synthesized effective policy.", "reason": "Merging invents limits nobody authored and hides the ambiguity the blueprint requires be resolved to exactly one."},
        {"alternative": "Let the decision site pick the strictest candidate at request time.", "reason": "That makes 'exactly one effective policy' unobservable and moves a policy decision into the hot path."},
      ],
      "swimlane": {"id": "SL-POLICY-RESOLUTION", "name": "Policy resolution", "owner": UNOWNED, "legs": [
        {"id": "LEG-EFFECTIVE-POLICY",
         "observable_state": "Resolution returns exactly one effective policy for an organization and fails deterministically on ambiguous or empty candidate sets.",
         "proof": "Unit evals over exactly-one, ambiguous, and empty candidate sets, plus the metering grep guard.",
         "requires": ["validated versioned policy objects"], "produces": ["exactly one effective policy per organization"],
         "tasks": [tasks["resolve"]]},
      ]},
    },
    {
      "id": "SEAM-LIMIT-DECISION", "name": "Window counting and limit decision",
      "description": "Owns request counting within a window and the allow/deny decision at the limit. This is step 3 and the seam that carries the storage boundary the blueprint defers.",
      "evidence": ["EV-STEEL-THREAD", "EV-SCOPE-BOUNDARY", "EV-NO-IMPLEMENTATION"],
      "responsibility": "Count requests per window behind a substitutable store and deny the request that exceeds the effective limit.",
      "consumes": ["exactly one effective policy per organization", "evaluated requests"],
      "produces": ["structured allow or deny decisions", "a substitutable window store interface"],
      "owner": UNOWNED,
      "independent_proof": "Drive 101 requests through the decision function against the in-process store with a fixed effective policy; telemetry is not required to assess it.",
      "rejected_alternatives": [
        {"alternative": "Derive counts from provider-owned usage metering.", "reason": "The blueprint places provider-owned usage metering out of scope; sourcing counts from it would move the stated boundary."},
        {"alternative": "Introduce a production cache or database now to make counting realistic.", "reason": "The blueprint states production storage is not selected here, so the steel thread proves against an in-process store behind an interface."},
      ],
      "swimlane": {"id": "SL-DECISION-ENGINE", "name": "Decision engine", "owner": UNOWNED, "legs": [
        {"id": "LEG-WINDOW-COUNTER",
         "observable_state": "An in-process store behind an explicit interface counts requests per window key with counts isolated across keys.",
         "proof": "Unit evals on increment-by-one and cross-key isolation, plus the metering grep guard.",
         "requires": [], "produces": ["a substitutable window store interface", "per-window request counts"],
         "tasks": [tasks["store"]]},
        {"id": "LEG-LIMIT-DECISION",
         "observable_state": "Under a limit of 100, the first 100 requests in a window are allowed and the 101st in that same window is denied.",
         "proof": "Unit evals driving 100 allowed requests and then the 101st denial, plus the metering grep guard.",
         "requires": ["exactly one effective policy per organization", "per-window request counts"],
         "produces": ["structured allow or deny decisions"],
         "tasks": [tasks["decide"]]},
      ]},
    },
    {
      "id": "SEAM-DENIAL-TELEMETRY", "name": "Denial contract and decision telemetry",
      "description": "Owns the stable denial reason and the decision telemetry that must match it. This is step 4 and it also carries the assembled end-to-end proof of the thread.",
      "evidence": ["EV-STEEL-THREAD", "EV-SCOPE-BOUNDARY"],
      "responsibility": "Return a stable machine reason on denial and emit one matching decision telemetry event per decision.",
      "consumes": ["structured allow or deny decisions"],
      "produces": ["stable denial reason codes", "decision telemetry events matching the returned decision", "end-to-end steel-thread evidence"],
      "owner": UNOWNED,
      "independent_proof": "Assert reason-code stability and one-event-per-decision field equality against fixed decision results; the assembled proof leg is evaluated separately.",
      "rejected_alternatives": [
        {"alternative": "Emit decision telemetry into the provider usage-metering stream.", "reason": "That stream is provider-owned and out of scope; decision telemetry is this component's own signal and must not be conflated with metering."},
        {"alternative": "Derive telemetry by re-evaluating the request after the response is returned.", "reason": "A second evaluation can disagree with the returned denial, which breaks the blueprint's requirement that telemetry match."},
      ],
      "swimlane": {"id": "SL-DENIAL-TELEMETRY", "name": "Denial contract and telemetry", "owner": UNOWNED, "legs": [
        {"id": "LEG-DENIAL-CONTRACT",
         "observable_state": "Denials carry a stable reason code from a closed set and each decision emits exactly one telemetry event whose fields equal the returned decision.",
         "proof": "Unit evals on reason-code stability and one-event-per-decision field equality, plus the metering grep guard.",
         "requires": ["structured allow or deny decisions"],
         "produces": ["stable denial reason codes", "decision telemetry events matching the returned decision"],
         "tasks": [tasks["telemetry"]]},
        {"id": "LEG-STEEL-THREAD-PROOF",
         "observable_state": "The four blueprint steps pass together in declared order against the in-process store with no component stubbed.",
         "proof": "One end-to-end eval driving schema, resolution, the 100/101 boundary, and telemetry agreement, plus a repository-wide metering grep guard.",
         "requires": ["stable denial reason codes", "decision telemetry events matching the returned decision", "structured allow or deny decisions"],
         "produces": ["end-to-end steel-thread evidence"],
         "tasks": [tasks["proof"]]},
      ]},
    },
  ],
  "steel_thread": ["LEG-SCHEMA-VALIDATION", "LEG-EFFECTIVE-POLICY", "LEG-WINDOW-COUNTER",
                   "LEG-LIMIT-DECISION", "LEG-DENIAL-CONTRACT", "LEG-STEEL-THREAD-PROOF"],
  "objections": [
    {"id": "OBJ-OWNER-UNASSIGNED", "status": "OPEN",
     "summary": "No responsible owner is named for any seam or swimlane. The evidence source names the provider only as owner of the out-of-scope metering boundary. Every owner field carries an explicit UNASSIGNED marker rather than an inferred team, and no leaf may be sealed until real owners are recorded."},
    {"id": "OBJ-WINDOW-SEMANTICS", "status": "OPEN",
     "summary": "Step 3 says request 101 is denied 'in the same window' without stating whether the window is fixed or sliding. The two choices produce different observable behavior at the boundary and different store contracts. This is a product decision and is not resolved here."},
    {"id": "OBJ-COUNTER-KEY", "status": "OPEN",
     "summary": "The counting key is unspecified. Resolution is per organization, but whether counting is per organization alone or per organization plus caller, route, or credential changes what 'the same window' means. Left open rather than assumed."},
    {"id": "OBJ-TELEMETRY-SCOPE", "status": "OPEN",
     "summary": "Step 4 requires telemetry matching the denial but does not state whether allowed requests also emit decision telemetry. The plan proposes emitting for every decision; this needs an explicit decision because it changes event volume."},
    {"id": "OBJ-STACK-UNSELECTED", "status": "OPEN",
     "summary": "No implementation language or test runner is stated in the evidence source. Evals are authored for python3 unittest solely because python3 is the verified runtime here. DEC-PYTHON-TEST-RUNNER is proposed, not accepted, and the eval commands change if it is replaced."},
    {"id": "OBJ-STORAGE-DEFERRED", "status": "OPEN",
     "summary": "Production storage is deferred by the blueprint itself, so durability, atomic increment, and concurrent-caller behavior are unproven by design. This is a stated boundary rather than an oversight, but it must be accepted knowingly: the steel thread proves logic, not production counting under concurrency."},
  ],
  "contentions": [
    {"between": ["T-20260915-effective-policy-resolution", "T-20260915-window-counter-store"],
     "resolution": "Both leaves register their module in the shared src/ratelimit/__init__.py export surface; serialize them so the two edits cannot interleave.",
     "order": ["T-20260915-effective-policy-resolution", "T-20260915-window-counter-store"]},
  ],
}

with open(".taskspec/scratch/rate-limiting-recipe.yaml", "w") as f:
    json.dump(recipe, f, indent=2)
    f.write("\n")
print("written")
