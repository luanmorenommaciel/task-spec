---
schema_version: 1
kind: system-map
claim: proposed
components:
- versioned rate-limit policy schema
- effective policy resolver for an organization
- window counter behind a storage port
- admission decision function
- stable denial reason enumeration
- decision telemetry emitter
external_dependencies:
- provider-owned usage metering (out of scope; boundary only)
- production storage backend (not selected by this plan)
- deployment infrastructure (not selected by this plan)
unknowns: []
proposed_steel_thread:
- LEG-POLICY-SCHEMA
- LEG-POLICY-RESOLUTION
- LEG-WINDOW-COUNTER
- LEG-ADMISSION-DECISION
- LEG-DENIAL-REASON
- LEG-DECISION-TELEMETRY
- LEG-THREAD-PROOF
objections:
- id: OBJ-OWNER-MISSING
  status: ACCEPTED
  summary: No responsible owner is recorded in the source fixture, so every seam and swimlane owner is
    the literal string 'UNASSIGNED placeholder'.
  owner: pending human assignment at plan review
  rationale: 'Accepted only for the purpose of proposing a topology. Ownership is a product decision and
    is not invented here: the placeholder text is carried verbatim into the projected artifacts, and review
    must replace it with a real owner before any leaf is sealed.'
- id: OBJ-TOOLCHAIN-PROPOSED
  status: ACCEPTED
  summary: Python 3 and pytest under src/rate_limiting and tests/rate_limiting are proposed, not evidenced;
    the repository has no implementation language or test runner.
  owner: pending human assignment at plan review
  rationale: Accepted as a recorded proposal because evals must be executable commands. DEC-TOOLCHAIN
    remains status 'proposed'; if review chooses another toolchain, every eval command and every path
    in the recipe changes and the plan must be replanned rather than patched.
- id: OBJ-WINDOW-SEMANTICS
  status: ACCEPTED
  summary: Fixed-window semantics with an injected clock are inferred from the source phrase 'same window';
    sliding-window behavior is neither stated nor ruled out.
  owner: pending human assignment at plan review
  rationale: Accepted as the minimal reading of the source and recorded in DEC-FIXED-WINDOW with status
    'proposed'. A sliding-window requirement changes the counter leaf, its evals, and the boundary assertions
    in the integration proof.
- id: OBJ-METERING-BOUNDARY
  status: ACCEPTED
  summary: Provider-owned usage metering stays out of scope; no leaf reads, writes, or emits into metering.
  owner: provider (metering remains provider-owned per the source fixture)
  rationale: The boundary is stated directly by the source and is carried into every leaf as an anti-pattern
    and a do_not_touch entry rather than left as prose.
contentions:
- between:
  - T-20260915-denial-reason
  - T-20260915-decision-telemetry
  resolution: Both leaves edit src/rate_limiting/limiter.py, so they are serialized on that file; the
    reason enumeration must exist before telemetry can emit a matching reason field.
  order:
  - T-20260915-denial-reason
  - T-20260915-decision-telemetry
---
# System Map

## Components

- versioned rate-limit policy schema
- effective policy resolver for an organization
- window counter behind a storage port
- admission decision function
- stable denial reason enumeration
- decision telemetry emitter

## External dependencies

- provider-owned usage metering (out of scope; boundary only)
- production storage backend (not selected by this plan)
- deployment infrastructure (not selected by this plan)

## Unknowns

- (none)

This is a **proposed** map. The delivery-plan transformation must
close or gate every material unknown; it may not reinterpret this text as
runtime proof.
