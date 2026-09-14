# Release process

A release is complete only when the versioned evidence, remote tag, published
assets, hosted checks, and verified installation agree on the shipped revision.
The working tree is an implementation candidate until those checks pass.

1. Decompose the release into reviewed atomic work. Materialize and HMAC-seal
   each ready leaf before implementation dispatch. Record scope changes as new
   authorization; do not rewrite accepted historical tasks.
2. Settle code and documentation. Check root/installed skill parity, the shared
   CLI registry, migration and rollback, runtime compatibility, and file ownership.
3. Run the single `make check` gate on the settled source. Run required Mesh
   isolation and packaging checks explicitly; UNAVAILABLE does not mean PASS.
4. Execute the prospective comparative pilot on fixed repository issues,
   snapshots, budgets, permissions, and evaluators. Record interventions when
   they occur and retain failures. Publish unfavorable results too. A corpus
   definition or synthetic adapter run does not establish provider quality.
5. Complete canonical acceptance of implementation tasks. Keep supervisor
   acceptance distinct from the user's decision to publish a release.
6. Update VERSION and its declared mirrors, then generate release reports and
   reproducible artifacts in the new version's release directory. Preserve prior
   version directories, protocol locks, and historical acceptance evidence.
7. Commit the authorized changes to main, publish the new immutable tag, and
   create the release with checksums and provenance. Verify the downloaded
   assets and retain hosted macOS/Linux results against the shipped commit.
8. Record exact commands, commit, tag, release URL, artifact hashes, and clean
   status in the release checklist. Any unresolved release criterion remains
   visibly open; publication must not convert a missing observation to a pass.

The toolkit pilot criteria require zero observed false acceptance, no acceptance
quality regression against the separate-engine workflow, and improvement in one
median time measure without worsening the other. Results against the practical
native-harness workflow are reported even when they favor that baseline.
