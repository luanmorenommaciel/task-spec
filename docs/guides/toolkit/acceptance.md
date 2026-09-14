# First accepted task and evidence

For one small understood change, author `TaskPlan/v1`, preview it with
`taskspec plan --manifest <file>`, and materialize with `taskspec batch --plan <file>`.
Inspect `taskspec validate <spec>`, `taskspec dod <spec>`, and every eval. An eval
must discriminate a real result from a stub; metadata compliance is not behavioral proof.

Record human authorization with `taskspec gate --stamp <spec> --stamp-by <identity>`.
For ordinary tasks, create an attempt handoff using
`taskspec handoff <spec> --backend <backend> --out <path>`, execute within it, and
use canonical `taskspec accept --handoff <path> --stamp <spec>` with the required
receipts and supervisor decision. For managed recipes use the Mesh route in the
execution guide. Failed evals, stale revisions, and missing required attestations
cannot establish acceptance. Never edit sealed evals to make work pass.

`taskspec status --initiative <id>` reconstructs acceptance from canonical records,
separately from lifecycle status. `graph --initiative <id> --view capabilities`
shows explicit integration proof gaps. Passing child tasks does not prove a capability,
a successful pipeline does not establish service health, and acceptance does not
authorize production release.
