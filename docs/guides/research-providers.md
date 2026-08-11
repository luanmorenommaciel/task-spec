# Research providers

Firecrawl, Tavily, and Exa are optional non-normative sources. A harness may
call one only when the user or repository configuration selects it. Credentials
remain in the provider CLI, MCP client, or environment.

Every provider output must normalize to `AuthoringEvidence/v1`:

- provider, request id, query, and observation time;
- source URL, title, retrieval time, and content digest;
- bounded claims/excerpts with source references;
- optional provider usage/cost;
- explicit `unavailable`, `rate_limited`, `authentication_failed`, `timeout`,
  and `schema_drift` states.

```bash
integrations/research/exa/fake-adapter.sh "query" > evidence.json
python3 integrations/research/validate-evidence.py evidence.json
```

The repository currently proves only offline fake adapters. Do not describe a
provider as live-supported until its real smoke gate retains current evidence.
