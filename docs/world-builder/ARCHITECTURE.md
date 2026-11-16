# Gate 01 World Builder

The offline pipeline starts with a read-only source snapshot, replays corrections against source digests and writes a reproducible ScenePackage. The first fixture is **SYNTHETIC — NOT BANJA LUKA**.

| Boundary | Owner and caller | Consumers |
| --- | --- | --- |
| Versioned source and patches | `contracts.py` validates source and applies ordered patches from the pristine version. `exports.build_fixture` calls this before writing. | Metric geometry and the normalized feature files. |
| Coordinate conversion | `projections.py` defines metrical projection, a fixed origin and the 100 cm scale. Geographic input is longitude then latitude. Local axes are east, north and up. | Geometry, glTF exchange and native checks. |
| Meshes | `geometry.mesh_features` creates the two connected road surfaces, three building shells and flat provisional ground. The first road owns the crossing overlap. | `exports.generate_scene` writes GLB files with Y up and positive Z north after the observed Interchange axis test. |
| Package | `exports.validate_scene` verifies the manifest seal, catalogs, safe paths, artifact digests, object counts, imported GLB face counts, bounds and road normals. | The CLI, runtime-independent tests and the native editor bridge. |
| Geographic capture | `osm_adapter.approved_query` gates the live capture method before loading or calling OSMnx. `proposal` validates and fingerprints the request offline. | Ignored source snapshot and subsequent licensed normalization work. |
| Native bridge | `pipelines/unreal/run_editor_smoke.py` copies the configuration into an isolated project and calls `import_world.py` with Unreal's embedded Python. | An isolated pilot level and trace or failure evidence. |

A patch compares the expected raw feature hash and the previous value to the actual source and active overlay. An unknown feature, stale value, stale source or duplicate ID produces an explicit error. The fixture and prior packages stay intact. Build different revisions in separate generated directories. Matching builds leave an existing sealed output untouched.

Source height stays null when unknown. The visual shell uses an explicit 6 m placeholder. The flat ground has no surveyed elevation. The native importer compares measured mesh boxes to metric catalog bounds in centimeters. A format claim in editor documentation does not establish local runtime behavior. [Unreal Engine 5.7 glTF import](https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-gltf-files-into-unreal-engine?application_version=5.7)

## Pilot runtime

The generated level installs `ARoadsideSpectatorGameMode` as its level-specific override. The pawn has a camera and no collision body. `ARoadsideSpectatorPawn::ApplyFlightInput` is shared by player input and PIE smoke. It samples only designated road and ground feature actors at the proposed XY and enforces a configurable vertical clearance. It can pass through buildings without using them as floors.

`ARoadsideWorldFeatureActor` binds the package catalog to native actor Details. Inspect dimensions and positions in metres and retain the catalog ID, coordinate reference, source type and confidence. Package source and corrections remain authoritative for rebuilds.

The 401-line editor bridge was reviewed under the standing [Code Modularity Policy](../../CODE_MODULARITY_POLICY.md). It stays the native import and validation entry point for this pilot. Gameplay movement and inspection metadata live in the C++ module. Review separating native verification from import when Gate 02 expands the bridge.
