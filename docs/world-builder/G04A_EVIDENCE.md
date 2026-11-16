# Gate 04A evidence

The source branch starts from G03 `dfb7d0126087f59279227dbc3bd0d5745439dde5`. The same signed package, `fa6150f0ea7debd025b3dea2464e73cb19b3beb99b8526ed235ab29473cefe18`, and its 633 feature IDs were loaded in both maps. Native landmark controls agreed with G03, including Park Mladen Stojanović left toward END and Gospodska left at its source control in that direction. These landmarks are outside the visual treatment.

The 200 m slice fingerprint is `7a29994d8167592163ecd6ab1e101398cd41ca68a933042fb0d4c3f70773bdde`. The overlay manifest, `7f56a73c19de920c6988610863580f01bac8dbbbb4cd8b885f00acb8c3902b55`, binds the approved route and source snapshot, set of parent road and pedestrian sources, and the three signed GLBs. A replay with the same input reproduced all four files byte for byte.

| Mesh | Surface area | Original map scale | SHA-256 |
| --- | ---: | --- | --- |
| `road_overlay.glb` | 1,732.79 m² | 4 m per asphalt tile | `6cacbbda1d16c48e10a8529c017a9c3e1d297dbba577630d3526be25fb342067` |
| `sidewalks.glb` | 1,170.74 m² | 2 m per paving tile | `42b4369a21c99d944539d6a44b61a0c72594f96800dd9588dca448ae7aeb5322` |
| `curbs.glb` | 63.94 m² | 1 m per concrete tile | `e0fd6d2162d73592365039fa54eb7615a0a3666c530da9daa9ec4bba22e5273b` |

The original texture manifest SHA-256 is `83a3fbc45399ef0f06a26271bc64d20f3f45233edcb17bbea627f7e9d0af31fa`. Re-baking the nine maps with the local runtime reproduced their pixels. Four PNG byte digests changed with local encoding. The native build uses the kit originals. G04A cuts the geometry at station 200 and its offline station-250 negative control is clear. Four mapped OSM lines and the residual road-edge presentation areas are recorded separately. The new display widths and curb heights are estimated.

## Native execution

The kit read-only preflight and nine route/PBR checks passed. The focused source tests check both station cuts, the parallel roadway band, junction openings and existing path gaps. The Unreal 5.7.4 Intel Metal capability probe passed. The build used the already-verified G03 direction, imported the original nine textures and wrote the new separate level. Intermediate runs identified Unreal Python differences in graph pin names, material parameter setters, overlap property access and custom input struct construction. The final writer resolves native pins, verifies the material values it reads back and sets the reflected struct and component properties. A directory-level save returned success before the new asset packages were present on disk. The writer explicitly saves each owned package before saving the level.

The final run reopened the saved level and rendered five native 1440 × 810 views. START and 100 m show textured asphalt against stone paving and a raised concrete edge. The 200 m view shows the transition at the cut. The forward 250 m view shows the original greybox road. The sky view shows the blue atmosphere and sparse white cloud cards. The asphalt instance uses a 0.62 base-color gain to darken the original starter color under the daytime rig. The local project is `data/processed/world_builder/gate04a-native-07/project/RoadsideDrive.uproject`. Its review directory contains `start.png`, `100m.png`, `200m.png`, `250m.png`, `sky.png` and `review.json` with camera transforms.

Play in Editor kept the exact signed START heading and moved forward 250 cm on the initial input probe. All 71 route samples stayed at approximately 160 cm above the floor. Passage through a building, floor fallback and PlayerController WASD, mouse and speed controls passed. An earlier capture-to-PIE attempt lost its first two simulated key events. The review waits for the viewport to settle before sending input.

All 633 G03 feature IDs remained in the level. The original G03 level and 1,266 G03 asset packages matched the independent source project byte for byte. The correction-set fingerprint remained `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`. The three new surface actors use NoCollision. Operator street-level sign-off and performance profiling are pending.
