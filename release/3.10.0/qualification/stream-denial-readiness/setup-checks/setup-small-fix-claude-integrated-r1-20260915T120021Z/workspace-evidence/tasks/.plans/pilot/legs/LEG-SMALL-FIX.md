---
schema_version: 1
kind: capability-leg
claim: derived
id: LEG-SMALL-FIX
seam_id: SEAM-SMALL-FIX
swimlane_id: LANE-SMALL-FIX
observable_state: Accept valid stdin JSON and reject malformed stdin with the same typed errors as file
  input; preserve file validation.
proof: The declared evaluator succeeds without widening the write surface.
requires: []
produces:
- small-fix verified behavior
tasks:
- id: T-20260914-pilot-small-fix
  title: Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input;
    preserve file validation
  goal: Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve
    file validation.
  done_condition: Accept valid stdin JSON and reject malformed stdin with the same typed errors as file
    input; preserve file validation.
  effort: S
  profile: standard
  execution_backend: claude
  required_tools:
  - git
  - bash
  - python3
  depends_on: []
  touches_paths:
  - src/recipe/recipes.py
  creates_paths: []
  behavior:
  - id: B-1
    given: the registered repository issue and fixed authorized scope
    when: the bounded implementation is independently evaluated
    then: the declared behavior passes without modifying unrelated files or promoting reported evidence
  - id: B-2
    given: the recorded evidence and authorization boundary
    when: the candidate is checked
    then: source evidence is unchanged and no unrelated write is present
  evals:
  - id: eval_1
    description: Independent behavioral proof for small-fix
    bash: '/Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python -c ''import
      hashlib,pathlib,sys; manifest={''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"'':
      ''"''"''5580a3b17085de0837e0181fd8402ed97926d854884756b57ce40b677de2bdca''"''"'', ''"''"''tests/fixtures/toolkit/public-evaluator/spec/conformance/toolkit/execution-recipe.json''"''"'':
      ''"''"''ccf680057d987028e116666849c720ec8ba5ad30216e347ff58c3db40b5fae59''"''"'', ''"''"''tests/fixtures/toolkit/public-evaluator/docs/examples/incident.json''"''"'':
      ''"''"''f95954e02b9e42fab5f661bc087d994acf27061d6a24a27745e0a5a29cde4e8b''"''"''}; contents={p:pathlib.Path(p).read_bytes()
      for p in manifest}; valid=all(not pathlib.Path(p).is_symlink() and hashlib.sha256(contents[p]).hexdigest()==h
      for p,h in manifest.items()); sys.exit("public evaluator integrity check failed") if not valid else
      None; sys.argv=[''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"'',''"''"''small-fix''"''"'',"--root","."];
      exec(compile(contents[''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"''],''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"'',"exec"),{"__name__":"__main__","__file__":''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"''})'''
    verifies:
    - B-1
  - id: eval_2
    description: Declared write surface only
    bash: '/Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python -c ''import
      hashlib,pathlib,sys; manifest={''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"'':
      ''"''"''5580a3b17085de0837e0181fd8402ed97926d854884756b57ce40b677de2bdca''"''"'', ''"''"''tests/fixtures/toolkit/public-evaluator/spec/conformance/toolkit/execution-recipe.json''"''"'':
      ''"''"''ccf680057d987028e116666849c720ec8ba5ad30216e347ff58c3db40b5fae59''"''"'', ''"''"''tests/fixtures/toolkit/public-evaluator/docs/examples/incident.json''"''"'':
      ''"''"''f95954e02b9e42fab5f661bc087d994acf27061d6a24a27745e0a5a29cde4e8b''"''"''}; contents={p:pathlib.Path(p).read_bytes()
      for p in manifest}; valid=all(not pathlib.Path(p).is_symlink() and hashlib.sha256(contents[p]).hexdigest()==h
      for p,h in manifest.items()); sys.exit("public evaluator integrity check failed") if not valid else
      None; sys.argv=[''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"'',''"''"''write-boundary''"''"'',"--root","."];
      exec(compile(contents[''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"''],''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"'',"exec"),{"__name__":"__main__","__file__":''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"''})'''
    verifies:
    - B-2
  - id: eval_3
    description: Registered issue evidence is unchanged
    bash: '/Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python -c ''import
      hashlib,pathlib,sys; manifest={''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"'':
      ''"''"''5580a3b17085de0837e0181fd8402ed97926d854884756b57ce40b677de2bdca''"''"'', ''"''"''tests/fixtures/toolkit/public-evaluator/spec/conformance/toolkit/execution-recipe.json''"''"'':
      ''"''"''ccf680057d987028e116666849c720ec8ba5ad30216e347ff58c3db40b5fae59''"''"'', ''"''"''tests/fixtures/toolkit/public-evaluator/docs/examples/incident.json''"''"'':
      ''"''"''f95954e02b9e42fab5f661bc087d994acf27061d6a24a27745e0a5a29cde4e8b''"''"''}; contents={p:pathlib.Path(p).read_bytes()
      for p in manifest}; valid=all(not pathlib.Path(p).is_symlink() and hashlib.sha256(contents[p]).hexdigest()==h
      for p,h in manifest.items()); sys.exit("public evaluator integrity check failed") if not valid else
      None; sys.argv=[''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"'',''"''"''source-integrity''"''"'',"--root","."];
      exec(compile(contents[''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"''],''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"'',"exec"),{"__name__":"__main__","__file__":''"''"''tests/fixtures/toolkit/public-evaluator/tests/evals/toolkit/evaluate_issue.py''"''"''})'''
    verifies:
    - B-2
  anti_patterns:
  - action: weaken the independent evaluator
    reason: it would invalidate the comparison
    instead: fix the behavior within the declared surface
  - action: expand the scope
    reason: it breaks matched permissions
    instead: report the missing work as a blocker
  - action: claim success without evidence
    reason: a plausible patch does not establish behavior
    instead: run the independent proof and report failures
  do_not_touch:
  - tests/fixtures/toolkit/pilot-issue.json
  - tests/fixtures/toolkit/public-evaluator
  - tasks
  rollback: Revert only this isolated candidate change.
  observability: Retained provider output, evaluation result, and prospective event journal.
  execution_recipe: diagnose-repair-verify
  proves_capabilities:
  - LEG-SMALL-FIX
source_seam_sha256: d59804b3b01430127b3d08a6aa1ce6adbcd748656fb7fe14e415fcb30c043d52
---
# Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation.

## Observable proof

The declared evaluator succeeds without widening the write surface.

## Runnable leaves

- `T-20260914-pilot-small-fix` — Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation: Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation.

The leg names a capability state, not an activity. Each leaf owns one coherent,
independently provable done-condition.
