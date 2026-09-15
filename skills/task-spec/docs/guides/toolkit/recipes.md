# Atomic recipes

`taskspec recipe list` discovers pinned strategies. `recipe show <strategy>` emits
a resolved example; `recipe validate <file> --budget <n>` validates a resolved
recipe. TaskPlan units accept either a strategy name or a resolved recipe mapping.
Native authored decomposition recipes accept strategy names.

Bind acceptance checks to the source requirements and recorded decisions. If a
limit, threshold, or edge-case behavior is unspecified, label a proposed choice
and keep it open for review; do not encode it as an already agreed requirement.

During authoring, choose scratch paths before running eval-discrimination checks.
If the harness confines file tools to the workspace, create a unique scratch
subdirectory under the initiative's planning workspace and remove only the scratch
files created by that check. A system temporary directory is not automatically
within the permitted write surface. Once execution is sealed, scratch writes must
also fit the signed task scope. A denied write stops the session; this guidance
never authorizes moving that denied action to another path.

For a directly authored TaskPlan with multiline shell evals, use a JSON manifest
and encode each command as a JSON string with `\n` escapes. The portable YAML
manifest reader supports a restricted subset and does not accept `|` or `>` block
scalars. Multiline commands remain supported through JSON; direct atomic-task
authoring also remains available.

Strategies are direct, plan-execute-verify, diagnose-repair-verify, test-first, and
research-synthesize-verify. Their guidance resolves into the Validation Card's
agent contract before HMAC authorization. Changing installed strategy instructions
cannot alter a sealed task. Use relevant context, examples when needed, tool
feedback, explicit deliverables, and concise self-checks; do not request private
reasoning transcripts.

Each recipe stays within one outcome, scope, authority, and timeout. Internal
steps are sequential. Independent ownership or acceptance requires another leaf.
New recipes default to three executor-plus-evaluation rounds and stop after two
identical failing-eval/write-digest observations, capped by the signed budget.
Timeout and consumed rounds persist across replacement attempts of the same
revision. Cancellation, stale authorization, scope escape, and unavailable required
enforcement stop work. Optional usage metrics remain null when unavailable.
