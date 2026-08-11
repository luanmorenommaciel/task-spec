# Repository scan before authoring

A useful TaskPlan begins with repository evidence, not guessed file paths.
Before proposing units, the installed skill should identify:

1. repository-local instructions and the build/test commands they require;
2. the smallest existing vertical slice that resembles the requested outcome;
3. authoritative schemas, interfaces, and ownership boundaries;
4. candidate `touches_paths`, `creates_paths`, and explicit do-not-touch paths;
5. existing tests that can become discriminating evals;
6. dependency edges and likely write conflicts between proposed leaves.

The scan is read-only. Record durable findings in TaskPlan context or a cited
source note; do not dump an unbounded repository transcript into every leaf.
External research is a separate, explicitly selected input normalized as
`AuthoringEvidence/v1`.

After the scan, run `taskspec plan --manifest <file>`. The preview validates
only declared units and never fills gaps with invented work.
