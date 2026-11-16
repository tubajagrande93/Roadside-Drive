# Roadside Drive Grand Master

## GM-001 Identity and scope

Canonical document for `tubajagrande93/Roadside-Drive`. B0 inspected `refs/heads/main` on 2026-11-15 UTC before its first commit (SHA UNKNOWN). Use doctor for the live identity. See [profile](_agent_context/REPO_PROFILE.md) for the evidence. Operator acceptance is PENDING.

## GM-002 Authority order

Latest explicit operator authorization determines scope. Live Git/source establishes current implementation, approved invariants guide intended behavior, and observed runtime can reopen an automated or native gate. Handoffs and summaries are historical evidence.

## GM-003 Product purpose and boundaries

Roadside Drive is a modular real-world driving simulator. Gate 01 builds the [synthetic World Builder foundation](docs/world-builder/ARCHITECTURE.md) with a reproducible metric ScenePackage, reversible corrections, Unreal import, runtime spectator and editor inspection. [Gate 02](docs/world-builder/GATE_02_ENTRY.md) targets an approximately 2.2 km Banja Luka pilot after the corridor, source rights and scoped OSM GO are confirmed. Vehicle physics and production releases remain future work.

## GM-004 Architecture and writers

[Architecture map](_agent_context/ARCHITECTURE_MAP.md) anchors the existing Unreal configuration, Python dependency specification and agent infrastructure. ProjectID and startup map are configuration-owned. The World Builder pipeline owns spatial contracts and source packages. The generated pilot level sets the runtime game mode locally.

## GM-005 Protection and non-goals

Preserve existing Unreal identities, workspace configuration, local environments, raw/cached/processed geographic data and assets. INIT 00B publishes project configuration and documentation. Product implementation, data migration, releases and deployment require separate authority.

## GM-006 Invariants and acceptance

Preserve the local Unreal project identity and LFS mappings, with anchors in the architecture map. Future geometry accuracy and native behavior require measurements and operator acceptance. Harness green status covers only its asserted boundary.

## GM-007 Build, test, run and release

Use the [developer setup](README.md#set-up-a-local-checkout) for Python/GIS and the [pilot runbook](docs/world-builder/OPERATOR_QA.md) for the targeted Unreal smoke. Run `python3 tools/agentops.py verify` for installation consistency and the UAOS contract suite for changes to the infrastructure itself. App packaging, CI and production releases are open.

## GM-008 Decisions

- 2026-11-15, D001. Install the UAOS-B1 source-first method using repository-local Markdown/JSON and a standard-library CLI. The PDF credits a reference methodology. These commands are a new implementation.
- 2026-11-15, D002. Retain a local ignored handoff queue and checkpoint. A separate remote handoff ref requires explicit scope.
- 2026-11-15, D003. Preserve untracked product files outside the infrastructure commit. GitHub reported no existing main ref at discovery.
- 2026-11-16, D004. The operator approved the project foundation for public main in INIT 00B. Normalize the Android File Server settings for publication and preserve the original locally. Gate 01 implementation remains a separate task.
- 2026-11-16, D005. The operator authorized standing GitHub publication in [.agent_rules/30-evidence-and-publication.md](.agent_rules/30-evidence-and-publication.md), including the isolated public handoff archive. This supersedes D002’s pending authorization for remote handoffs.
- 2026-11-16, D006. Adopt the standing [Code Modularity Policy](CODE_MODULARITY_POLICY.md): source-owner separation before overgrowth, review at 400 lines, refactor assessment at 600, and a justified-exception growth gate at 800 hand-maintained production lines. Line count is an architectural maintainability signal, not a runtime performance metric. Read it from AGENTS.md at source-edit task startup.
- 2026-11-16, D007. Gate 01 preserves a read-only source snapshot, applies explicit versioned corrections, and derives a disposable ScenePackage. Unreal transforms use one local metric origin and one centimeters-per-meter conversion. Independently test native orientation, scale and collision. Live geographic requests require a scoped operator OSM GO.
- 2026-11-16, D008. Keep the runtime spectator and inspection in Gate 01. Move live OSM and the approximately 2.2 km corridor to Gate 02. Use the smallest meaningful development smoke test and record verification separately from implementation and operator acceptance.

## GM-009 Milestones and baseline

B0 snapshot was an unborn main with no indexed files. The first tracked bootstrap commit captures this snapshot. INIT 00B adds the validated Unreal and Python foundation. Subsequent source identity and verification belong in [current state](_agent_context/CURRENT_STATE.md) and local immutable reports.

## GM-010 Failures and false PASS

[Known issues](_agent_context/KNOWN_ISSUES.md) records native and publication gates. Installed binaries and legacy local configuration cannot prove an executed native test. Existing default branch metadata alone cannot prove an actual remote ref.

## GM-011 Agent operating laws

Start with [AGENTS.md](AGENTS.md). Follow the five UAOS-B1 rule layers plus the mandatory [Code Modularity Policy](CODE_MODULARITY_POLICY.md) for code changes, and route this document via the index. Host startup compliance depends on whether it loads repository instructions.

## GM-012 Continuity contract

Checkpoint path and output root are in the manifest. Reports queue in `output/agentops/handoff/`. History is authoritative, with local LATEST and INDEX. Same-task resume requires current source and exact next action. A repo-only checkout retains tracked state and can read the sanitized [public handoff](https://github.com/tubajagrande93/Roadside-Drive/blob/agent-output/AgentOutput/LATEST.md).

## GM-013 Verified source and open decisions

Snapshot evidence is tied to B0's unborn main and the current installation's Git history. Open gates are tracked in [known issues](_agent_context/KNOWN_ISSUES.md). Run doctor to detect changes. OPERATOR_ACCEPTANCE_PENDING.
