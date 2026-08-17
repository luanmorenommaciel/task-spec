#!/usr/bin/env python3
"""Validate the portable AuthoringEvidence v1 boundary without dependencies."""

import json
import pathlib
import re
import sys

STATES = {"ok", "unavailable", "rate_limited", "authentication_failed", "timeout", "schema_drift"}
required = {"contract", "provider", "request_id", "query", "observed_at", "state", "sources", "claims"}
path = pathlib.Path(sys.argv[1]) if len(sys.argv) == 2 else None
if path is None:
    print("usage: validate-evidence.py <evidence.json>", file=sys.stderr)
    raise SystemExit(2)
try:
    doc = json.loads(path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    print(f"EVIDENCE=INVALID\nerror: {exc}", file=sys.stderr)
    raise SystemExit(1)
if not isinstance(doc, dict):
    print("EVIDENCE=INVALID\nerror: document must be an object", file=sys.stderr)
    raise SystemExit(1)
errors = []
errors += [f"missing {key}" for key in sorted(required - set(doc))]
errors += [f"unknown field {key}" for key in sorted(set(doc) - (required | {"usage", "error"}))]
if doc.get("contract") != "AuthoringEvidence/v1": errors.append("contract must be AuthoringEvidence/v1")
if doc.get("state") not in STATES: errors.append("unknown state")
for field in ("provider", "request_id", "query", "observed_at"):
    if not isinstance(doc.get(field), str): errors.append(f"{field} must be a string")
if not isinstance(doc.get("sources"), list) or not isinstance(doc.get("claims"), list): errors.append("sources and claims must be lists")
for index, source in enumerate(doc.get("sources", [])):
    if not isinstance(source, dict): errors.append(f"sources[{index}] must be an object"); continue
    if not all(key in source for key in ("url", "title", "retrieved_at", "content_digest")): errors.append(f"sources[{index}] incomplete")
    elif not re.fullmatch(r"[0-9a-f]{64}", str(source["content_digest"])): errors.append(f"sources[{index}].content_digest invalid")
for index, claim in enumerate(doc.get("claims", [])):
    if not isinstance(claim, dict): errors.append(f"claims[{index}] must be an object"); continue
    if not isinstance(claim.get("text"), str): errors.append(f"claims[{index}].text must be a string")
    if not isinstance(claim.get("source_refs"), list): errors.append(f"claims[{index}].source_refs must be a list")
    for ref in claim.get("source_refs", []):
        if not isinstance(ref, int) or ref < 0 or ref >= len(doc.get("sources", [])): errors.append(f"claims[{index}] has invalid source ref {ref}")
if doc.get("state") != "ok" and (doc.get("sources") or doc.get("claims")): errors.append("failure states must not masquerade as evidence")
if doc.get("state") != "ok" and not isinstance(doc.get("error"), str): errors.append("failure states require a named error")

sensitive = re.compile(r"(?:^|[_-])(?:api[_-]?key|access[_-]?token|auth[_-]?token|secret|password|credentials?|private[_-]?key)(?:$|[_-])", re.I)
def scan_keys(value, prefix="$"):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{prefix}.{key}"
            if sensitive.search(str(key)): found.append(child_path)
            found.extend(scan_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value): found.extend(scan_keys(child, f"{prefix}[{index}]") )
    return found
credential_paths = scan_keys(doc)
if credential_paths: errors.append(f"credential-bearing keys are forbidden: {credential_paths}")
if errors:
    for error in errors: print(f"ERROR: {error}", file=sys.stderr)
    print("EVIDENCE=INVALID")
    raise SystemExit(1)
print(f"AuthoringEvidence v1: {doc['provider']} state={doc['state']} sources={len(doc['sources'])} claims={len(doc['claims'])}")
print("EVIDENCE=OK")
