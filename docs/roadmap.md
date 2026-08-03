# Roadmap — v4 candidates

The full prioritized list lives in [`../TODO.md`](../TODO.md). The format-v4
candidates, summarized:

- **Sealed holdout evals (P1-1).** A second, HMAC-sealed eval block revealed
  only to the acceptance gate — workers cannot game evals they cannot read.
  The single biggest integrity upgrade on the table.
- **Graded `check_type` (P1-2).** Beyond `deterministic`: `graded` (model-judged
  rubric) and `human`, with a judge runner — closes the intent-faithfulness gap
  bash cannot reach.
- **Mutation matrix (P1-3).** Generalize `--gold-sanity` from one baseline to
  N injected realistic bugs; an eval that can't be forced RED is rejected at
  gate time.
- **Key rotation & identity (P1-4).** Rotation, per-author signing identity,
  remote verification for cross-repo fleet dispatch — hardens the envelope the
  v4 holdout trick relies on.

Each is format-affecting, so each requires: schema update (`spec/schemas/`),
conformance fixtures (`spec/conformance/`), and a CHANGELOG entry — see
`AGENTS.md`.
