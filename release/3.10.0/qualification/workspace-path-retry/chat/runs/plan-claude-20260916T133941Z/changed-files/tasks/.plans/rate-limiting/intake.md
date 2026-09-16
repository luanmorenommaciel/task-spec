# Candidate intent

Outcome: an organization-scoped request rate limit that resolves exactly one
effective policy, denies request 101 after 100 allowed requests in the same
window, and emits a stable denial reason with matching decision telemetry.

Evidence: tests/fixtures/toolkit/blueprint.md at
sha256:f40ed16c2898b8363dfce1c19e7c3fd539d52810d52b21faeaf59323117af445,
captured 2026-09-16T13:40:45Z. The file declares itself fixture input, not
documentation of shipped behavior, so every claim derived from it is proposed
rather than observed in this repository.

Constraints: provider-owned usage metering stays out of scope and is not
reimplemented, wrapped, or corrected here. Production storage and deployment
infrastructure are not selected by this initiative.

Owner: not stated in the source blueprint. Unresolved.

Unknowns: the responsible owner for each seam; the window accounting semantics
(fixed or sliding); the policy storage and resolution substrate, which is
deliberately unselected; the telemetry sink the decision events are emitted to.
