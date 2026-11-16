# Gate 03 environment harvest

Gate 03 extends the operator-approved Gate 02 road by layering building evidence, park geometry and roadside features onto the existing ScenePackage. The original Gate 02 centerline, source mesh files, corrections, level and Unreal project remain in place. The enriched package retains the 28 road mesh hashes, the provisional floor and all Gate 02 stable object IDs. Where any Gate 02 correction overlay is present, the enrichment keeps the existing building meshes as well.

## Repeat the authorized harvest

From the Roadside Drive checkout, set these repository-relative paths to the immutable Gate 02 capture, directed review and operator route approval.

```sh
export PYTHONPATH=src
CAPTURE=data/raw/world_builder/snapshots/8782db052330bc6154bb439f4606135881f7c3ccf7b8ef5add9693094dd1b36a/capture_manifest.json
REVIEW=data/processed/world_builder/gate02-route-review/review.json
APPROVAL=data/raw/world_builder/approvals/gate02-banja-luka-route.json
BASE=data/processed/world_builder/gate02-accepted-final/scene_manifest.json
harvest() {
  .venv/bin/python -m roadside_drive.world.harvest.cli \
    --capture "$CAPTURE" --review "$REVIEW" --approval "$APPROVAL" "$@"
}
harvest osm
harvest osm --live
harvest overture --cli "$OVERTURE_CLI"
```

The first command is offline. It derives four approved polygon tiles and the 12 exact Overpass queries. Run only against the authorized scope. The reviewed version uses bounded responses, a combined budget and a three-second interval. Resume only failed slots with `harvest osm --retry "$OSM_RESULT"`; use `--mirror` only if the original endpoint fails. Keep the resulting vintage per slot. Set `OVERTURE_CLI` to the locally installed official Overture Maps 2.1.1 executable. The wrapper reads the official STAC catalog, pins its release and records three separate files. Source release and capture time are separate.

Set `OSM_RESULT` and `OVERTURE_RESULT` to the verified result files. Replay the package in a new ignored directory.

```sh
harvest build --base "$BASE" --osm "$OSM_RESULT" --overture "$OVERTURE_RESULT" \
  --output data/processed/world_builder/gate03-final
.venv/bin/python pipelines/unreal/run_editor_smoke.py --engine "$ROADSIDE_UNREAL_ROOT" \
  --scene data/processed/world_builder/gate03-final/package/scene_manifest.json \
  --output data/processed/world_builder/gate03-native-final --mode spectator --timeout 900
```

The Unreal runner creates an isolated project. For an isolated source worktree, use `--artifact-root` to place the generated project under the live checkout’s ignored data tree. The map uses `/Game/RoadsideDrive/Levels/L_RD_G03_Corridor` and owns `/Game/RoadsideDrive/Generated/G03`. The G02 GameMode and floor constraints are reused. Added park, path, context and street meshes do not block the spectator.

Use the named Park Mladen Stojanović and Boska cameras, or reopen the saved map through `review_corridor.py` with `RD_CORRIDOR_REVIEW_GATE=G03`. Use the existing native **Roadside Inspection** details and issue capture flow to report a revision. The captured image and viewport materials are provisional.

## Evidence and source reuse

The merged candidate table ranks heights by surviving evidence. Tagged values and floor-count estimates remain estimates. Attributable footprints and rendering geometry retain feature identity. A geometric match in 0.15–0.65 IoU enters the conflict list. The 22 stations contain two signed sides per station. The object inventory and building evidence table remain in the generated data tree. Park Mladen Stojanović is left of the approved forward route. Its sampled polygon point is around station 424 m and 146 m lateral offset. The park edge intersects the near-road band. Boska and the two distinct church footprints are kept separate. Review roof and facade measurements before higher-detail modelling.

See the [separate Source Expansion Handoff](../../source_atlas/G03_SOURCE_EXPANSION_HANDOFF.md) for the exact successful queries, hashes, releases, licenses and unavailable source paths. The Commons photographs are local only. The protected kit, official-provider access details, third-party materials and generated Unreal files stay outside Git.

The common Unreal importer remains the package integrity and asset writer after the RD-ARCH-001 soft review. Corridor and landmark presentation, spectator tests, and reopened-scene evidence live in separate helpers.
