# Gate 04A first 200 m

G04A layers a summer road preview over the corrected G03 Banja Luka corridor. The parent remains the signed G03 ScenePackage at `fa6150f0ea7debd025b3dea2464e73cb19b3beb99b8526ed235ab29473cefe18` and the matching saved level. Station zero is the operator-approved START. The chainage ends at exactly 200 m on the directed metric route. The park is farther along at approximately 424 m.

## Geometry and source confidence

`visual/route_slice.py` interpolates the directed chainage and applies perpendicular end cuts and a lateral window. `visual/surfaces.py` reuses the exact polygons of the parent meshes and verifies archived OSM tiles used for mapped sidewalks and access/crossing masks. It decodes the exchange with the basis from the existing coordinate owner. The asphalt is a 4 mm rendering offset of the visible G03 road surfaces, including the parallel carriageway where present. The fallback pedestrian bands subtract roads, openings, existing paths and nearby buildings and park polygons. Four OSM mapped pedestrian lines establish positions in this slice. Display widths, curb width of 16 cm, curb top 12 cm above the road and the remaining strips are estimates. Real grade and curb ramps await measurements.

`visual/export.py` writes and seals an independent manifest and three signed GLBs. Each overlay actor uses `NoCollision`, keeps overlaps disabled and has its own visual ID. The G03 feature actors continue to own source IDs, corrections, geometry and floor sampling.

## Native assets and lighting

`pipelines/unreal/run_g04a.py` copies the built disposable G03 project to a fresh directory. The editor opens the original signed G03 level, checks its IDs and geographic landmarks, and uses it as a template for `/Game/RoadsideDrive/Levels/L_RD_G04A_Visual200`. The new meshes and materials live in `/Game/RoadsideDrive/Generated/G04A`. All three surfaces share a world-XY master material. Texture repeats are 4 m for asphalt, 2 m for sidewalk and 1 m for concrete. The level reuses one sun and adds native SkyAtmosphere, captured skylight and lightweight procedural translucent cloud planes.

## Rebuild and reopen

From the source checkout, use the existing Python/GIS runtime and set paths to the accepted local artifacts. Use the selected nine kit assets and their manifest for matching native evidence. Alternatively, `python scripts/bake_g04a_pbr.py --out "$PBR"` regenerates original textures from source. PNG compression can change file digests across environments. Rebuild the overlay manifest and its texture seal together.

```sh
PYTHONPATH=src python scripts/build_g04a_visual.py \
  --root "$ARTIFACT_ROOT" --base "$G03_SCENE" --osm "$ARCHIVED_OSM_RESULT" \
  --textures "$PBR" --config configs/worlds/g04a_visual200.json \
  --output "$ARTIFACT_ROOT/data/processed/world_builder/g04a-visual200-new"
python pipelines/unreal/run_g04a.py --engine "$UE57_ROOT" \
  --source-project "$ORIENTED_G03_PROJECT" --parent-scene "$G03_SCENE" \
  --orientation "$VERIFIED_G03_ORIENTATION_CONTROLS" \
  --overlay "$ARTIFACT_ROOT/data/processed/world_builder/g04a-visual200-new/visual_manifest.json" \
  --textures "$PBR" --output "$ARTIFACT_ROOT/data/processed/world_builder/gate04a-native-new"
```

Use the G04A generated `project/RoadsideDrive.uproject` and open `L_RD_G04A_Visual200`. Play from Default Player Start. The native review writes five images and a JSON record under `Saved/RoadsideG04AReview`. For the G03 baseline, open the original generated project and `L_RD_G03_Corridor` separately. In the G04A level, hide the three overlay actors to inspect the original road underneath. Original source graphics, raw data, Unreal assets and screenshots remain in their local artifact directories.

[Epic UE 5.7 material editor API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialEditingLibrary?application_version=5.7) · [Sky Atmosphere](https://dev.epicgames.com/documentation/en-us/unreal-engine/sky-atmosphere-component-in-unreal-engine)
