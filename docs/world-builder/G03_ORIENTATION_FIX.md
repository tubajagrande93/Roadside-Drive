# Gate 03 geographic handedness

Operator reproduction was START, forward toward the city centre, then Park Mladen Stojanović appeared on the right. The earlier native bounds and spectator tests measured scale and motion in the same mirrored frame. Their expected coordinates never checked a surveyed geographic side.

## First divergence

Longitude and latitude project to EPSG:32633 in X-east/Y-north order. Subtracting the Gate 02 origin keeps the local geometry in east, north and up metres. This frame and the approved directed road were correct.

The old writer serialized glTF XYZ as east, up, north. Unreal Interchange mapped this to Unreal XYZ east, north, up, in centimetres. There was no per-actor mirror or negative scale. Unreal's left-handed coordinate system uses positive Y on the viewer's right when facing +X. Keeping geographic north as positive Unreal Y reflected the entire geographic environment relative to the start-to-end journey. The legacy native park mesh bounds independently reproduced this. The old hard-coded START yaw also followed the legacy map frame.

The geographic writer now uses glTF XYZ east, up, **south**, with the corresponding triangle winding. Interchange produces native XYZ east, **south**, up. Unchanged physics and input stay in native coordinates. Spawn yaw derives from the first 20 m or more of the approved route. Park/landmark cameras, collision probes and spectator test checkpoints use the same signed conversion. Stable IDs, geographic bounds, source centers and patch hashes remain east/north/up. Locations captured as native centimetres in old editor feedback refer to the old frame.

[Epic coordinate-system reference](https://dev.epicgames.com/documentation/unreal-engine/coordinate-system-and-spaces-in-unreal-engine?application_version=5.7) · [Epic georeferencing and handedness](https://dev.epicgames.com/documentation/unreal-engine/georeferencing-a-level-in-unreal-engine?application_version=5.7)

## Reproduction and rerun

Use the accepted Gate 02 inputs and the exact cached Gate 03 results from the [runbook](GATE_03_RUNBOOK.md). Regenerate only the derived Gate 03 package in a new output directory. If the base has the legacy exchange, its generated meshes are reframed as they are copied. A base with the current signed exchange is copied directly. This keeps accepted source/correction relationships intact. Previously saved levels and generated packages are retained. The existing synthetic fixture exchange is preserved independently.

Run the orientation control recipe against the new manifest and pass the resulting file to the editor smoke:

```sh
PYTHONPATH=src .venv/bin/python scripts/check_g03_orientation.py \
  --scene data/processed/world_builder/gate03-oriented/package/scene_manifest.json \
  --osm "$OSM_RESULT" \
  --legacy-evidence data/processed/world_builder/gate03-native-release/native.json \
  --output output/agentops/g03-mirror/orientation-controls.json
export RD_ORIENTATION_CONTROLS="$PWD/output/agentops/g03-mirror/orientation-controls.json"
```

The legacy results are positive-to-right for the Park, Boska, the Gospodska midpoint and Christ the Saviour. The comparison includes a known right-side building as a falsifier and the distinct parallel road surface at START. Gospodska's source centerline midpoint is covered by the generated path triangles and checked against its native mesh group bounds. Native landmark results use the directed road tangent at the source station. Runtime checks independently verify PlayerStart location and facing, forward movement, road and ground constraints, and the actual input events.

The corrected G03 ScenePackage SHA-256 is `fa6150f0ea7debd025b3dea2464e73cb19b3beb99b8526ed235ab29473cefe18`. The saved copy is in the generated `gate03-native-oriented` project. Use that copy for operator recheck.

## Observed Unreal 5.7.4 results

Distances are in metres along the camera's right axis at the matched directed road station. Negative means left. Landmark and building rows use native actor bounds centres. The sampled Gospodska point and the parallel road use source centreline points within their native mesh group bounds.

| Control | Archived native | Corrected native | Corrected side |
| --- | ---: | ---: | --- |
| Park Mladen Stojanović | 110.277 | −110.277 | Left |
| Boska | 83.773 | −83.773 | Left |
| Gospodska / Veselina Masleše | 61.445 | −61.445 | Left |
| Hram Hrista Spasitelja | 37.160 | −37.160 | Left |
| Building OSM way/1349089233 | −34.115 | 34.115 | Right |
| Parallel road at START, OSM way/785905277 | 1.888 | −1.888 | Left |

A native Mac Intel build succeeded. A fresh editor imported 633 assets at identity scale, saved the corrected level, and passed the middle-road and off-map collision probes. Play in Editor possessed the spectator at the exact START point, with a heading dot product of 1.0. Forward at spawn advanced 250 cm toward END. All 71 ordered road samples measured 160 cm clearance. The tests also passed through a building, verified under-roof and off-map fallback at 148 cm and exercised real keyboard, mouse and wheel input. Native Details preserved OSM source references and the selected building's Overture reference.

The corrected package replayed byte-for-byte, including every mesh digest. The directed route, geographic origin, source and normalized hashes, and all 633 IDs and catalog attributes matched the archived G03 package. A separate replay of the existing Gate 02 width correction kept all 183 base IDs and patch fingerprint `d1ef4c29f3fcd9e545fb80d30282db4875a4ad673e549f5938c64873c89d4f13`. Each base mesh matched its explicit signed reframe. The Gate 02 recipe generated a signed package. The Gate 01 synthetic package reproduced its previous hash exactly.
