# Proposed rate-limiting steel thread

Provider-owned usage metering remains provider-owned and out of scope; rate-limit counters and decision telemetry do not become usage or billing records.
Production storage and deployment infrastructure are not selected here.
This is synthetic fixture intent, not evidence of shipped behavior.
Propose only: no approval, compilation, task materialization, signing, execution, acceptance, commit, or publication.

## Original intake

Turn the problem in tests/fixtures/toolkit/blueprint.md into a proposed plan. Preserve the stated ownership and metering boundary. Do not approve or execute it.

## Source

# Rate-limiting steel thread (test evidence fixture)

Synthetic evidence source for `rate-limiting-recipe.yaml`. It exists so the
proving fixture has a real local file to hash, and so source verification,
digest mismatch, and tamper rejection can be exercised without depending on
a large binary document.

## Steel thread order

1. A versioned policy schema rejects invalid limits and windows.
2. Resolution produces exactly one effective policy for an organization.
3. Request 101 is denied after 100 allowed requests in the same window.
4. The denial returns a stable reason and emits matching decision telemetry.

## Boundaries

- Provider-owned usage metering is out of scope.
- Production storage and deployment infrastructure are not selected here.

This file is fixture input. It is not documentation of shipped behavior.

## Ownership

Unassigned: the blueprint does not name an in-scope owner. Resolve ownership before approval; do not assign provider-owned metering to this work.
