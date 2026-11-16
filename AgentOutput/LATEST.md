# Latest public handoff

[Immutable record](history/20261116T020725Z_RD-G03-HARVEST_9897d5d.md)

# Roadside Drive — Gate 03 environment harvest

- Task and UTC: RD-G03-CORRIDOR-RECONSTRUCTION-HARVEST · 20261116T020725Z
- Technical status: COMPLETE_VERIFIED for the targeted Gate 03 scope
- Operator acceptance of Gate 03 preview: PENDING. Gate 02 operator preview was deferred.
- Local and verified remote source ref: `refs/heads/codex/gate03-environment` at `9897d5df284352acf81e87c89a1a9310d299dec4`
- Published main baseline: `ee674878624f69322dd983dc122bd87c49b9eecd`. Concurrent local dependency edits were left intact.
- [Separate Source Expansion Handoff](https://github.com/tubajagrande93/Roadside-Drive/blob/9897d5df284352acf81e87c89a1a9310d299dec4/source_atlas/G03_SOURCE_EXPANSION_HANDOFF.md) · [Runbook](https://github.com/tubajagrande93/Roadside-Drive/blob/9897d5df284352acf81e87c89a1a9310d299dec4/docs/world-builder/GATE_03_RUNBOOK.md) · [Evidence](https://github.com/tubajagrande93/Roadside-Drive/blob/9897d5df284352acf81e87c89a1a9310d299dec4/docs/world-builder/GATE_03_EVIDENCE.md)

## Verified acquisition and scene

The operator-approved route is 2,145.684 m. The 12 bounded semantic OSM responses include the southern building tile recovered through a July 2026 Kumi mirror after two HTTP 502 responses from FOSSGIS. The immutable Source Expansion Handoff records the exact plan fingerprint and all response hashes. The official Overture STAC release 2026-10-21.0 returned 3,788 building, 7 part and 2,215 place features before the local polygon filter. Three individual Commons references have verified license and SHA-256.

The final ScenePackage SHA-256 is `4eaa05f355043fb78083f536a2bc935823eda963b65f62b662bbbf994cdb89a6`. It contains 633 features: 512 buildings, 28 roads, one retained floor, one wider context surface, 25 park groups and 22 groups each of vegetation, paths and street details. The station inventory assigns 352 left and 648 right candidate buildings over 22 × 2 cells, one cell with no source features. 903 overlapping Overture candidates linked to OSM and 42 overlap reviews are queued. Of 510 new/refined building records, 3 use OSM height tags, 1 an Overture height, 155 level-based estimates and 351 a 7 m placeholder. Roofs and facades are still provisional. Park and Boska have distinct mapped geometry; the two cathedrals retain distinct identities.

## Native and preservation checks

Unreal 5.7.4 Intel built and reopened `/Game/RoadsideDrive/Levels/L_RD_G03_Corridor`. The final viewport rendered the three corridor views, Park Mladen Stojanović and Boska. An editor point sample recorded 57.73 FPS. The first render showed paths beyond the context ground; geometry is now clipped at the approved polygon and the final viewport was repeated.

The native 100 m control measured 10,000 cm. All 71 ordered road samples remained at 160 cm clearance. The pawn passed through a building and used the same fallback. Native PlayerController inputs verified WASD, mouse, Space, Ctrl, Shift and wheel. The route frame, all 183 retained IDs and road/floor hashes match Gate 02; a separate width-patch replay also retained all 183 base mesh hashes and the patch-set hash. The existing Gate 02 map and assets stayed intact.

Twenty-one focused project tests, 12 kit tests, Ruff, AgentOps verify and localized deterministic replay passed. Git and the GitHub API independently matched the branch tip and all 96 source blobs. Raw sources, photographs, screenshots, maps and logs stayed local.

## Source limitations

OpenBuildingMap tile 120233 is listed at 1.0 GB and remained outside the capture budget. Official LoD2 is NEEDS_ACCESS. KartaView HTTPS calls failed. Mapillary and OpenTopography were not run without authorized credentials. These sources did not contribute geometry.

NEXT_EXACT_ACTION: Open L_RD_G03_Corridor in the saved isolated project and review the Park Mladen Stojanović and Boska viewpoints before selecting the first measured facade or roof correction. Integrate the verified source branch after the concurrent main checkout work is safe to reconcile.
