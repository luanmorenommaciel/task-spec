# Planning validation

- `decompose init rate-limiting --intent-file tests/fixtures/toolkit/blueprint.md`: `DECOMPOSE=INTENT`.
- `decompose prepare rate-limiting --recipe tasks/.plans/rate-limiting/recipe.json`: exit 1, `DECOMPOSE=INVALID unaccepted_decision: Seam SEAM-RATE-LIMITING depends on decisions that are not accepted.`
- The proposed decisions remain proposed; ownership and product/harness objections remain OPEN. Preparation was not forced past this blocker.
- `status --initiative rate-limiting`: `DECOMPOSE=INTENT`, `plan_missing`. Native delivery topology has not been generated.
- `graph --initiative rate-limiting --view capabilities`: unavailable because no compiled `task-plan.json` exists.
- Local checks confirmed the evidence SHA-256 matches the source, intake is byte-identical to the blueprint, and all decisions/objections retain their unresolved states.

The reviewable authored proposal is `proposal.md`; its native input is `recipe.json`. No approval, compilation, materialization, sealing, execution or acceptance was performed. Future implementation tests were specified, not run.
