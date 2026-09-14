# Rate-limiting steel thread

Outcome: an organization-scoped request rate limiter whose policy is validated,
resolved to exactly one effective policy, enforced at the declared limit, and
observable through a stable denial reason and matching decision telemetry.

Evidence: tests/fixtures/toolkit/blueprint.md at repository revision
70c689863d1a2ea2ba393792bdcd5654b89a8dad,
sha256 f40ed16c2898b8363dfce1c19e7c3fd539d52810d52b21faeaf59323117af445,
captured 2026-09-14T21:43:14Z. The file declares itself fixture input and not
documentation of shipped behavior, so it is intake, not proof of current code.

Constraints:
- Provider-owned usage metering stays out of scope and is not reimplemented,
  mirrored, or reconciled by this work.
- Production storage and deployment infrastructure are not selected here; the
  counter store stays behind an injectable interface proven in-process.
- Steel-thread order is fixed: schema validation, policy resolution, enforcement
  at the boundary, then denial reason and decision telemetry.

Owner: not stated in the intake. The blueprint states ownership only for usage
metering, which it assigns to the provider and places out of scope. A named
responsible owner for the rate-limiting work is an open decision.

Unknowns: implementation stack and module layout are unestablished in this
repository; the counter store backing the enforcement window is deliberately
unselected; the denial reason string must be fixed as a product decision before
it can be treated as stable.
