# Topic-to-canonical-anchor map

| Topic | Canonical anchor | Source | Why |
| --- | --- | --- | --- |
| Authority and scope | [GM-002](../GRAND_MASTER.md#gm-002-authority-order), [GM-003](../GRAND_MASTER.md#gm-003-product-purpose-and-boundaries) | AGENTS.md, project descriptor | Check intent and scope |
| Ownership and preservation | [GM-004](../GRAND_MASTER.md#gm-004-architecture-and-writers), [GM-006](../GRAND_MASTER.md#gm-006-invariants-and-acceptance) | ARCHITECTURE_MAP.md, .agent_rules/10-preservation.md | Identify protected writer |
| Test and runtime | [GM-007](../GRAND_MASTER.md#gm-007-build-test-run-and-release), [GM-010](../GRAND_MASTER.md#gm-010-failures-and-false-pass) | tests/, KNOWN_ISSUES.md | Reproduce and prove |
| Resume and handoff | [GM-011](../GRAND_MASTER.md#gm-011-agent-operating-laws), [GM-012](../GRAND_MASTER.md#gm-012-continuity-contract) | tools/agentops_state.py | Read checkpoint and publication rules |
| Durable decisions | [GM-008](../GRAND_MASTER.md#gm-008-decisions) | .agentops/manifest.json | Find prior scope decisions |

## Usage examples

For an interrupted handoff, use GM-012. For a map startup change, use GM-004 and GM-007 after checking actual source.
