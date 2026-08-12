#!/usr/bin/env python3
"""Supplemental semantic validation for opt-in Task-Spec format v4."""

from __future__ import annotations

import pathlib
import re
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "lib"))
from taskspec_data import DataError, frontmatter, parse_yaml_subset, sensitive_key_paths  # noqa: E402


def section(text: str, name: str) -> str:
    match = re.search(rf"^##\s+{re.escape(name)}\s*$\n(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    return match.group(1).strip() if match else ""


def validation_card(text: str) -> dict[str, Any]:
    body = section(text, "Validation Card")
    match = re.search(r"```ya?ml\s*\n(.*?)```", body, re.S | re.I)
    if not match: raise DataError("Validation Card has no YAML fence")
    value = parse_yaml_subset(match.group(1))
    if not isinstance(value, dict): raise DataError("Validation Card must be a mapping")
    return value


def required(policy: Any) -> bool:
    return isinstance(policy, dict) and policy.get("required") is True


def validate(path: pathlib.Path) -> list[str]:
    text = path.read_text(encoding="utf-8"); fm = frontmatter(text)
    if int(str(fm.get("format_version", 0)).split(".")[0]) != 4: return []
    errors: list[str] = []
    policy = fm.get("evaluation_policy")
    if not isinstance(policy, dict): return ["format v4 requires evaluation_policy"]
    if policy.get("acceptance_scope") not in {"local", "portable", "human-authorized"}:
        errors.append("evaluation_policy.acceptance_scope must be local, portable, or human-authorized")
    if not any(required(policy.get(name)) for name in ("deterministic", "holdout", "graded", "human")):
        errors.append("evaluation_policy must require at least one evaluation class")
    holdout = policy.get("holdout")
    if required(holdout) and not (holdout.get("descriptor_digest") or holdout.get("authorization_ref")):
        errors.append("required holdout policy needs descriptor_digest or authorization_ref")
    graded = policy.get("graded")
    if required(graded):
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(graded.get("rubric_digest", ""))):
            errors.append("required graded policy needs a sha256 rubric_digest")
        if not isinstance(graded.get("threshold"), (int, float)) or not 0 <= graded["threshold"] <= 1:
            errors.append("required graded policy threshold must be between 0 and 1")
    human = policy.get("human")
    if required(human) and not human.get("owner"):
        errors.append("required human policy needs an accountable owner")
    env = fm.get("environment_contract")
    if required(env):
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(env.get("digest", ""))):
            errors.append("required environment_contract needs a sha256 digest")
        if not env.get("ref"):
            errors.append("required environment_contract needs a ref")
    if policy.get("acceptance_scope") == "portable" and not required(env):
        errors.append("portable acceptance requires an enforced environment_contract")
    identity = fm.get("identity_policy")
    if required(identity) and not identity.get("key_id"):
        errors.append("required identity_policy needs a trusted key_id")
    for sensitive in sensitive_key_paths(fm):
        errors.append(f"credential-bearing key is forbidden in Task-Spec frontmatter: {sensitive}")
    try: card = validation_card(text)
    except DataError as exc: errors.append(str(exc)); return errors
    allowed = {"deterministic", "graded", "human"}
    for item in card.get("success_criteria", []):
        if not isinstance(item, dict): continue
        check_type = item.get("check_type", "deterministic")
        if check_type not in allowed: errors.append(f"format v4 success criterion {item.get('id')} has unsupported check_type {check_type!r}")
    questions = section(text, "Open Questions")
    if questions and questions.lower() not in {"none", "(none)", "- (none)"} and fm.get("status") != "blocked":
        errors.append("unresolved Open Questions require status: blocked; an agent may not silently decide them")
    return errors


def main() -> int:
    try: errors = validate(pathlib.Path(sys.argv[1]))
    except (IndexError, OSError, DataError, ValueError) as exc: errors = [str(exc)]
    for error in errors: print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
