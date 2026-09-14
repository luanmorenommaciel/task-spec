# Qualification retry boundary

Status: prepared; awaiting explicit authorization. No corrected retry described here has run.

The failed observations remain in their original cohorts with their original costs. A corrected cohort must register its source hashes, installed resources, provider versions, cases, budgets and intervention events before dispatch.

| Failed boundary | Prepared correction | Scope of requested authorization |
| --- | --- | --- |
| Claude could not edit a pilot source worktree below Git metadata. | TaskMesh creates source worktrees under `.taskspec/mesh/workspaces/`; Git metadata remains separate. | Run a new comparative cohort using these source worktrees. Preserve the interrupted original cohort. |
| Claude atomic authoring tried another tool after a denied scratch-file read. | Qualification hook denies subsequent pending tools and ends the turn after a recorded permission denial. Its marker-write probe passes. | Repeat the atomic authoring case with this deny-and-stop guard. A new denial still stops execution. |
| Claude could not read a guide outside the fixture workspace. | Copy the installed skill, exact guides and plugin manifest into the fixture workspace; load that native plugin path. Pin the installed CLI first in PATH. | Repeat the affected chat qualification using the workspace-local installed resources. No external guide-directory grant is requested. |
| Codex could not initialize protected Git metadata or reach the Mesh Unix socket. | The fixture controller initializes the existing Mesh daemon before the harness starts. Configure a session-scoped allowlist for that fixture's exact Unix socket using the harness's documented socket policy. | Permit the existing local Mesh control channel for managed chat cases while retaining filesystem restrictions. No broad network grant, full-access sandbox, second runner or global Codex configuration change is requested. |

The source-worktree, guard and skill-resource corrections have implementation and local regression evidence. The socket-policy configuration is a prepared direction supported by the current documented configuration interface; an actual configured handshake and execution qualification are still required. If the installed harness cannot enforce the exact socket allowance, stop and report that limit rather than broadening access.

The existing TaskMesh MCP surface was inspected as an alternative, but is not selected for these retries. Its current surface has no resume operation, and using another execution interface would add an avoidable qualification difference.

After approval, run bounded readiness checks first, then the registered comparative and chat cases. Preserve failures and prospective intervention records. Passing process exit does not establish acceptance, chat correctness or release readiness.

Sources and evidence:

- [Initial pilot observations](../pilot/cohorts/initial/results.json)
- [Atomic chat review](chat-corrected/runs/atomic-claude-20260914T215012Z/behavior-review.json)
- [Guide-boundary review](chat-effects/runs/stopped-claude-20260914T223539Z/behavior-review.json)
- [Socket-boundary review](chat-independent-codex/resume-codex-20260914T223751Z/behavior-review.json)
- [Official Codex configuration reference](https://developers.openai.com/codex/config-reference): named permission profiles support exact Unix-socket allowlist entries. Configuration syntax alone does not prove that the installed harness enforces the proposed boundary.
