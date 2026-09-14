#!/usr/bin/env python3
"""Optional v3 recipe conformance without changing legacy format readers."""
from pathlib import Path
import copy,json,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'src/recipe'),str(ROOT/'tests')]
from recipes import validate
from schema_contracts import validate_instance, Invalid
fixture=json.loads((Path(__file__).parent/'execution-recipe.json').read_text())
validate_instance(fixture,'task-execution-recipe.schema.json')
assert not validate(fixture,fixture['eval_ids'],15)
lineage=json.loads((Path(__file__).parent/'task-plan-lineage.json').read_text())
validate_instance(lineage,'decompose-task-lineage.schema.json')
for remove in ('unit_id','seam','swimlane','leg','source_sha256'):
    bad=copy.deepcopy(lineage);del next(iter(bad['units'].values()))[remove]
    try:validate_instance(bad,'decompose-task-lineage.schema.json')
    except Invalid:pass
    else:raise AssertionError('incomplete lineage accepted: '+remove)
for schema_name in ('agent-contract','task-plan','task-spec-frontmatter'):
    schema=json.loads((ROOT/'spec/schemas'/f'{schema_name}.schema.json').read_text())
    for key,name in [('executionRecipe','task-execution-recipe'),('nativeProvenance','task-plan-provenance')]:
        if key not in schema.get('$defs',{}):continue
        standalone=json.loads((ROOT/'spec/schemas'/f'{name}.schema.json').read_text())
        assert schema['$defs'][key]=={k:v for k,v in standalone.items() if k not in ('$schema','$id')}
for patch in ({'max_rounds':16},{'runner':'nested-runner'},{'no_progress_rounds':4},{'eval_ids':['eval_missing']}):
    bad=copy.deepcopy(fixture);bad.update(patch)
    assert validate(bad,fixture['eval_ids'],15),patch
capability={"contract":"ExecutorCapability/v1","adapter":"omp-rpc","adapter_version":"omp/17.3.3","harness":"omp","available":True,"assurance_modes":["autonomous"],"tools":["read","edit","shell"],"network":"attempt_proxy_only","limits":{"max_parallel":1,"max_output_bytes":1048576},"observed_at":"2026-09-14T00:00:00Z","managed_recipe_modes":["autonomous"],"managed_recipe_capabilities":["managed_recipe_v1","persistent_round_budget","signed_timeout","attested_execution"]}
validate_instance(capability,'executor-capability.schema.json')
print('TOOLKIT_CONFORMANCE=PASS optional recipe, self-contained schemas, and complete lineage shape')
