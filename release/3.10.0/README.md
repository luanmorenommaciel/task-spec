# TaskSpec 3.10.0 release candidate evidence

This directory is being assembled for the native toolkit release. It is not a
published-release claim. [The checklist](checklist.json) keeps missing evidence
explicit until every release criterion is met.

Current focused proof: [attested recipe isolation](qualification/attested-recipes.txt)
used a fake provider inside real Docker isolation. It observed two execution rounds,
separate signed environment evidence, distinct revoked credentials, canonical
acceptance, and an unchanged target branch. Real provider and comparative
productivity qualification remain separate requirements.

The [area overview](implementation-overview.md) explains the toolkit with seven
Mermaid diagrams. [Chat cohort reviews](qualification/chat-cohorts-summary.json)
retain 28 observations across candidate versions, including failed journeys;
they do not establish a qualified final corpus. The [retry proposal](qualification/retry-authorization.md)
identifies the permission boundaries that require explicit authorization.

The [source archive](artifacts/task-spec-3.10.0.tar.gz) and its
[checksum](artifacts/task-spec-3.10.0.tar.gz.sha256) are unpublished candidate
artifacts. A release tag, published assets, hosted proof and the completed pilot
are still required before release completion can be claimed.
