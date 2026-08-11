#!/usr/bin/env python3
"""Small stdlib-only data helpers shared by TaskPlan and TaskHandoff.

The YAML reader intentionally supports the Task-Spec contract subset: indented
mappings and lists plus JSON-compatible scalars. JSON documents are accepted
directly. It is not a general YAML implementation and rejects tabs, anchors,
tags, and block scalars so the same manifest has one predictable meaning on
every harness.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any, Iterable

SENSITIVE_KEY = re.compile(
    r"(?:^|[_-])(?:api[_-]?key|access[_-]?token|auth[_-]?token|secret|password|credentials?|private[_-]?key)(?:$|[_-])",
    re.I,
)


class DataError(ValueError):
    pass


def _scalar(raw: str) -> Any:
    value = raw.strip()
    if value == "":
        return None
    if value in {"|", ">"}:
        raise DataError("block scalars are not supported; use a quoted string")
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() in {"null", "~"}:
        return None
    if re.fullmatch(r"-?[0-9]+", value):
        return int(value)
    if value.startswith(("[", "{", '"')):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                return [] if not inner else [_scalar(item) for item in inner.split(",")]
            raise DataError(f"invalid JSON-compatible scalar {value!r}: {exc.msg}") from exc
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def _split_key(text: str, line_number: int) -> tuple[str, str]:
    if ":" not in text:
        raise DataError(f"line {line_number}: expected key: value")
    key, value = text.split(":", 1)
    key = key.strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", key):
        raise DataError(f"line {line_number}: invalid key {key!r}")
    return key, value.strip()


def parse_yaml_subset(text: str) -> Any:
    rows: list[tuple[int, str, int]] = []
    for number, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw:
            raise DataError(f"line {number}: tabs are not allowed")
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or stripped == "---":
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent % 2:
            raise DataError(f"line {number}: indentation must use multiples of two spaces")
        rows.append((indent, raw[indent:], number))

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(rows) or rows[index][0] < indent:
            return {}, index
        is_list = rows[index][0] == indent and rows[index][1].startswith("- ")
        container: Any = [] if is_list else {}
        while index < len(rows):
            current_indent, content, number = rows[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise DataError(f"line {number}: unexpected indentation")
            if is_list:
                if not content.startswith("- "):
                    break
                item_text = content[2:].strip()
                if not item_text:
                    item, index = parse_block(index + 1, indent + 2)
                    container.append(item)
                    continue
                if ":" in item_text:
                    key, raw_value = _split_key(item_text, number)
                    item = {key: _scalar(raw_value)}
                    index += 1
                    if index < len(rows) and rows[index][0] > indent:
                        extra, index = parse_block(index, indent + 2)
                        if not isinstance(extra, dict):
                            raise DataError(f"line {number}: list mapping continuation must be a mapping")
                        item.update(extra)
                    container.append(item)
                else:
                    container.append(_scalar(item_text))
                    index += 1
            else:
                if content.startswith("- "):
                    break
                key, raw_value = _split_key(content, number)
                index += 1
                if raw_value == "":
                    if index < len(rows) and rows[index][0] > indent:
                        value, index = parse_block(index, indent + 2)
                    else:
                        value = {}
                else:
                    value = _scalar(raw_value)
                container[key] = value
        return container, index

    if not rows:
        raise DataError("document is empty")
    result, final = parse_block(0, rows[0][0])
    if final != len(rows):
        raise DataError(f"line {rows[final][2]}: could not parse document")
    return result


def load_document(path: str | pathlib.Path) -> Any:
    source = pathlib.Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise DataError(f"cannot read {source}: {exc}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return parse_yaml_subset(text)


def frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---\n"):
        raise DataError("Task-Spec has no leading frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise DataError("Task-Spec frontmatter is not closed")
    parsed = parse_yaml_subset(text[4:end])
    if not isinstance(parsed, dict):
        raise DataError("Task-Spec frontmatter must be a mapping")
    return parsed


def sha256_file(path: str | pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sensitive_key_paths(value: Any, prefix: str = "$") -> list[str]:
    """Return structural paths whose key names look credential-bearing."""
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{prefix}.{key}"
            if SENSITIVE_KEY.search(str(key)):
                found.append(child_path)
            found.extend(sensitive_key_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(sensitive_key_paths(child, f"{prefix}[{index}]"))
    return found


def require_keys(mapping: dict[str, Any], keys: Iterable[str], where: str) -> list[str]:
    return [f"{where}: missing {key}" for key in keys if key not in mapping]


def yaml_scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def yaml_inline_list(values: Iterable[Any]) -> str:
    return "[" + ", ".join(yaml_scalar(item) for item in values) + "]"
