# Five-minute reviewer route

This route separates an installed product check from source, hosted, and
external evidence. It is designed for reviewers who want to falsify the release
claims rather than trust a badge.

## 1. Prove the installed lifecycle

From any directory:

```bash
taskspec doctor
taskspec demo
```

`doctor` reports prerequisites and signing readiness. `demo` runs a disposable
plan → gate → handoff → eval → acceptance loop and must end with `DEMO=READY`.
It does not prove hosted CI, real-engine performance, or sandbox enforcement.

## 2. Inspect and materialize the public contracts

```bash
taskspec agent-context
taskspec example task-plan --out tasks/.plans/reviewer.yaml
taskspec plan --manifest tasks/.plans/reviewer.yaml
```

The example command reads the canonical TaskPlan bundled with the installed
release. It refuses an existing output unless `--force` is explicit. Plan
preview is deterministic and does not create Task-Specs.

## 3. Run the local repository gate

From the tagged source checkout:

```bash
make check
```

The command must execute doctor, documentation lint, all self-tests, the
isolated demo, and L0–L2 conformance before it emits both `CONFORMANCE=L2` and
`CHECK=READY`. A hosted job that starts zero steps is not equivalent evidence.

## 4. Verify retained proof and its digests

```bash
python3 src/evidence/release_audit.py check
python3 tools/render-status.py --check README.md
python3 -m json.tool release/3.8.1/protocol-conformance.json
```

The fixed rubric, scorecard, and release-evidence manifest must agree
byte-for-byte. Protocol evidence names exact specification revisions, SDK
commits, and package digests in `spec/UPSTREAM.lock`. The report proves
compatibility with those pinned implementations—not ecosystem certification.

## 5. Recalculate release readiness

```bash
make release-audit
```

The final published release must end with:

```text
PROTOCOLS=READY
ENGINE_MATRIX=READY
SANDBOX_ATTESTATION=VERIFIED
QUALITY_SCORE=97
RELEASE_AUDIT=READY
```

During release construction, a nonzero result with named `BLOCKED` tokens is
correct. Missing, pending, unavailable, failed, or digest-mismatched evidence
earns zero; it is never silently promoted to a pass.

## Reading the score honestly

| Evidence class | What it proves | What it does not prove |
|---|---|---|
| Local | The repository tests ran against one checkout | Hosted execution or publication |
| Protocol | Pinned SDK and wire fixtures round-tripped | Certification across every implementation |
| External engine | A frozen attempt was accepted within scope | Production reliability |
| External enforcement | A signed attestor observed the declared boundary | Semantic correctness of the work |
| Published/provenance | Tagged bytes, SBOM, and attestations agree | That future deployments remain healthy |

The remaining three rubric points are deliberately unavailable: shared-key
HMAC does not establish universal semantic truth, pinned SDK tests are not
ecosystem-wide certification, and one synthetic benchmark is not long-running
production evidence.
