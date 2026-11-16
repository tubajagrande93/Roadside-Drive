# Subsystem ownership table

B0 provenance 2026-11-15 UTC, unborn main. B1–B8 infrastructure provenance is the tracked bootstrap diff. INIT 00B promotes the product paths below to tracked source. Check doctor for the live SHA.

| Subsystem | Source owner / canonical writer | Reader or caller | Consumer | Tests | Risk |
| --- | --- | --- | --- | --- | --- |
| Unreal registration | `apps/unreal/RoadsideDrive/RoadsideDrive.uproject`, EngineAssociation 5.7 and ModelingToolsEditorMode | Unreal Editor (descriptor contract; native TO_VERIFY) | Editor project startup TO_VERIFY | descriptor parse | Engine mismatch |
| Project identity | `apps/unreal/RoadsideDrive/Config/DefaultGame.ini`, ProjectID | Config system TO_VERIFY | Asset/project references TO_VERIFY | B0 byte preservation | Identity change |
| Rendering and input defaults | `apps/unreal/RoadsideDrive/Config/DefaultEngine.ini` and `Config/DefaultInput.ini` under the project | Unreal config and Enhanced Input engine plugin (static) | Intel rendering and spectator mode TO_VERIFY | INI validation; native UE-01 open | Metal SM6, input contexts |
| Default map | `apps/unreal/RoadsideDrive/Config/DefaultEngine.ini`, GameDefaultMap | Config system TO_VERIFY | /Engine/Maps/Templates/OpenWorld configured | static | World startup |
| Python/GIS | `pyproject.toml`, `uv.lock`, `.python-version` | uv | Python 3.12 environment VERIFIED imports | GIS import/smoke | Dependency or CRS drift |
| Checkpoint/handoff | tools/agentops_state.py | tools/agentops.py dispatch | report, doctor, fresh operator | tests/test_agentops_contract.py | Stale or fabricated evidence |

## Canonical writers

AgentOps checkpoint is written by write_checkpoint. Reports are queued by write_report and history entries are exclusive. The [World Builder ownership map](../docs/world-builder/ARCHITECTURE.md) traces the Python producers, generated package, Unreal importer, native inspection actor and spectator.

## Readers/consumers

Doctor and report validate checkpoint metadata; AgentOps startup reads manifest and scoped source. The Unreal importer consumes validated ScenePackages. The pilot map uses the native spectator game mode and typed actors for Details inspection and floor sampling.

## Test ownership

Contract harness owns bootstrap regressions, with ledger in the templates. There was no B0 product test suite discovered. Native execution evidence is UE-01.

## Unverified nodes

Real Banja Luka source licensing, acquisition, projected CRS and geography remain Gate 02 work. Operator acceptance of the synthetic pilot remains pending.

## Gate 01 and Gate 02 source

[World Builder architecture](../docs/world-builder/ARCHITECTURE.md) traces the source, correction, mesh, package and editor boundaries. The public handoff identifies the exact verified source and records the executed tests.


Gate 02 extends the existing OSM adapter with two exact scoped Overpass requests. The route review produces a directed candidate sealed against the graph. The corridor builder binds the approved review and assembles features for the existing ScenePackage and correction writers. The native importer owns both isolated maps and delegates corridor presentation and PIE checks to the corridor editor and spectator verification modules.

## Gate 04A visual layer

The [visual foundation runbook](../docs/world-builder/G04A_VISUAL_FOUNDATION.md) anchors station slicing and overlay export in `src/roadside_drive/world/visual`. The G04A editor bridge consumes the sealed overlay, applies separate material instances and lighting in a new level, and reopens it for native evidence. G03 keeps canonical source IDs, corrections, orientation and collision.
