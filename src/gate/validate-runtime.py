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
    errors=[]
    if not isinstance(maximum,int) or maximum < 1: errors.append("retry_policy.max_iterations must be a positive integer")
    elif not isinstance(budget,int) or maximum > budget: errors.append("retry_policy.max_iterations must not exceed signed budget_iterations")
    if not isinstance(breaker,int) or breaker < 1: errors.append("retry_policy.circuit_breaker_no_progress must be a positive integer")
    elif isinstance(maximum,int) and breaker > maximum: errors.append("circuit_breaker_no_progress must not exceed max_iterations")
except (OSError,ValueError,DataError,AttributeError) as exc: errors=[str(exc)]
for error in errors: print(error)
raise SystemExit(1 if errors else 0)
