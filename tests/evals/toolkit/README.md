# Integrated toolkit evaluation corpus

This directory holds the protocol for prospective behavioral and real-provider
qualification. Deterministic adapters establish bounded runtime behavior; they do
not establish quality, comparative productivity, or live provider support.

The release pilot requires six scenarios: small fix, cross-seam feature, ambiguous
investigation, shared-resource contention, incident successor, and release evidence.
For each scenario, retain matched repository snapshot, evaluators, permissions,
budgets, model/provider/strategy versions, all failed attempts, and repeated runs
with Codex and Claude Code under separate-engine, integrated, and native-harness
workflows. Record engineer active time separately from agent wall time.

`pilot.py validate <results.json>` verifies comparability and computes the release
criteria from submitted observations. It never supplies missing measurements.
Unavailable data blocks qualification; observed zero is different from null.

`chat-cases.json` defines behavioral requests and expected state/authority actions.
`chat_score.py` checks retained normalized action traces, including a state read
before action, no work after denial, and no false completion. Human review must
also assess scope, question quality, and evidence. Passing trace validation alone
is not a claim that all supported chat hosts work well.

Release publication remains blocked until full make check, matching packaging,
live-provider runs, no false acceptance, migration/rollback proof, and comparative
criteria all pass. Published results must include unfavorable native-harness results.

## Prospective recording

`record.py` appends timestamped, hash-linked events and retains complete command
outputs with digests. Record run and intervention starts when they happen.
Unfinished intervals cannot be measured; failed delivery has a censored duration
and no accepted-capability time. Automated controller time is separate from human
intervention time. A verified journal protects integrity, not the truth of an
operator's assertions.

`preflight.py` exercises a pinned harness on the real stdin-validation issue in
an isolated snapshot with a HMAC-authorized task. These runs establish provider
and recording readiness and are explicitly excluded from comparative cells.
`evaluate_issue.py` supplies independent behavioral regressions; investigation
outputs also require retained review of their actual claims.

The `pilot.py validate` CLI checks retained file hashes, prospective timing, and
cost-evidence declarations in addition to the metric comparison. Calling its
pure arithmetic function in a unit test does not qualify a release.

## Permission-boundary qualification

Every comparison arm receives identical public evaluator files under
`tests/fixtures/toolkit/public-evaluator/` before the source snapshot is committed.
Signed eval commands check the script and input digests; the controller checks
those digests again before acceptance and uses its external evaluator for the
independent assessment. A failed managed attempt is assessed in its candidate
workspace, without granting acceptance.

The native comparison recorder observes each output stream during the existing
invocation and terminates the process group on recognized denial events. The
supervised TaskMesh recipe runner applies the same rule while consuming native
JSONL. Both observers bound each event at 2 MiB. This cannot prevent an already
in-flight action or detect a denial the harness does not report. Truncated native
output still retains the TaskMesh denial code. Missing final usage after a stop
remains unknown; it must not become a zero-cost observation.

After a denial, preserve the cohort and pause before another block. Correct the
fixture or implementation, obtain authorization for the changed boundary, and
register a fresh cohort. Never replace failed cells or combine changed controller
versions into a matched comparison.
