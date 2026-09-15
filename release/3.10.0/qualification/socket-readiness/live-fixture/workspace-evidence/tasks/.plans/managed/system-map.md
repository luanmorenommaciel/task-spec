---
schema_version: 1
kind: system-map
claim: proposed
components:
- Policy contract boundary
- Effective policy resolver
- Request enforcement boundary
- Decision response and telemetry boundary
external_dependencies:
- Organization identity supplied by the host application
- Time-window and counter state supplied by an implementation-selected adapter
unknowns: []
proposed_steel_thread:
- LEG-POLICY-SCHEMA-VALID
objections:
- id: OBJ-METERING-SEPARATION
  status: FIXED
  summary: Metering was removed from the canonical steel thread and kept external.
  owner: example-fixture
  rationale: The accepted boundary decision leaves metering outside the four-leg proving path.
contentions: []
---
# System Map

## Components

- Policy contract boundary
- Effective policy resolver
- Request enforcement boundary
- Decision response and telemetry boundary

## External dependencies

- Organization identity supplied by the host application
- Time-window and counter state supplied by an implementation-selected adapter

## Unknowns

- (none)

This is a **proposed** map. The delivery-plan transformation must
close or gate every material unknown; it may not reinterpret this text as
runtime proof.
