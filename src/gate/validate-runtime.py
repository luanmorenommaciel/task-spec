#!/usr/bin/env python3
"""Validate retry policy against the signed iteration budget."""

from __future__ import annotations
import pathlib,re,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"/"lib"))
from taskspec_data import DataError,frontmatter,parse_yaml_subset  # noqa: E402

try:
    path=pathlib.Path(sys.argv[1]); text=path.read_text(encoding="utf-8"); fm=frontmatter(text)
    match=re.search(r"^##\s+Validation Card\s*$.*?```ya?ml\s*\n(.*?)```",text,re.M|re.S|re.I)
    if not match: raise DataError("Validation Card has no YAML fence")
    card=parse_yaml_subset(match.group(1)); retry=card.get("retry_policy",{})
    maximum=retry.get("max_iterations"); breaker=retry.get("circuit_breaker_no_progress")
    budget=fm.get("budget_iterations")
    sys.path.insert(0,str(ROOT/"src/recipe"))
    sys.path.insert(0,str(ROOT/"src/security"))
    from recipes import validate as validate_recipe
    from provenance import verify_task
    from workspace import resolve_workspace
    errors=[]
    for field in ("shared_resources", "proves_capabilities", "sdlc_stages"):
        if field in fm and (not isinstance(fm[field], list) or any(not isinstance(x, str) or not x.strip() for x in fm[field]) or len({str(x) for x in fm[field]}) != len(fm[field])):
            errors.append(field + " must contain unique nonblank strings")
    if isinstance(fm.get("sdlc_stages"), list) and any(stage not in ("plan", "design", "build", "test", "deploy", "maintain") for stage in fm["sdlc_stages"]):
        errors.append("unknown SDLC stage")
    recipe=card.get("agent_contract",{}).get("execution_recipe")
    if recipe is not None:
        eval_ids=re.findall(r"^eval_([0-9]+)\(\)",text,re.M)
        errors.extend(validate_recipe(recipe,["eval_"+x for x in eval_ids],budget))
    if fm.get("provenance") is not None:
        try: verify_task(resolve_workspace(path),str(fm.get("id")),fm["provenance"])
        except (ValueError,OSError) as error: errors.append(str(error))
    if not isinstance(maximum,int) or maximum < 1: errors.append("retry_policy.max_iterations must be a positive integer")
    elif not isinstance(budget,int) or maximum > budget: errors.append("retry_policy.max_iterations must not exceed signed budget_iterations")
    if not isinstance(breaker,int) or breaker < 1: errors.append("retry_policy.circuit_breaker_no_progress must be a positive integer")
    elif isinstance(maximum,int) and breaker > maximum: errors.append("circuit_breaker_no_progress must not exceed max_iterations")
except (OSError,ValueError,DataError,AttributeError) as exc: errors=[str(exc)]
for error in errors: print(error)
raise SystemExit(1 if errors else 0)
