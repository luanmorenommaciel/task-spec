#!/usr/bin/env python3
"""Dependency-free JSON Schema integrity and checked-in contract fixture checks."""

from __future__ import annotations

from datetime import datetime
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import uuid
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "spec" / "schemas"


class Invalid(ValueError):
    pass


def load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def pointer(value: Any, fragment: str) -> Any:
    current = value
    if fragment in {"", "#"}:
        return current
    if not fragment.startswith("#/"):
        raise Invalid(f"unsupported JSON pointer {fragment!r}")
    for raw in fragment[2:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        current = current[int(key)] if isinstance(current, list) else current[key]
    return current


def resolve(ref: str, schema_path: pathlib.Path, document: Any) -> tuple[Any, pathlib.Path, Any]:
    if ref.startswith("#"):
        return pointer(document, ref), schema_path, document
    raw_path, separator, fragment = ref.partition("#")
    target_path = (schema_path.parent / raw_path).resolve()
    if not target_path.is_file() or SCHEMAS.resolve() not in {target_path.parent, *target_path.parents}:
        raise Invalid(f"unresolvable local schema reference {ref!r} in {schema_path.name}")
    target_document = load(target_path)
    return pointer(target_document, "#" + fragment if separator else ""), target_path, target_document


def is_type(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def validate(value: Any, schema: Any, schema_path: pathlib.Path, document: Any, at: str = "$") -> None:
    if isinstance(schema, bool):
        if not schema:
            raise Invalid(f"{at}: rejected by false schema")
        return
    if not isinstance(schema, dict):
        raise Invalid(f"{at}: schema must be an object or boolean")
    if "$ref" in schema:
        target, target_path, target_document = resolve(schema["$ref"], schema_path, document)
        validate(value, target, target_path, target_document, at)
    if "allOf" in schema:
        for child in schema["allOf"]:
            validate(value, child, schema_path, document, at)
    if "anyOf" in schema:
        if not any(valid(value, child, schema_path, document, at) for child in schema["anyOf"]):
            raise Invalid(f"{at}: does not match anyOf")
    if "oneOf" in schema:
        matches = sum(valid(value, child, schema_path, document, at) for child in schema["oneOf"])
        if matches != 1:
            raise Invalid(f"{at}: expected exactly one oneOf match, found {matches}")
    if "not" in schema and valid(value, schema["not"], schema_path, document, at):
        raise Invalid(f"{at}: matches forbidden schema")
    if "if" in schema:
        branch = schema.get("then") if valid(value, schema["if"], schema_path, document, at) else schema.get("else")
        if branch is not None:
            validate(value, branch, schema_path, document, at)
    if "const" in schema and value != schema["const"]:
        raise Invalid(f"{at}: expected const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise Invalid(f"{at}: value is not in enum")
    expected_type = schema.get("type")
    if expected_type:
        choices = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(is_type(value, choice) for choice in choices):
            raise Invalid(f"{at}: expected type {expected_type!r}")
    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        if missing:
            raise Invalid(f"{at}: missing required {missing}")
        properties = schema.get("properties", {})
        patterns = schema.get("patternProperties", {})
        for key, child in value.items():
            if key in properties:
                validate(child, properties[key], schema_path, document, f"{at}.{key}")
                continue
            matched = False
            for pattern, child_schema in patterns.items():
                if re.search(pattern, key):
                    validate(child, child_schema, schema_path, document, f"{at}.{key}")
                    matched = True
            if not matched and schema.get("additionalProperties") is False:
                raise Invalid(f"{at}: unknown property {key!r}")
            if not matched and isinstance(schema.get("additionalProperties"), dict):
                validate(child, schema["additionalProperties"], schema_path, document, f"{at}.{key}")
        if "minProperties" in schema and len(value) < schema["minProperties"]:
            raise Invalid(f"{at}: too few properties")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise Invalid(f"{at}: too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise Invalid(f"{at}: too many items")
        if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            raise Invalid(f"{at}: items are not unique")
        if isinstance(schema.get("items"), dict):
            for index, child in enumerate(value):
                validate(child, schema["items"], schema_path, document, f"{at}[{index}]")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise Invalid(f"{at}: string is too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise Invalid(f"{at}: string is too long")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise Invalid(f"{at}: string does not match {schema['pattern']!r}")
        if schema.get("format") == "uuid":
            if str(uuid.UUID(value)) != value.lower():
                raise Invalid(f"{at}: invalid canonical UUID")
        if schema.get("format") == "date-time":
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise Invalid(f"{at}: date-time has no offset")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise Invalid(f"{at}: below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise Invalid(f"{at}: above maximum")


def valid(value: Any, schema: Any, schema_path: pathlib.Path, document: Any, at: str) -> bool:
    try:
        validate(value, schema, schema_path, document, at)
        return True
    except (Invalid, KeyError, ValueError, TypeError):
        return False


def validate_file(instance_path: pathlib.Path, schema_name: str) -> None:
    schema_path = SCHEMAS / schema_name
    schema = load(schema_path)
    validate(load(instance_path), schema, schema_path, schema)


def validate_instance(value: Any, schema_name: str) -> None:
    schema_path = SCHEMAS / schema_name
    schema = load(schema_path)
    validate(value, schema, schema_path, schema)


def main() -> int:
    schema_paths = sorted(SCHEMAS.glob("*.schema.json"))
    ids: dict[str, str] = {}
    for path in schema_paths:
        schema = load(path)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise Invalid(f"{path.name}: missing Draft 2020-12 declaration")
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise Invalid(f"{path.name}: missing $id")
        if schema_id in ids:
            raise Invalid(f"duplicate $id {schema_id!r}: {ids[schema_id]} and {path.name}")
        ids[schema_id] = path.name
        for ref in refs(schema):
            resolve(ref, path, schema)
    validate_file(ROOT / "docs" / "examples" / "task-handoff.json", "task-handoff.schema.json")
    validate_file(ROOT / "docs" / "examples" / "authoring-evidence.json", "authoring-evidence.schema.json")
    for path in sorted((ROOT / "integrations" / "mutations").glob("*.json")):
        validate_file(path, "mutation-matrix.schema.json")
    fixture = ROOT / "tests" / "fixtures" / "T-20260603-stamp-then-verify.md"
    task_revision = json.loads(subprocess.check_output(
        [sys.executable, str(ROOT / "src" / "security" / "task_revision.py"), str(fixture)], text=True,
    ))
    validate_instance(task_revision, "task-revision.schema.json")
    with tempfile.TemporaryDirectory(prefix="taskspec-schema-") as raw:
        backlog = pathlib.Path(raw) / "tasks"
        backlog.mkdir()
        (backlog / fixture.name).write_bytes(fixture.read_bytes())
        graph = json.loads(subprocess.check_output(
            [sys.executable, str(ROOT / "src" / "graph" / "task_graph.py"), "--backlog", str(backlog), "--json"], text=True,
        ))
    validate_instance(graph, "task-graph-view.schema.json")
    digest = "sha256:" + "a" * 64
    validate_instance({
        "contract": "TaskStatus/v1", "task_id": "T-20260603-stamp-then-verify", "path": str(fixture),
        "lifecycle": "ready", "authorization": {"scheme": "hmac-sha256-v3", "tier": 1, "verification": "verified", "stale": False, "task_revision_digest": digest},
        "graph": {"revision_digest": digest, "projection_digest": None, "stale": True, "issues": [], "blockers": []},
        "evidence": {"missing_or_mismatched": [], "authoring_refs": []},
        "acceptance": {"accepted": False, "record": None, "record_matches": False, "record_error": None},
        "next_command": "taskspec rebuild-state",
    }, "task-status.schema.json")
    validate_instance({
        "contract": "AcceptanceRecord/v1",
        "subject": {"task_id": "T-20260603-stamp-then-verify", "task_revision_digest": digest, "authorization_ref": "hmac-sha256-v3:12345678:" + "b" * 64, "attempt_id": "11111111-1111-4111-8111-111111111111", "base_commit": "c" * 40},
        "outcome": {"status": "accepted", "code": "ACCEPTED_TIER_1"},
        "gate_outcomes": {name: {"status": "pass", "code": code} for name, code in (("authorization", "AUTHORIZATION_VALID"), ("evaluation", "EVAL_PASSED"), ("preflight", "PREFLIGHT_PASSED"), ("evidence", "EVIDENCE_SATISFIED"))},
        "receipts": [], "acceptance_tier": 1, "accepted_by": "verifier", "accepted_at": "2026-08-13T12:00:00Z",
    }, "acceptance-record.schema.json")
    print(f"SCHEMAS=READY count={len(schema_paths)} fixtures=10")
    return 0


def refs(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str):
                found.append(child)
            else:
                found.extend(refs(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(refs(child))
    return found


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, json.JSONDecodeError, Invalid, KeyError, ValueError, TypeError) as exc:
        print(f"SCHEMAS=INVALID error={exc}", file=sys.stderr)
        raise SystemExit(1)
