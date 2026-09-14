# Intent and evidence

Read the workspace's agent instructions, `taskspec agent-context`, and current
`taskspec status --initiative <id>` before continuing an existing initiative.
For small, understood changes, author one TaskPlan unit or use `taskspec new` directly.
Decomposition is optional; never invent lanes to fill a template.

For a broader outcome, collect the desired observable result, evidence sources,
constraints, responsible owner, and unresolved material decisions. Use
`taskspec example intent --out intent.md`, then
`taskspec decompose init <id> --intent-file intent.md`. Standard input is accepted
as `--intent-file -`. An incident JSON file can be the explicit intake source.

Research the repository and author the decomposition recipe. Evidence needs source
identifiers and exact digests for local files. Missing ownership, evidence, or
material decisions is a blocker to explain, not a reason to invent an answer.
External information remains reported until independently checked. Store decisions
in the recipe so another harness can recover them without conversation history.
