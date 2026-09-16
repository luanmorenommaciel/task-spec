# Remaining bounded qualification retry

Status: prepared; no new live retry is authorized or dispatched by this proposal.

## What the latest attempt established

The full local gate and the required hosted macOS, Ubuntu and autonomous-isolation
jobs passed for source `640d061`. The thirteen implementation/infrastructure tasks
now have current canonical acceptance records. Their fresh verification handoffs
do not reconstruct the original implementation attempt history.

The fresh Claude atomic-authoring observation passed its bounded draft-authoring
review. Overall retained chat coverage is 19 of 20 cases, with source-bound
observations from different candidate revisions. The atomic draft still needs
product decisions and stronger purity proof before it could be sealed.

The fresh Claude planning observation failed. It wrote example files under `/tmp`
and then attempted native `Read` outside its restricted workspace. The first read
was denied by the harness; the guard refused the subsequent read. No proposal or
completed user-facing blocker was produced. Exit zero did not count as a pass.
The comparison was held before its first cell, so the completion-retry registration
has zero observations. Earlier cohorts and failures remain unchanged.

Evidence: [planning review](completion-retry/chat/runs/plan-claude-20260916T022738Z/behavior-review.json),
[atomic review](completion-retry/chat/runs/atomic-claude-20260916T022739Z/behavior-review.json),
[acceptance summary](completion-retry/acceptance-summary.json).

## Concrete corrections prepared

- The shared skill entry point now applies workspace-contained scratch and example
  paths to **every** route, before planning or authoring begins. It distinguishes
  shell permission from native file-tool permission. Root and packaged mirrors
  remain identical. No permission grant changed.
- The comparative recorder probes the actual CLI version, retains that output, and
  refuses a mismatch against the registered version before dispatch. It no longer
  hardcodes an old Claude version. Setup-only and synthetic runs are labeled as such.
- A new private installation and source archive preserve the corrected candidate.
  [Readiness review](planning-path-readiness/review.json) records 238 verified
  installed resources, the passing full local gate and all three hosted jobs
  for source `459f0cd`. No new provider observation was run.

These corrections are implementation and deterministic readiness evidence. They
are not a passed Claude planning case or a qualified comparative pilot.

## Requested bounded scope

1. Run **one** fresh Claude planning observation from the corrected installed skill,
   with unchanged restricted permissions. Preserve its actual artifacts, costs,
   errors and behavioral review. Do not rerun the already passed atomic case.
2. Only if that planning observation passes, freeze a new complete 72-cell comparison
   registration for the corrected source and actual harness versions: the same six
   repository issues, three workflows, two harnesses and two repetitions. Keep the
   original snapshots, scopes, evaluators, budgets and prospective intervention
   recording. Do not reuse or pool observations from earlier cohorts.
3. A new permission denial stops the affected work and pauses before another
   comparative block. Do not retry through another tool/path or replace a losing
   cell. Ordinary authorized eval repair remains bounded by the signed contract.
4. Publish only if the original qualification criteria and final release gates pass.
   An unfavorable comparison or unknown measurement remains an explicit release gap.

## Why another decision is required

The [product skill](../../../SKILL.md) says: “Do not switch tools or paths to perform
it; a changed boundary needs explicit authorization.” The last
[approved retry](completion-retry-approval.json) was bounded to one fresh planning
case and stopping on new denials. That observation has now encountered a new denial.
This proposal requests a new observation with corrected initial path selection;
it does not widen permissions or retry the denied `/tmp` read.
