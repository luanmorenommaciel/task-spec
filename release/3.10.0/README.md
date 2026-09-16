# TaskSpec 3.10.0 release candidate evidence

This directory is being assembled for the native toolkit release. It is not a
published-release claim. [The checklist](checklist.json) keeps missing evidence
explicit until every release criterion is met.

The latest [readiness review](qualification/planning-blocker-readiness/review.json)
records passing local, hosted macOS/Linux/isolation, and fresh-installation checks
for source `97c9274`. Fifteen implementation and correction tasks are canonically
accepted. Chat coverage remains 19/20: the latest planning proposal retained its
product blockers but failed scratch containment and validation-claim review.
No comparative cohort was started after that failure. The next
[bounded retry proposal](qualification/planning-blocker-retry-proposal.md) requires
a new decision; passing deterministic checks do not qualify live behavior.

Current focused proof: [attested recipe isolation](qualification/attested-recipes.txt)
used a fake provider inside real Docker isolation. It observed two execution rounds,
separate signed environment evidence, distinct revoked credentials, canonical
acceptance, and an unchanged target branch. Real provider and comparative
productivity qualification remain separate requirements.

The [area overview](implementation-overview.md) explains the toolkit with seven
Mermaid diagrams. The earlier [chat cohort reviews](qualification/chat-cohorts-summary.json)
retain 28 observations across candidate versions, including failed journeys.
The [current chat result](qualification/chat-results.json) also references later
observations; these are source-bound cases, not one uniform final-source cohort.

The [source archive](artifacts/task-spec-3.10.0.tar.gz) and its
[checksum](artifacts/task-spec-3.10.0.tar.gz.sha256) are unpublished candidate
artifacts. The latest unpublished source archive is linked from the readiness
review above. A release tag, published assets, a qualified pilot, and final gates
for the release source are still required before release completion can be claimed.
