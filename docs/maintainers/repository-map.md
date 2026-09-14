# Repository map and change ownership

Read [OPERATING.md](../../OPERATING.md) and [AGENTS.md](../../AGENTS.md) before
changing the engine. Keep the existing root layout; add workflow depth within
its owning directory.

| Area | Owns | Change and validation boundary |
|---|---|---|
| `bin/` | The single CLI entry point | Dispatch remains compatible with the shared command registry |
| `src/author`, `src/decompose`, `src/recipe` | Authoring, reviewed decomposition, sealed recipes | Schema, representative fixtures, provenance and legacy behavior |
| `src/gate`, `src/accept`, `src/lib`, `src/security` | Authorization and canonical acceptance | Bash 3.2, HMAC, revision, scope, and receipt checks |
| `src/cli`, `src/dispatch`, `src/interop` | Help, machine contracts, handoff, inspection | Registry parity, JSON purity, read-only MCP; preserve the locked base bridge |
| `src/meshctl`, `mesh/` | Cockpit and durable execution control plane | One scheduler and round lifecycle, fenced attempts, recovery |
| `spec/` | Normative formats, schemas, conformance | Format changes update schema, conformance, and changelog together |
| `harness/` | Non-normative adapters and host entry points | Adapter claims describe capabilities actually enforced |
| `skills/`, root `SKILL.md` | Portable chat workflow | Root/mirror byte parity and complete installed guide resources |
| `docs/` | User knowledge base and maintainer guidance | New workflows under `guides/`; exact contracts under `reference/` |
| `tests/` | Reproducible tests and prospective evaluation corpus | Fixtures stay under `fixtures/`; report synthetic and provider proof separately |
| `release/` | Mutable runtime inputs and frozen version evidence | `release/mesh/` can evolve; shipped version evidence is immutable |
| `interop/` | Protocol lock | Preserve the frozen lock path and digest-bound references |
| `tools/` | Release, rendering, verification utilities | Generated views must match their authoritative sources |
| `tasks/`, `.taskspec/` | This engine's backlog and acceptance records | Materialize, seal, evaluate, accept; never hand-edit completion |
| `.github/` | Hosted verification and publication | Retain run IDs, platform results, exact revision and asset digests |
| `.claude-plugin/`, `package.json`, `install.sh` | Distribution | Version identity, non-clobbering install, private runtime, packaged resources |
| `assets/` | README visual assets | Preserve the established Receipt Gate identity and descriptive alt text |

`docs/guides/toolkit/` now groups the integrated user journey; installed skills
carry that same directory. `docs/maintainers/` holds process and repository
ownership. Existing runbooks remain historical walkthroughs; that directory
is closed to new how-tos. Cross-product operating hops belong in OPERATING.md.

`WATCHDOG.yml` is local host advisor configuration, explicitly ignored and
excluded from release inputs. It is not product configuration or authority to
launch additional agents. Preserve local contents during cleanup.
