# Subsystem ownership table

B0 provenance 2026-11-15 UTC, unborn main. B1–B8 infrastructure provenance is the tracked bootstrap diff. Product paths below are local discovery evidence.

| Subsystem | Source owner / canonical writer | Reader or caller | Consumer | Tests | Risk |
| --- | --- | --- | --- | --- | --- |
| Unreal registration | `apps/unreal/RoadsideDrive/RoadsideDrive.uproject`, EngineAssociation 5.7 and ModelingToolsEditorMode | Unreal Editor (descriptor contract; native TO_VERIFY) | Editor project startup TO_VERIFY | descriptor parse | Engine mismatch |
| Project identity | `apps/unreal/RoadsideDrive/Config/DefaultGame.ini`, ProjectID | Config system TO_VERIFY | Asset/project references TO_VERIFY | B0 byte preservation | Identity change |
| Default map | `apps/unreal/RoadsideDrive/Config/DefaultEngine.ini`, GameDefaultMap | Config system TO_VERIFY | /Engine/Maps/Templates/OpenWorld configured | static | World startup |
| Python/GIS | `pyproject.toml`, `uv.lock`, `.python-version` | uv | Python 3.12 environment VERIFIED imports | GIS import/smoke | Dependency or CRS drift |
| Checkpoint/handoff | tools/agentops_state.py | tools/agentops.py dispatch | report, doctor, fresh operator | tests/test_agentops_contract.py | Stale or fabricated evidence |

## Canonical writers

AgentOps checkpoint is written by write_checkpoint. Reports are queued by write_report and history entries are exclusive. Product dataset writers are TO_VERIFY.

## Readers/consumers

Doctor and report validate checkpoint metadata; AgentOps startup reads manifest and scoped source. Python and Unreal domain consumers beyond their known configurations are TO_VERIFY.

## Test ownership

Contract harness owns bootstrap regressions, with ledger in the templates. There was no B0 product test suite discovered. Native execution evidence is UE-01.

## Unverified nodes

Spatial schema, canonical CRS and transformations, world generation, editor runtime and simulation acceptance.
