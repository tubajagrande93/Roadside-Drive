# Latest public handoff

[Immutable record](history/20261116T070743Z_RD-G03-MIRROR-FIX_dfb7d01.md)

# Roadside Drive — Gate 03 geographic handedness correction

- Task and UTC · RD-G03-MIRROR-FIX · 20261116T070743Z
- Technical status · COMPLETE_VERIFIED
- Operator acceptance · PENDING
- Source ref · `refs/heads/codex/gate03-environment`
- Local source SHA and independently verified GitHub SHA · `dfb7d0126087f59279227dbc3bd0d5745439dde5`
- GitHub Git transport and API confirmed the same source SHA and 101 identical source blobs.
- Main remains at the accepted Gate 02 baseline while separate dependency work is present.
- [Changed files](https://github.com/tubajagrande93/Roadside-Drive/commit/dfb7d0126087f59279227dbc3bd0d5745439dde5) · [Correction and native evidence](https://github.com/tubajagrande93/Roadside-Drive/blob/dfb7d0126087f59279227dbc3bd0d5745439dde5/docs/world-builder/G03_ORIENTATION_FIX.md) · [Source Expansion Handoff](https://github.com/tubajagrande93/Roadside-Drive/blob/dfb7d0126087f59279227dbc3bd0d5745439dde5/source_atlas/G03_SOURCE_EXPANSION_HANDOFF.md)

## First divergence and correction

The operator reported Park Mladen Stojanović on the right when moving from START toward the city centre. The WGS84 → EPSG:32633 → local east/north/up chain and the operator-approved journey were correct. Export mapped ENU metres to glTF east/up/north. Unreal Interchange produced east/north/up centimetres in an axis system where the viewer's right is positive Y when looking along +X. This reflected the corridor, park, roads, buildings and surroundings relative to travel.

Geographic GLBs now encode east/up/south with matching winding. Unreal receives east/south/up at 100 cm per metre with identity actor scale. START yaw derives from the directed road. Regeneration reused the archived bounded source and approved corridor. Only the generated corridor was rebuilt and reimported into a new isolated project. The original map and correction material remain available.

## Observed evidence

| Control | Archived native right-axis m | Corrected native right-axis m | Corrected side |
| --- | ---: | ---: | --- |
| Park Mladen Stojanović | 110.277 | −110.277 | Left |
| Boska | 83.773 | −83.773 | Left |
| Gospodska / Veselina Masleše midpoint | 61.445 | −61.445 | Left |
| Hram Hrista Spasitelja | 37.160 | −37.160 | Left |
| Building OSM way/1349089233 | −34.115 | 34.115 | Right |
| START parallel road OSM way/785905277 | 1.888 | −1.888 | Left |

The generated Gospodska triangles cover its source control. Unreal verified the matching native groups and the middle-road and off-map collision traces. Intel Mac UE 5.7.4 built and imported successfully. The possession check measured a heading dot of 1.0, zero horizontal spawn error and 250 cm forward toward END. All 71 route samples measured 160 cm above the floor. Keyboard, mouse, speed control, passage through walls and both fallback floor probes passed. Reopening the saved level confirmed 633 distinct actors, road/building inspection capture and five viewport images.

The corrected package replayed byte-identically at SHA-256 `fa6150f0ea7debd025b3dea2464e73cb19b3beb99b8526ed235ab29473cefe18`. The approved route and all 633 stable IDs, geographic bounds, and source/correction relationships were preserved. A separate replay of the earlier width correction confirmed 183 exact signed reframes and the original patch SHA. Gate 01's synthetic fixture retained its original SHA.

The final source passed all 47 pytest cases, native evidence checks, preservation replay, Ruff and AgentOps verification. An earlier cold-start test identified a missing heading in CURRENT_STATE and a reopen attempt used a separate inspection directory. Both were corrected and passed on repeat.

## NEXT_EXACT_ACTION

Open the generated `data/processed/world_builder/gate03-native-oriented/project/RoadsideDrive.uproject` and play `L_RD_G03_Corridor` from START. Confirm the park is left while travelling toward END before refinement.
