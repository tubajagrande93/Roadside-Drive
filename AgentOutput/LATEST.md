# Latest public handoff

[Immutable record](history/20261116T075444Z_RD-G04A-200M-VISUAL-FOUNDATION_bbe1f10_G04A_VISUAL_FOUNDATION_HANDOFF.md)

# Roadside Drive — G04A 200 m visual foundation

- Task · RD-G04A-200M-VISUAL-FOUNDATION · 20261116T075444Z
- Implementation and technical verification · COMPLETE_VERIFIED
- Operator acceptance · PENDING
- Parent · `codex/gate03-environment` at `dfb7d0126087f59279227dbc3bd0d5745439dde5`
- Source delivery · `refs/heads/codex/gate04a-visual-foundation` at `bbe1f10b6d3e856f8bcfeed52614064f4aef2725`. Git transport, GitHub API and 116 blob IDs matched independently.
- [Runbook](https://github.com/tubajagrande93/Roadside-Drive/blob/bbe1f10b6d3e856f8bcfeed52614064f4aef2725/docs/world-builder/G04A_VISUAL_FOUNDATION.md) · [Evidence](https://github.com/tubajagrande93/Roadside-Drive/blob/bbe1f10b6d3e856f8bcfeed52614064f4aef2725/docs/world-builder/G04A_EVIDENCE.md)

The Unreal 5.7.4 Intel Metal editor built and reopened `/Game/RoadsideDrive/Levels/L_RD_G04A_Visual200` in the generated project `data/processed/world_builder/gate04a-native-07/project/RoadsideDrive.uproject`. The G03 level and asset bytes, original correction fingerprint and all 633 stable IDs were preserved. Native geographic controls still place Park Mladen Stojanović on the left toward END. No extra reflection was applied.

The asphalt geometry and corresponding presentation sidewalks and curbs terminate at chainage 200 m. Asphalt follows five G03 road surfaces, including the parallel carriageway. Four OSM mapped lines establish some sidewalk locations. Sidewalk widths, remaining bands and curb heights are provisional. Original greybox beyond the visual area is visible at 250 m. The three overlay actors use NoCollision. One world-XY material family uses nine original kit maps. Native SkyAtmosphere, a single directional sun, captured skylight and sparse procedural cloud cards are saved in the new level.

- 200 m chainage fingerprint · `7a29994d8167592163ecd6ab1e101398cd41ca68a933042fb0d4c3f70773bdde`
- Overlay package · `7f56a73c19de920c6988610863580f01bac8dbbbb4cd8b885f00acb8c3902b55`
- Original texture manifest · `83a3fbc45399ef0f06a26271bc64d20f3f45233edcb17bbea627f7e9d0af31fa`

| Saved GLB | SHA-256 | Unreal material instance |
| --- | --- | --- |
| curbs.glb | `e0fd6d2162d73592365039fa54eb7615a0a3666c530da9daa9ec4bba22e5273b` | `MI_G04A_concrete` |
| road_overlay.glb | `6cacbbda1d16c48e10a8529c017a9c3e1d297dbba577630d3526be25fb342067` | `MI_G04A_asphalt` |
| sidewalks.glb | `42b4369a21c99d944539d6a44b61a0c72594f96800dd9588dca448ae7aeb5322` | `MI_G04A_paving` |

Actual local screenshot names in `Saved/RoadsideG04AReview` are `start.png`, `100m.png`, `200m.png`, `250m.png` and `sky.png`. The seed replay reproduced the three GLBs and overlay manifest byte-for-byte. Kit tests 9/9, source tests 2/2, Ruff, AgentOps verify and the native evidence check passed. PIE recorded 71 route floor samples near 160 cm, forward from START, motion through buildings and PlayerController WASD, mouse and speed controls.

Visual G04A seal, six unchanged orientation controls, original map and 1266 asset bytes, five Unreal renders, and floor-only PIE PASS

The initial attempts exposed engine Python API differences, incomplete directory-level asset saves and unstable input immediately after high-resolution capture. The final run explicitly saved its asset packages and verified input after the PIE viewport settled. No frame-rate certification or manual operator check was performed.

## NEXT_EXACT_ACTION

Open the generated project and play `L_RD_G04A_Visual200` from Default Player Start. Inspect the asphalt, sidewalk and curb around 100 m, look up at the clouds, and continue past 200 m to the original G03 surface.
