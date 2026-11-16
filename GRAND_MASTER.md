# Roadside Drive Grand Master

## GM-001 Identity and scope

Canonical document for `tubajagrande93/Roadside-Drive`. B0 inspected `refs/heads/main` on 2026-11-15 UTC before its first commit (SHA UNKNOWN). Use doctor for the live identity. See [profile](_agent_context/REPO_PROFILE.md) for the evidence. Operator acceptance is PENDING.

## GM-002 Authority order

Latest explicit operator authorization determines scope. Live Git/source establishes current implementation, approved invariants guide intended behavior, and observed runtime can reopen an automated or native gate. Handoffs and summaries are historical evidence.

## GM-003 Product purpose and boundaries

Operator intent is a modular real-world driving simulator, initially a precision World Builder for 500–1000 metres of Banja Luka, Bosnia and Herzegovina. Planned work includes OSM ingestion, georeferenced metric editable geometry, collisions and physical surfaces, CS 1.6-style spectator free flight, object inspection and measurement, reversible corrections, provenance/confidence, repeatability and Unreal import. This is roadmap intent. INIT 00B tracks the descriptor, default configurations, and locked geospatial dependencies. Pipeline/runtime implementation is TO_VERIFY.

## GM-004 Architecture and writers

[Architecture map](_agent_context/ARCHITECTURE_MAP.md) anchors the existing Unreal configuration, Python dependency specification and agent infrastructure. ProjectID and startup map are configuration-owned. No world data schema or canonical feature writer was located in B0.

## GM-005 Protection and non-goals

Preserve existing Unreal identities, workspace configuration, local environments, raw/cached/processed geographic data and assets. INIT 00B publishes project configuration and documentation. Product implementation, data migration, releases and deployment require separate authority.

## GM-006 Invariants and acceptance

Preserve the local Unreal project identity and LFS mappings, with anchors in the architecture map. Future geometry accuracy and native behavior require measurements and operator acceptance. Harness green status covers only its asserted boundary.

## GM-007 Build, test, run and release

Run `python3 -m unittest discover -s tests -p test_agentops_contract.py -v` and `python3 tools/agentops.py verify`. Recreate the local Python environment and check GIS imports using the [README](README.md#set-up-a-local-checkout). Engine Build.version and project config are static evidence. Headless Unreal automation, app packaging, CI and production releases are open.

## GM-008 Decisions

- 2026-11-15, D001. Install the UAOS-B1 source-first method using repository-local Markdown/JSON and a standard-library CLI. The PDF credits a reference methodology. These commands are a new implementation.
- 2026-11-15, D002. Retain a local ignored handoff queue and checkpoint. A separate remote handoff ref requires explicit scope.
- 2026-11-15, D003. Preserve untracked product files outside the infrastructure commit. GitHub reported no existing main ref at discovery.
- 2026-11-16, D004. The operator approved the project foundation for public main in INIT 00B. Normalize the Android File Server settings for publication and preserve the original locally. Gate 01 implementation remains a separate task.
- 2026-11-16, D005. The operator authorized standing GitHub publication in [.agent_rules/30-evidence-and-publication.md](.agent_rules/30-evidence-and-publication.md), including the isolated public handoff archive. This supersedes D002’s pending authorization for remote handoffs.
- 2026-11-16, D006. Adopt the standing [Code Modularity Policy](CODE_MODULARITY_POLICY.md): source-owner separation before overgrowth, review at 400 lines, refactor assessment at 600, and a justified-exception growth gate at 800 hand-maintained production lines. Line count is an architectural maintainability signal, not a runtime performance metric. Read it from AGENTS.md at source-edit task startup.

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
