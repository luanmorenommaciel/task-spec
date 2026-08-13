# Optional research provider packs

These adapters are non-normative authoring inputs. Core never installs, calls,
or authenticates Firecrawl, Tavily, or Exa. A harness explicitly selects a
provider, keeps credentials in that provider's CLI/MCP/environment, and converts
the result to `AuthoringEvidence/v1`. Evidence may inform context and guardrails;
it does not become an acceptance criterion without human review.

The bundled adapters are deterministic fakes for CI. They prove the shared
contract and named failure states without a network or secret. Live support must
not be claimed until a provider-specific smoke gate has retained evidence.
Support is version-scoped: `validate-smoke.py` must accept retained
`ProviderSmokeEvidence/v1` for the exact advertised adapter version. Fake
adapters do not count as live-provider evidence.

```bash
integrations/research/firecrawl/fake-adapter.sh "atomic task research"
integrations/research/tavily/fake-adapter.sh "atomic task research"
integrations/research/exa/fake-adapter.sh "atomic task research"
python3 integrations/research/validate-evidence.py evidence.json
```

Contract: [`AuthoringEvidence v1`](../../spec/schemas/authoring-evidence.schema.json).
