# release/ — shipped inputs and frozen evidence

Current engine: **3.9.0** (`../VERSION`). This directory name is load-bearing.
`../install.sh` and the npm `files` allowlist ship `release/mesh`. CI reads
`release/trust`. Frozen `release/<version>/` paths are digest-pinned. Do not
rename this directory or rewrite a shipped version tree to match a later
refactor.

There are two proof corridors. They are not the same thing:

| Corridor | Answers | Current files |
|---|---|---|
| Quality score (97/100) | Did the 3.8.1 trust chain ship with digest-backed proof? | `evidence.json`, `quality-rubric.json`, `3.8.1/` |
| TaskMesh 3.9.0 | Did the optional control plane install, isolate, and recover? | `3.9.0/`, `mesh/` |

3.9.0 **reuses** the 3.8.1 scorecard as its quality baseline. It does not
replace it. Recalculate with `make release-audit`. Check without mutating
with `python3 src/evidence/release_audit.py check`.

## Inclusion rule

Pick a side before adding a file:

| Kind | Paths | Mutable? |
|---|---|---|
| Shipped runtime input | `mesh/`, `docker/`, `trust/` | Yes, with installer/CI review |
| Current audit input | `evidence.json`, `quality-rubric.json` | Yes, with the release-audit tests |
| Frozen per-version evidence | `3.7/`, `3.8.1/`, `3.9.0/`, … | **No.** |

New files must declare which row they belong to. Do not introduce a second
top-level directory for either side.

## Catalog

### Shipped runtime inputs

| Path | What it is | Used by |
|---|---|---|
| [`mesh/Dockerfile`](mesh/Dockerfile) | Non-root TaskMesh worker image (OMP 17.3.3, pinned base digest) | `install.sh --with-mesh` |
| [`mesh/image.lock`](mesh/image.lock) | `TaskMeshWorkerImageLock/v1` for engine **3.9.0** | mesh install / isolation tests |
| [`mesh/worker-entrypoint.sh`](mesh/worker-entrypoint.sh) | Worker entrypoint copied into that image | `mesh/Dockerfile` |
| [`docker/Dockerfile`](docker/Dockerfile) | Attestation runner image (read-only engine copy) | sandbox attestation |
| [`docker/run-attestation.sh`](docker/run-attestation.sh) | Host-side attestation driver | `make release-audit` sandbox token |
| [`trust/release-provenance.ed25519.pub.pem`](trust/release-provenance.ed25519.pub.pem) | Public key for DSSE/in-toto release provenance | CI and [`../docs/getting-started/installation.md`](../docs/getting-started/installation.md) |

`mesh/` is a worker image, not an audit receipt. `docker/` attests an
environment; it is not the TaskMesh worker.

### Current audit inputs

| Path | What it is |
|---|---|
| [`evidence.json`](evidence.json) | `TaskSpecReleaseEvidence/v2` for the **3.8.1** quality corridor. README status is generated from this file. |
| [`quality-rubric.json`](quality-rubric.json) | Fixed 100-point rubric (`taskspec-release-quality-3.8.1`). Target 97. |

These two files plus `3.8.1/scorecard.json` must agree. A later engine version
may keep them until a new quality corridor is explicitly opened.

### Frozen per-version evidence

Rewrite nothing under these directories. `tests/test-repo-layout.sh` re-checks
digest-pinned paths named in `*/protocol-conformance.json`.

#### `3.7/`

Disabled nine-family `EngineMatrix/v1` **template**
([`3.7/engine-matrix.json`](3.7/engine-matrix.json)). Every entry is
`enabled: false`. That is unavailability, not a pass. There is no handoff or
`runs/` tree here. How to run a real matrix is in
[`../docs/guides/multi-engine-evidence.md`](../docs/guides/multi-engine-evidence.md).

#### `3.8.1/`

The quality-corridor archive. Notable files:

| Path | Holds |
|---|---|
| `scorecard.json` | 97/100 result the 3.9.0 baseline still cites |
| `protocol-conformance.json` | A2A/MCP pins; names `../interop/UPSTREAM.lock` by digest |
| `sbom.spdx.json` | SPDX of the 3.8.1 source archive (historical paths) |
| `engine-matrix.json` / `engine-matrix-result.json` | Frozen Codex + Claude corridor |
| `benchmark/` | Three synthetic leaves (XS/S/M) and the snapshot they start from. See [`3.8.1/benchmark/README.md`](3.8.1/benchmark/README.md) |
| `local-gates.json`, `hosted-ci.json`, `install-matrix.json` | Gate and install evidence |
| `environment-*.json`, `sandbox-execution-artifact.json` | Signed environment / sandbox receipts |
| `reviewer-report.json`, `release-report.json` | Human review and publication record |
| `rc1-publication-attempt.json`, `rc2-publication-attempt.json` | Failed publication attempts, retained on purpose |

#### `3.9.0/`

TaskMesh + private-release corridor. It does **not** contain a new scorecard.

| Path | Holds |
|---|---|
| `mesh-conformance.json` | Local TaskMesh suites (`MESH_*=READY`) |
| `mesh-release-evidence.json` | Roll-up: isolation, install, hosted CI, provenance |
| `reviewer-report.json` | Product-boundary and cockpit review |
| `release-report.json` | Tagged artifacts for `v3.9.0` |
| `hosted-ci.json` | GitHub Actions ubuntu + macOS `make check` |
| `install-matrix.json` | Checksum-backed / private install matrix |
| `private-release-evidence.json` | DSSE provenance observation |

## How to read a claim

1. Engine version → `../VERSION` (3.9.0).
2. Quality score → `evidence.json` + `3.8.1/scorecard.json` (97, 3.8.1 corridor).
3. TaskMesh readiness → `3.9.0/mesh-release-evidence.json`.
4. Protocol pins → `3.8.1/protocol-conformance.json` + `../interop/UPSTREAM.lock`.

Unavailable or disabled evidence is never a pass. The 3.7 matrix template and
the 3.8.1/3.9.0 “does not claim production reliability” limitations are
intentional.

## Adding the next version

Create `release/<new-version>/`. Do not move or edit an older version
directory. If the quality corridor stays 3.8.1, leave `evidence.json` and
`quality-rubric.json` pointing at `3.8.1/scorecard.json`. If you open a new
corridor, update those two files and the release-audit tests in the same
change.
