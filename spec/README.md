# spec/ — the normative contract

Everything in this directory is the contract. `../src/`, `../mesh/`, and
`../harness/` are one implementation of it and may lag; this directory may not.
If prose anywhere else disagrees with what is here, this directory wins.

## What is here

| Path | Holds |
|---|---|
| [task-spec-v3.md](task-spec-v3.md) | the stable format. This is the authoring default |
| [task-spec-v4.md](task-spec-v4.md) | opt-in evidence, identity, environment, and portability policy. v3 is never upgraded implicitly |
| [schemas/](schemas/README.md) | Draft 2020-12 JSON Schemas for every contract the engine emits or reads |
| [conformance/](conformance/README.md) | the executor conformance suite (L0/L1/L2) and its fixtures |
| `UPSTREAM.lock` | lives in [`../interop/`](../interop/), not here — its path is digest-pinned by 3.8.1 release evidence |

## The compatibility rule

Formats v1 through v4 stay readable. A `format_version` bump is MAJOR.

Changing the format is triple-locked, and all three land in one change:

1. the schema in `schemas/` is updated,
2. a fixture in `conformance/` covers the change,
3. `../CHANGELOG.md` records it.

`../tests/lint-skill-docs.sh` and `../tests/test-schema-contracts.sh` assert the
first two; the conformance suite is what an independent executor is measured
against. See [../docs/reference/compatibility-policy.md](../docs/reference/compatibility-policy.md)
for what a minor release may change.

## Reading order

Start with `task-spec-v3.md`. Read `task-spec-v4.md` only when you need
independent evidence policy. For the concepts behind the format — the six
zones, the effort gate, the sign-off contract — read
[../docs/index.md](../docs/index.md); for exact field names and CLI behavior,
read [../docs/reference/](../docs/reference/index.md).
