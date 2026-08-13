#!/usr/bin/env python3
"""Validate retained ProviderSmokeEvidence/v1 for one exact adapter version."""
import argparse,json,pathlib,sys
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("evidence"); parser.add_argument("--provider",required=True,choices=["firecrawl","tavily","exa"]); parser.add_argument("--adapter-version",required=True)
args=parser.parse_args()
try:
    value=json.loads(pathlib.Path(args.evidence).read_text(encoding="utf-8"))
    if value.get("contract")!="ProviderSmokeEvidence/v1": raise ValueError("contract must be ProviderSmokeEvidence/v1")
    if value.get("provider")!=args.provider or value.get("adapter_version")!=args.adapter_version: raise ValueError("smoke evidence does not match the exact provider adapter version")
    if value.get("result")!="pass": raise ValueError("smoke result is not pass")
    if not str(value.get("evidence_digest","")).startswith("sha256:"): raise ValueError("evidence_digest is required")
    print(f"PROVIDER_SMOKE=SUPPORTED provider={args.provider} adapter_version={args.adapter_version}")
except (OSError,ValueError,json.JSONDecodeError) as exc:
    print(f"PROVIDER_SMOKE=UNSUPPORTED error={exc}",file=sys.stderr); raise SystemExit(1)
