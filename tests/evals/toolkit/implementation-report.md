# Native TaskSpec toolkit implementation

Status: core implementation locally validated and ready for code review; the full release plan remains incomplete.

This change implements the approved native decomposition and supervised execution
architecture in the TaskSpec working tree. VERSION remains 3.9.0 with an Unreleased
changelog entry. No publication, target-branch commit, or production deployment is
claimed. The implementation tasks remain ready and unaccepted pending supervision.

## Delivered interfaces and behavior

| Package | Working-tree implementation | Evidence boundary |
| --- | --- | --- |
| Baseline and contracts | Optional recipe, native review/bundle/snapshot/lineage, operational evidence schemas; original formats remain readable | Local schema and conformance checks; no format-version bump |
| Decomposition | Native prepare/review/compile/status/impact/import; seams, lanes, legs, dependency and contention validation | Pinned Seamwise semantic fixture and adversarial tests; compiler validates authored architecture |
| Provenance and authoring | Domain-separated HMAC review, complete reviewed input inventory, immutable snapshots, exact unit lineage, relevant per-leaf constraints, resolved recipes | Tampering, missing sources, substituted units, and relevant drift refuse; sibling-only revisions preserve unaffected leaves |
| Managed execution | Existing Mesh attempt lifecycle runs bounded sequential recipes with durable rounds/deadline/no-progress accounting | Supervised recipe mode; required unsupported enforcement refuses |
| Graph and SDLC | Cross-run write/resource lease claims, initiative views, explicit capability proof tasks, optional SDLC stage labels, operational evidence import | Child completion alone never proves capability; reported pipeline status never establishes target health |
| CLI and chat | Shared command registry, stable JSON envelope, completions, installed guides, one portable skill, read-only initiative MCP tools | Installed journeys and bounded chat smokes; no universal harness quality claim |
| Packaging and cutover | Private hash-locked Python runtime, toolkit installer, resource inventory/integrity checks, explicit migration and rollback test, retirement patch | Comparative pilot and release publication remain outstanding |

The existing `plan`, `batch`, `run`, and `accept` meanings are preserved. Small work
can use direct task authoring. Recipe-managed work always uses TaskMesh, including a
single leaf. Execution guidance is resolved into the signed body before dispatch.
`mesh run --initiative` starts the currently eligible wave; later waves require
another request after their prerequisites have been accepted.

## Important implementation boundaries

- New decomposition lives under `tasks/.plans/<initiative>`. Original intake,
  authored recipe, source evidence, reviewed topology, generated plan, immutable
  snapshots, and migration originals remain distinguishable.
- Native reviews authenticate the complete input inventory, review identity and
  reason, topology, and plan. Review is distinct from execution authorization.
- Native materialization verifies the signed bundle, current reviewed inputs,
  complete unit mapping, and source digests. Atomic tasks carry relevant parent
  constraints and immutable provenance references.
- Native source evidence must be available as workspace-relative snapshots.
  Import requires the original authored recipe and resolvable evidence. It does
  not silently convert compiled legacy state or copy legacy review authority.
- Default recipes reserve at most three rounds and stop after two unchanged
  failing-eval/write-surface observations. Signed task budgets cap these values.
  Reservation occurs before provider invocation. Restart or replacement of the
  same task revision never refunds rounds or its total deadline.
- Required isolation or hard token enforcement is refused when unavailable.
  Managed attested-autonomy recipes are currently unsupported; ordinary existing
  attested-autonomy tasks retain their current path. This is a remaining runtime
  capability boundary, not an autonomy certification.
- Model/provider identities distinguish explicit routes, harness reports, and
  unknown defaults. Missing usage remains unknown. Pilot qualification requires
  explicit identities and measured human time.
- Claude managed recipes without declared MCP dependencies use restricted tools
  and an empty MCP configuration. Declared dependencies and custom adapters keep
  explicit configuration. Managed host policy remains effective.
- The original MCP protocol implementation remains byte-identical to its frozen
  conformance evidence. Toolkit tools register on that implementation through
  `src/interop/toolkit_mcp.py`; no second protocol stack or signing tool is added.
- Skill resources are bundled at matching relative paths. Installed source,
  schema, strategy, command metadata, guide, and skill integrity is checked before
  success. Generated conformance results and run state are excluded from shipped
  resources and integrity inventories; running conformance after installation
  does not create a false code-integrity failure. Reusing an incompatible same-version install refuses replacement
  unless explicitly requested with `--force`.

## Verification record

The original pinned checkout baseline was attempted in an isolated directory. It
failed its existing README release-status marker check. This implementation restores
the generated retained-release region; historical release evidence is unchanged.
That baseline failure is recorded, not presented as a clean baseline.

Current passing targeted evidence includes native semantic parity and adversarial
planning, installed native review-to-materialization, two-round synthetic repair
through supervised acceptance, durable budget/fencing/resource tests, operational
receipt validation, CLI completion/JSON checks, and legacy Python/TypeScript
consumer equivalence (26 portability checks). The final-source `make check` passed
with exit code 0 and `CHECK=READY`, including L0-L2 conformance. The local Docker
isolation suite also passed with its fixture provider; this is not a live-provider
managed-autonomy qualification. The original protocol SDK was unavailable; the
existing retained evidence was verified, without claiming fresh SDK certification.

The repository organization test now checks consistency of a declared live backlog,
while preserving its empty-frontier assertion for an empty backlog. It does not
require falsely accepting new implementation tasks merely to make tests green.

Real-provider evidence is deliberately narrower than the release pilot. Codex
completed one synthetic native initiative through canonical fixture acceptance,
with the fixture target branch unchanged. Claude also completed the fixture after adapter fixes. Its earlier stream-format
failure, two operator cancellations during host startup, and a no-progress run
remain in `managed-smoke-results.json`. Raw output and usage for earlier failures
are incomplete, so no aggregate cost or productivity claim is made. The final
Claude smoke reported $0.201117 for its successful run; that is not total effort
cost. `chat-smoke-results.json` separately retains the read-only chat checks.

## Qualification still required

1. Implement and qualify the managed attested-autonomy recipe path if it is to
   ship as part of this release. Current managed recipes explicitly refuse it;
   ordinary pre-existing autonomy is preserved. This is an implementation gap.
2. Run the full behavioral chat corpus and matched six-scenario comparative pilot
   with repeated Codex and Claude runs across separate-engine, integrated, and
   native-harness workflows. Repository snapshots, permission/budget/evaluator
   matches, explicit provider/model identities, raw failed attempts, and engineer
   active-time measurements are required. No productivity figures are invented.
3. Execute hosted macOS/Linux checks and obtain the required real-provider
   isolation evidence beyond the local fixture-provider suite.
4. Review implementation tasks through the normal supervisor acceptance boundary.
5. Apply the separately scoped Seamwise retirement notice only after cutover
   qualification. `tools/seamwise-retirement.patch` is prepared and unapplied.

No frozen `release/<version>`, `.taskspec/acceptance`, or `tasks/done` record is
rewritten. The pre-existing WATCHDOG.yml is outside this change. No target-branch
Git mutation or update to the earlier proposal document is part of this work.

## Final local gate

- Command: `make check`.
- Result: exit code 0, `CHECK=READY`, zero non-waived conformance failures,
  `CONFORMANCE=L2`.
- Host: macOS arm64; system Bash 3.2.57, Python 3.14.6, Go 1.26.2.
- Source: uncommitted working tree based on
  `76ff7b8880c95fd583f933c69b77c8d75ad041db`.
- [Complete final gate log](evidence/final-check.txt).
- [Verification manifest and log digests](evidence/verification.json).
- [Final packaging regression](evidence/packaging-regression.txt).
- [Original pinned baseline failure](evidence/baseline-check.txt).

The earlier successful full gate preceded one final packaging correction. Its
[separate log](evidence/pre-packaging-fix-check.txt) is retained; the final log
above is the fresh full run after that correction. Later writes only retain
these records and update this report. No implementation task is marked accepted
by this evidence, and release qualification remains false.

