# Bounded qualification retry proposal

Status: prepared; not authorized or dispatched. This proposal consolidates the
pending Claude planning/atomic question and the newly stopped comparative pilot.

The approved-runtime pilot remains paused with four original observations. Its
Claude integrated cell reported a denied external evaluator read, continued with
22 tool calls, and was parked without acceptance. Its retained failure assessment
used the supervisor checkout, so it does not establish final candidate quality.
See the [partial summary](../pilot/cohorts/approved-runtime/partial-summary.json).

## Concrete corrections

- Supervised TaskMesh recipes stop the current invocation when a recognized native
  denial event arrives, before another repair round. The native-harness comparison
  recorder applies the same rule. Events are bounded at 2 MiB; unreported denials
  and already in-flight actions remain limits. Unknown usage remains unknown.
- Every workflow receives the same public evaluator and input files within its
  workspace. Their digests are embedded in the signed eval commands and checked
  again by the supervisor before acceptance. The independent controller retains
  its external evaluator. No wider filesystem grant is proposed.
- Failed managed runs are assessed against their actual attempt workspace.
  Historical results are not rewritten.
- Corrected chat guides preserve unresolved decisions and applicable decision
  references, keep unspecified limits as proposals, and select permitted scratch
  storage before execution. The existing chat deny-and-stop guard remains active.

## Readiness evidence

[Deterministic readiness review](stream-denial-readiness/review.json) records
passing setup for all three workflows, a successful synthetic TaskMesh lifecycle
with canonical acceptance and external proof, and a synthetic denial that parks
after one round with no fallback write or acceptance. The fresh private toolkit
installation verifies 237 resources and runtime readiness. Full repository gate
results are recorded separately; synthetic checks do not qualify either provider.

## Requested scope

1. After local and installed readiness checks pass, register and run one fresh
   72-cell comparative cohort: six real repository issues, three workflows,
   Codex and Claude, two repetitions. Preserve fixed scopes, three invocation
   rounds and ten minutes per atomic leaf, prospective intervention recording,
   HMAC authorization, supervised acceptance, and independent evaluation.
2. Run one fresh Claude planning case and one fresh Claude atomic-authoring case
   using the corrected installed guides and unchanged restricted permissions.
3. A new permission denial stops the affected work; do not switch tools or paths
   to complete it. Retain every failed observation and pause before another
   comparative block. Do not replace cells or pool changed cohorts for qualification.

This authorizes qualification attempts, not a declaration that the release passes.
Publication still depends on the original release criteria and actual evidence.

## Why renewed authorization is needed

[Root skill](../../../SKILL.md) says: “Do not switch tools or paths to perform it;
a changed boundary needs explicit authorization.” The evaluator location changes
after an actual denial, and the two Claude chat cases also stopped on denials.
The previous approval covered earlier corrections; these are new bounded retries.
