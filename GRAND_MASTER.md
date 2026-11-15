# Roadside Drive Grand Master

## GM-001 Identity and scope

Canonical document for `tubajagrande93/Roadside-Drive`. B0 inspected `refs/heads/main` on 2026-11-15 UTC before its first commit (SHA UNKNOWN). Use doctor for the live identity. See [profile](_agent_context/REPO_PROFILE.md) for the evidence. Operator acceptance is PENDING.

## GM-002 Authority order

Latest explicit operator authorization determines scope. Live Git/source establishes current implementation, approved invariants guide intended behavior, and observed runtime can reopen an automated or native gate. Handoffs and summaries are historical evidence.

## GM-003 Product purpose and boundaries

Operator intent is a modular real-world driving simulator, initially a precision World Builder for 500–1000 metres of Banja Luka, Bosnia and Herzegovina. Planned work includes OSM ingestion, georeferenced metric editable geometry, collisions and physical surfaces, CS 1.6-style spectator free flight, object inspection and measurement, reversible corrections, provenance/confidence, repeatability and Unreal import. This is roadmap intent. Local descriptor and default configurations were observed. Pipeline/runtime implementation is TO_VERIFY.

## GM-004 Architecture and writers

[Architecture map](_agent_context/ARCHITECTURE_MAP.md) anchors the existing Unreal configuration, Python dependency specification and agent infrastructure. ProjectID and startup map are configuration-owned. No world data schema or canonical feature writer was located in B0.

## GM-005 Protection and non-goals

Preserve existing Unreal files, workspace configuration, local environments, raw/cached/processed geographic data and assets. Agent infrastructure is the bootstrap scope. Product logic, data migration, releases and deployment require separate authority.

## GM-006 Invariants and acceptance

Preserve the local Unreal project identity and LFS mappings, with anchors in the architecture map. Future geometry accuracy and native behavior require measurements and operator acceptance. Harness green status covers only its asserted boundary.

## GM-007 Build, test, run and release

Run `python3 -m unittest discover -s tests -p test_agentops_contract.py -v` and `python3 tools/agentops.py verify`. Local GIS can be checked via `.venv/bin/python` without syncing. Engine Build.version and project config are static evidence. Headless Unreal automation, app packaging, CI and production releases are open.

## GM-008 Decisions

- 2026-11-15, D001. Install the UAOS-B1 source-first method using repository-local Markdown/JSON and a standard-library CLI. The PDF credits a reference methodology. These commands are a new implementation.
- 2026-11-15, D002. Retain a local ignored handoff queue and checkpoint. A separate remote handoff ref requires explicit scope.
- 2026-11-15, D003. Preserve untracked product files outside the infrastructure commit. GitHub reported no existing main ref at discovery.

## GM-009 Milestones and baseline

B0 snapshot was an unborn main with no indexed files. The first tracked bootstrap commit captures this snapshot; subsequent observations belong in [current state](_agent_context/CURRENT_STATE.md) and local immutable reports.

## GM-010 Failures and false PASS

[Known issues](_agent_context/KNOWN_ISSUES.md) records native and publication gates. Installed binaries and legacy local configuration cannot prove an executed native test. Existing default branch metadata alone cannot prove an actual remote ref.

## GM-011 Agent operating laws

Start with [AGENTS.md](AGENTS.md). Follow the five rule layers and route this document via the index. Host startup compliance depends on whether it loads repository instructions.

## GM-012 Continuity contract

Checkpoint path and output root are in the manifest. Reports queue in `output/agentops/handoff/`. History is authoritative, with local LATEST and INDEX. Same-task resume requires current source and exact next action. A repo-only checkout retains tracked state, commands and publication gates.

## GM-013 Verified source and open decisions

Snapshot evidence is tied to B0's unborn main and the current installation's Git history. Open gates are tracked in [known issues](_agent_context/KNOWN_ISSUES.md). Run doctor to detect changes. OPERATOR_ACCEPTANCE_PENDING.
