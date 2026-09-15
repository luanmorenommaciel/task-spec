# Candidate intent

Outcome: a rate-limiting steel thread in which a versioned policy schema rejects
invalid limits and windows, policy resolution yields exactly one effective policy
per organization, request 101 is denied after 100 allowed requests in the same
window, and the denial carries a stable reason with matching decision telemetry.

Evidence: tests/fixtures/toolkit/blueprint.md at
sha256:f40ed16c2898b8363dfce1c19e7c3fd539d52810d52b21faeaf59323117af445,
captured 2026-09-15. The file declares itself fixture input and explicitly not
documentation of shipped behavior, so every statement drawn from it is a proposed
requirement, not observed current behavior.

Constraints: provider-owned usage metering stays out of scope and is not
reimplemented, wrapped, or corrected by this work; production storage and
deployment infrastructure are not selected here, so the steel thread must prove
itself against a substitutable in-process store behind an explicit boundary.

Owner: NOT STATED in the evidence source. The blueprint names a boundary owner
(the provider, for usage metering) but never names a responsible owner for the
rate-limiting work itself. This is unresolved and is not to be inferred.

Unknowns: responsible owner for every seam and swimlane; the implementation
language and test runner for the steel thread; the persistence contract that
production storage must later satisfy.
