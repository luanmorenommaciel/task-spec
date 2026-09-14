# Runtime defects found by the initial comparative cohort

The initial cohort is interrupted and is **not qualified**. Its two observations,
original controller bytes, schedule, and raw evidence are retained. The other 70
registered cells did not execute. Observed cost, including the failed Claude run,
was $2.5640405 under the recorded harness/API-equivalent accounting methods.

## Observed failures

1. **Worktree placement:** Claude Code's Edit permission check rejected
   `src/recipe/recipes.py` because its source checkout was under
   `.git/taskspec-mesh/runs/.../attempts/...`. The harness classified that path as
   protected Git metadata. Claude left the authorized source unchanged and reported
   the denial; its proposed scratch patch was not accepted as the task result.
2. **Lease lifetime:** TaskMesh did not renew a daemon-owned executing attempt.
   The default five-minute lease expired inside a ten-minute signed recipe budget.
   Fencing refused the stale result. A second repair round had also been attempted
   despite the harness's already reported permission denial.

## Prepared changes

- New integration and attempt source worktrees live under
  `.taskspec/mesh/workspaces/<run>/`. Git metadata stays in its original directory.
  Existing recorded workspace paths are retained; old worktrees are not moved.
- Managed workspace creation refuses symlink traversal.
- The daemon renews only attempts it actively executes, through the existing
  fenced heartbeat operation. Renewal preserves the requested lease lifetime,
  consumed recipe rounds, and original signed deadline.
- Losing renewal authority cancels the executor. Explicit cancellation also stops
  a daemon-owned process when its lease has already become stale.
- Recognized harness permission-denial results park the task before another
  repair round. They are not ordinary eval failures.
- Automatic acceptance evaluation shares the managed deadline and cancels its
  evaluator process group. Daemon shutdown cancels owned execution contexts.

## Verification

- [Go runtime tests](runtime-defect-go-tests.txt): pass, including short-lease
  renewal, unchanged recipe budgets, cancellation, worktree placement, symlink
  refusal, and recognition of permission denials.
- [Required Docker attested-recipe test](runtime-defect-attested-test.txt): pass,
  including two rounds, distinct revoked credentials, signed execution evidence,
  canonical acceptance, and the unchanged target branch.

These checks establish the prepared implementation and synthetic execution paths.
They do not establish that Claude will permit the new workspace layout or that a
corrected comparative cohort will satisfy the release criteria.

The changed workspace boundary requires explicit authorization before rerunning
Claude's previously denied edit. No permission bypass mode is part of the change.
