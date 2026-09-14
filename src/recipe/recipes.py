#!/usr/bin/env python3
"""Resolve portable, immutable execution guidance; never execute a recipe here."""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/lib"))
from taskspec_data import DataError, load_document, parse_yaml_subset  # noqa: E402
from taskspec_data import _json_object, _reject_json_constant  # noqa: E402

CONTRACT = "TaskExecutionRecipe/v1"
STRATEGIES = {
    "direct": ["Read the authorized context and implement the bounded change.", "Verify the declared behavior and report evidence."],
    "plan-execute-verify": ["Inspect the relevant evidence and record a concise implementation plan.", "Implement the plan within the authorized write surface.", "Verify behavior and the nearest affected flows."],
    "diagnose-repair-verify": ["Reproduce the failure and gather evidence before choosing a cause.", "Repair the evidenced cause within scope.", "Verify the reproduction and affected regression checks."],
    "test-first": ["Establish a discriminating behavioral check before implementation.", "Implement the bounded behavior without weakening the sealed acceptance checks.", "Run the behavioral checks and relevant regressions."],
    "research-synthesize-verify": ["Inspect authoritative sources and record their revisions and evidence limits.", "Synthesize conclusions with source references and explicit uncertainty.", "Verify the claims and requested deliverable against the declared checks."],
}


def resolve(strategy: str, eval_ids: list[str], budget: int = 15) -> dict:
    if strategy not in STRATEGIES:
        raise DataError(f"unknown strategy {strategy!r}; use taskspec recipe list")
    if type(budget) is not int or budget < 1:
        raise DataError("recipe requires a positive signed iteration budget")
    rounds = min(3, budget)
    return {
        "contract": CONTRACT, "strategy": strategy, "strategy_version": "1.0.0",
        "steps": copy.deepcopy(STRATEGIES[strategy]),
        "context": ["TaskHandoff", "authorized Task-Spec", "declared source evidence"],
        "artifacts": ["scoped changes", "evaluation evidence", "concise result"],
        "eval_ids": list(eval_ids), "max_rounds": rounds,
        "no_progress_rounds": min(2, rounds),
        "stop_on": ["scope_violation", "authority_changed", "environment_unverified", "budget_exhausted", "cancelled"],
        "on_failure": "park_with_context", "runner": "taskmesh",
        "required_capabilities": ["managed_recipe_v1", "persistent_round_budget", "signed_timeout"],
    }


def validate(recipe: object, eval_ids: list[str], budget: int) -> list[str]:
    if not isinstance(recipe, dict):
        return ["execution_recipe must be a resolved mapping"]
    required = set(resolve("direct", ["eval_1"]))
    errors = []
    if set(recipe) != required:
        errors.append("execution_recipe fields must match TaskExecutionRecipe/v1")
    if recipe.get("contract") != CONTRACT or recipe.get("runner") != "taskmesh":
        errors.append("execution_recipe requires TaskExecutionRecipe/v1 and the taskmesh runner")
    if not isinstance(recipe.get("strategy"), str) or not re.fullmatch(r"[a-z][a-z0-9-]*", recipe.get("strategy", "")):
        errors.append("recipe strategy must be a stable name")
    if not isinstance(recipe.get("strategy_version"), str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", recipe.get("strategy_version", "")):
        errors.append("recipe strategy_version must be pinned")
    for field in ("steps", "context", "artifacts", "eval_ids", "stop_on", "required_capabilities"):
        items = recipe.get(field)
        if not isinstance(items, list) or not items or any(not isinstance(x, str) or not x.strip() for x in items):
            errors.append(f"recipe {field} must be a nonempty list of strings")
    ids = recipe.get("eval_ids", [])
    if isinstance(ids, list) and (len(ids) != len(set(str(x) for x in ids)) or set(str(x) for x in ids) != set(eval_ids)):
        errors.append("recipe eval_ids must cover exactly the declared evals")
    rounds, breaker = recipe.get("max_rounds"), recipe.get("no_progress_rounds")
    if type(rounds) is not int or type(budget) is not int or not 1 <= rounds <= budget:
        errors.append("recipe max_rounds must fit the signed iteration budget")
    if type(breaker) is not int or type(rounds) is not int or not 1 <= breaker <= rounds:
        errors.append("recipe no_progress_rounds must fit max_rounds")
    canonical = resolve("direct", ["eval_1"])
    for field in ("stop_on", "on_failure"):
        if recipe.get(field) != canonical[field]:
            errors.append(f"recipe {field} cannot weaken the managed execution boundary")
    capabilities = recipe.get("required_capabilities")
    if isinstance(capabilities, list) and all(isinstance(item, str) for item in capabilities):
        if len(set(capabilities)) != len(capabilities) or not set(canonical["required_capabilities"]) <= set(capabilities):
            errors.append("recipe required_capabilities cannot omit mandatory enforcement or contain duplicates")
    return errors


def from_spec(text: str) -> tuple[dict | None, dict]:
    match = re.search(r"^##\s+Validation Card\s*$.*?```ya?ml\s*\n(.*?)```", text, re.M | re.S)
    if not match:
        raise DataError("Validation Card has no YAML fence")
    card = parse_yaml_subset(match.group(1))
    return card.get("agent_contract", {}).get("execution_recipe"), card


def load_input(source: str) -> object:
    if source != "-":
        return load_document(source)
    text = sys.stdin.read()
    if not text.strip():
        raise DataError("no recipe on standard input; pipe a JSON or YAML document to recipe validate -")
    # Standard input must parse exactly as strictly as load_document does for a
    # file: duplicate keys and ambiguous JSON constants stay rejected.
    try:
        return json.loads(text, object_pairs_hook=_json_object, parse_constant=_reject_json_constant)
    except json.JSONDecodeError:
        return parse_yaml_subset(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("list")
    show = sub.add_parser("show"); show.add_argument("strategy", choices=sorted(STRATEGIES))
    check = sub.add_parser("validate"); check.add_argument("file", help="recipe document, or - to read standard input"); check.add_argument("--budget", type=int, default=15)
    args = parser.parse_args()
    try:
        if args.action == "list":
            data = {"contract": "TaskRecipeCatalog/v1", "strategies": [{"name": name, "version": "1.0.0", "summary": steps[0]} for name, steps in STRATEGIES.items()]}
        elif args.action == "show":
            data = resolve(args.strategy, ["eval_1"])
        else:
            data = load_input(args.file)
            errors = validate(data, data.get("eval_ids", []) if isinstance(data, dict) else [], args.budget)
            if errors:
                raise DataError("; ".join(errors))
            data = {"contract": "TaskRecipeValidation/v1", "valid": True}
        if os.environ.get("TASKSPEC_JSON_MODE") == "1" or args.action == "show":
            print(json.dumps(data, indent=2))
        elif args.action == "list":
            for row in data["strategies"]:
                print(f"{row['name']}@{row['version']}  {row['summary']}")
        else:
            print("RECIPE=VALID")
        return 0
    except (OSError, ValueError) as exc:
        print(f"RECIPE=INVALID {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
