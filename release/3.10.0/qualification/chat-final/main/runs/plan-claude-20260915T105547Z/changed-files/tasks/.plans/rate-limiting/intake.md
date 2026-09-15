# Rate-limiting steel thread

Outcome: an organization-scoped request rate limiter that admits the first 100
requests in a window and denies request 101 with a stable machine-readable reason,
backed by a versioned policy schema that resolves to exactly one effective policy.

Evidence: tests/fixtures/toolkit/blueprint.md
(sha256 f40ed16c2898b8363dfce1c19e7c3fd539d52810d52b21faeaf59323117af445,
captured 2026-09-15). The file is a synthetic evidence fixture for
`rate-limiting-recipe.yaml`, not documentation of shipped behavior.

Constraints:
- Provider-owned usage metering stays out of scope and keeps its current owner;
  this work consumes metering only as an external boundary and never re-implements,
  reconciles, or bills against it.
- Production storage and deployment infrastructure are not selected here; leaves
  must stay behind a storage port and must not choose a production backend.
- Steel-thread order is fixed by the source: schema validation, single effective
  policy resolution, deny-on-101 enforcement, stable reason plus decision telemetry.

Owner: not recorded in the source fixture. The responsible product owner for the
rate-limiting service is an open blocker; ownership of usage metering remains with
the provider per the source.

Unknowns:
- Implementation language, test runner, and repository layout are unchosen (the
  repository currently contains only fixtures and skill assets).
- Window semantics (fixed vs sliding) and clock source are unstated in the source.
- Telemetry transport and the concrete reason-code vocabulary are unstated.
