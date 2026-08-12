# Roadmap — after the v4 evidence foundation

Engine 3.7 ships the opt-in v4 evidence foundation: holdout commitments,
graded/human/environment receipts, mutation audit, identity receipts, A2A/MCP
bridges, and a multi-engine evidence harness. Format v3 remains supported.

The remaining work requires external systems or broader runtime ownership:

- execute and retain real-engine runs across all nine declared families;
- integrate a production sandbox that can truthfully issue environment receipts;
- add remote trust distribution and policy for Ed25519 keys and revocation;
- add stack-specific mutation and evaluation packs;
- validate bridges against third-party A2A/MCP implementations—the current
  envelopes preserve Task-Spec identity but are not a certification claim;
- publish a conformance-badge process backed by retained external evidence.

Any future format change still requires schema, conformance, template,
validator, examples, and changelog updates together—see `AGENTS.md`.
