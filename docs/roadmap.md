# Roadmap — after the v4 evidence foundation

Engine 3.8 completes the local revision-bound trust chain around the opt-in v4
evidence foundation: HMAC v3 authorization, attempt-bound handoffs/receipts,
commit-aware scope checks, durable acceptance records, a derived graph, and
read-only lifecycle status. Format v3 remains the authoring default.

The remaining work requires external systems or broader runtime ownership:

- execute and retain real-engine runs across all nine declared families;
- integrate a production sandbox that can truthfully issue environment receipts;
- add remote trust distribution and policy for Ed25519 keys and revocation;
- graduate repository-specific Python, JavaScript, Go, and Bash mutation patches
  from the checked-in experimental manifest shapes;
- validate bridges against third-party A2A/MCP implementations—the current
  envelopes preserve Task-Spec identity but are not a certification claim;
- publish a conformance-badge process backed by retained external evidence.

Any future format change still requires schema, conformance, template,
validator, examples, and changelog updates together—see `AGENTS.md`.
