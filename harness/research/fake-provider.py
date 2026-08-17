#!/usr/bin/env python3
"""Credential-free deterministic producer for AuthoringEvidence v1 tests."""

import argparse
import hashlib
import json

parser = argparse.ArgumentParser()
parser.add_argument("--provider", required=True, choices=("firecrawl", "tavily", "exa"))
parser.add_argument("--state", default="ok", choices=("ok", "unavailable", "rate_limited", "authentication_failed", "timeout", "schema_drift"))
parser.add_argument("query")
args = parser.parse_args()

source_text = f"deterministic fake evidence for {args.provider}: {args.query}"
source = {
    "url": f"https://example.invalid/{args.provider}/fixture",
    "title": f"{args.provider.title()} offline contract fixture",
    "retrieved_at": "2026-08-11T00:00:00Z",
    "content_digest": hashlib.sha256(source_text.encode()).hexdigest(),
}
document = {
    "contract": "AuthoringEvidence/v1",
    "provider": args.provider,
    "request_id": hashlib.sha256(f"{args.provider}:{args.query}".encode()).hexdigest()[:16],
    "query": args.query,
    "observed_at": "2026-08-11T00:00:00Z",
    "state": args.state,
    "sources": [source] if args.state == "ok" else [],
    "claims": [{"text": source_text, "excerpt": source_text, "source_refs": [0]}] if args.state == "ok" else [],
    "usage": {"requests": 0, "cost": 0, "mode": "offline_fake"},
}
if args.state != "ok":
    document["error"] = f"simulated_{args.state}"
print(json.dumps(document, indent=2))
