# release/ — shipped inputs and frozen evidence

This directory name is load-bearing. `install.sh` and the npm `files`
allowlist ship `release/mesh`; CI reads `release/trust`. Frozen
`release/<version>/` paths are digest-pinned by retained evidence. Do not
rename this directory or move files under an existing version.

## Inclusion rule

Pick a side before adding a file:

| Kind | Paths | Mutable? |
|---|---|---|
| Shipped runtime input | `mesh/`, `docker/`, `trust/` | Yes, with installer/CI review |
| Current audit input | `evidence.json`, `quality-rubric.json` | Yes, with the release-audit tests |
| Frozen per-version evidence | `<version>/` (`3.7/`, `3.8.1/`, `3.9.0/`, …) | **No.** Never rewrite to match a later refactor |

`mesh/` is a Dockerfile, image lock, and worker entrypoint installed by
`install.sh --with-mesh`. It is not an audit receipt.

`<version>/` holds SBOMs, checksums, conformance results, attestations, and
reviewer reports for that shipped tag. A test re-verifies named artifact
digests against the working tree. Moving a pinned path makes that evidence
unverifiable.

New files must declare which row they belong to in the name or a nearby
README. Do not introduce a second top-level directory for either side.
