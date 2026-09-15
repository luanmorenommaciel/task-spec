# Execute and recover with TaskMesh

Initialize TaskMesh with `taskspec mesh init` in the authorized host environment
before using it from a coding harness that protects Git metadata. Initialization
writes `.git/info/exclude` and creates the repository-local daemon state. Several
inspection commands also initialize a missing daemon; they are not guaranteed to
be filesystem read-only. If the host denies this setup, report that boundary and
wait for the required authorization. Do not switch tools to repeat the denied write.

Inspect `taskspec status <task>`, `taskspec mesh frontier`, and
`taskspec mesh explain --task <id>`. Ready leaves need a valid HMAC seal.
Use `taskspec mesh run --initiative <id> --execute` for the eligible native
initiative frontier, or `mesh run --task <id> --execute` for one managed task.
Declared resources and overlapping writes share the existing concurrency logic.
A run starts the currently eligible wave; inspect status before requesting later work.
Without `--execute`, `mesh run` still creates a run, worktree and lease. Use
`--dry-run` for a preview; omitting `--execute` is not a preview.

A recipe-managed run follows existing attempts, worktrees, leases, fencing,
cancellation, and recovery. Per-round artifacts retain executor and eval evidence;
no separate loop runner is introduced. In supervised mode, passing evals enter
awaiting_supervision.

New source worktrees live under `.taskspec/mesh/workspaces/<run>/`, outside Git's
metadata directory. Existing recorded workspace paths remain valid. The daemon
renews the fenced lease while it owns an active executor; renewal does not extend
the signed deadline or refund rounds. If renewal loses authority, execution stops.
Recognized harness permission-denial results park immediately instead of entering
another repair round. Resolve the reported permission boundary before resuming;
an eval failure and a denied tool action need different recovery decisions.

Use `mesh accept <attempt> --supervised-by <identity> --reason <text>` only with
applicable supervisor authorization. `finish` reports the human integration route.
Canonical acceptance receipts may already exist as untracked files in the
supervisor checkout. After `finish`, inspect `git status --short` and commit the
exact receipt files for that run before performing the reported merge. This
preserves the evidence and avoids Git refusing to overwrite untracked receipts.
TaskMesh does not perform this user-branch commit or merge.

After interruption, read `mesh status`, `mesh watch <run>`, and initiative state.
Use `mesh resume <run-or-attempt> --execute` only after resolving the recorded blocker.
Resuming does not refund recipe rounds or restart its total deadline. Exhaustion
requires reviewed successor work, not silent budget expansion.

For a stop explanation, distinguish unused rounds from time remaining. Compare
the recorded deadline with current UTC and report the check time. Recommend a
successor for exhausted time only when that comparison establishes exhaustion;
an executor failure alone does not mean the deadline is nearly gone.

For inspection-only requests, prefer read-only CLI views and existing artifacts.
If database inspection is necessary, use a read-only connection to existing state.
Never delete or reuse a fixed scratch directory to inspect a live database.
Any necessary scratch space must be uniquely created within the permitted boundary,
and cleanup must be limited to files created by that inspection.

Ordinary tasks retain direct `taskspec handoff`. Managed recipes require TaskMesh.
Supervised adapters and the attested OMP sandbox use the same round controller.
Autonomous OMP requires the pinned sandbox, fixed provider/model, external host
attestor, and evaluator trust registry. Each round receives a fresh expiring
capability and retains its own signed execution evidence; prior credentials stay
revoked. Evals run in the sanitized host environment, and canonical acceptance
reruns the task proof. Execution attestation does not claim eval isolation.
Automatic acceptance evaluation uses the remaining signed deadline; cancellation
also stops its evaluator subprocesses. An explicit later supervisor acceptance
does not grant new execution rounds or reset the managed run's deadline.
Custom required environment contracts and hard token limits refuse before any
round when their enforcement cannot be established. No silent downgrade occurs.

Keep the authorized task, native plan bundle, immutable snapshots, and applicable
source evidence in the Git revision used for the attempt. Mesh creates worktrees
from that revision. Recording files in Git does not replace review or HMAC sealing.

Round evidence distinguishes explicitly routed models from models reported by a
harness. Unreported defaults remain unknown; comparative qualification requires
explicit model and provider identities. Supervised adapters use the harness host
environment; required isolation or hard token enforcement must refuse if unavailable.

Recipe-managed Claude runs with no declared MCP dependencies use restricted
Read/Edit/Write/Bash tools and an empty MCP configuration. User, project, and
local settings hooks are excluded from that worker context; managed host policy
still applies. Explicit route model/provider choices remain authoritative.
Declare needed MCP dependencies or provide an explicitly configured adapter.
