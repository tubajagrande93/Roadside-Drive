# Gate 02 Banja Luka corridor

Start and end retain the two operator reference intersections near Dr. Mladena Stojanovića 103 and the Boska approach from Kralja Petra I Karađorđevića. Their WGS84 coordinates and exact 350 m search polygon are in the [corridor config](../../configs/worlds/banja_luka_gate02.json). The chord measures 2,148.247 m. It is a geographic reference. The query uses both anchors and the exact 1.888 km² polygon, in two topic requests. Complete way and relation members support topology. The route solver and scene enforce their own spatial scope.

## Capture and route review

Run these from the checkout with its locked environment. A bounded live run uses an ignored approval record binding the exact query SHA, endpoint and ODbL. The operator authorized the initial corridor download for Gate 02. A different scope needs its own authorization. The completed snapshot is reusable. An incomplete capture remains visibly reserved and needs a review before retry.

```sh
export PYTHONPATH=src
.venv/bin/python scripts/world_builder.py prepare-aoi \
  --config configs/worlds/banja_luka_gate02.json
.venv/bin/python scripts/world_builder.py ingest-osm \
  --config configs/worlds/banja_luka_gate02.json --allow-network \
  --approval data/raw/world_builder/approvals/gate02-banja-luka-approved.json
.venv/bin/python scripts/world_builder.py review-route \
  --capture "$CAPTURE_MANIFEST" --output data/processed/world_builder/gate02-route-review
```

The Banja Luka review compared a directed shortest route and a name-weighted route. Both followed the two intended named streets and returned 2,145.684 m, with 4.494 m at START and 1.590 m at END. OSM tagged one-way directions are preserved, including mapped parallel ways. The initial derived adjacency uses the street name, proximity and alignment along the route to include separately mapped carriageways. The two carriageways and connectors need visual review before any accuracy claim. A route approval binds the exact graph SHA, review SHA and candidate ID, recorded in an ignored approval file after operator sign-off. The operator accepted the displayed directed route with review SHA `46c52ad839e5f89d56573ea4834da2288939f47e498188a0b1e4f4fa0bab9666`. This accepts the route choice. Native preview acceptance remains a separate check.

The v1 capture includes UTC source dates, request content, original response digests, OSMnx-derived graph counts and reference attribution. The capture, kit, screenshot previews and generated assets are kept local. [OpenStreetMap copyright and license](https://www.openstreetmap.org/copyright) · [OSMF attribution guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines)

## Candidate preview and native view

```sh
.venv/bin/python scripts/world_builder.py build-corridor --capture "$CAPTURE_MANIFEST" \
  --review data/processed/world_builder/gate02-route-review/review.json \
  --candidate-id directed-shortest --candidate-preview \
  --output data/processed/world_builder/gate02-osm-preview
.venv/bin/python pipelines/unreal/run_editor_smoke.py --engine "$ROADSIDE_UNREAL_ROOT" \
  --scene data/processed/world_builder/gate02-osm-preview/scene_manifest.json \
  --output data/processed/world_builder/gate02-native-preview --mode spectator --timeout 900
```

Use a separate output folder when substituting `--approval` for `--candidate-preview`. Point it to the reviewed local route record. The real-source and synthetic recipes share the canonical source, patch, GLB and ScenePackage owners. Grade is flat and provisional. Road widths record unverified OSM widths, a 3.2 m-per-lane estimate or road-class placeholders. Unknown heights use 6 m greybox shells and stay explicitly unknown in the source. Scene coverage uses a 65 m visual buffer around the candidate. Edge-crossing, courtyard and invalid building footprints are counted where they are excluded.

The isolated editor saves `/Game/RoadsideDrive/Levels/L_RD_G02_Corridor` and uses `/Game/RoadsideDrive/Generated/G02`. The native GameMode sets the 160 cm spectator for this map. The disposable editor configuration uses basic lighting and turns off ray tracing, Nanite, Lumen and distance-field generation for this corridor. START, MID and END camera actors provide fixed overview viewpoints. The reopened map can produce three viewport renders and a saved-map check through `pipelines/unreal/review_corridor.py`. Pass the generated project path in `RD_G02_REVIEW_PROJECT`, then launch it with `-ExecutePythonScript`. Evidence lands under the generated project’s `Saved/RoadsideG02Review`. The pilot remains disposable and publication of derived Unreal assets requires a separate provenance and distribution review.

## Feedback and corrections

Select exactly one imported road or building and inspect **Details → Roadside Inspection**. In the UE Python console load `inspection_feedback.py` and call `capture_issue_context()`. For example:

```python
exec(open("/absolute/path/to/pipelines/unreal/inspection_feedback.py").read())
capture_issue_context()
```

From the checkout, submit the printed context using a repository-relative path under the disposable project. If you include a screenshot, save it under `output/agentops` first.

```sh
.venv/bin/python scripts/world_builder.py report-issue --scene "$SCENE_MANIFEST" \
  --editor-context "$SELECTION_JSON" --severity minor \
  --observed 'Describe the issue at this object' --expected 'Describe the expected result'
```

Use the existing `CorrectionPatch` contract with the stable ID, raw feature hash, expected value and supported field. Rebuild to a new generated directory with `--patches`. The source capture is immutable. A changed source feature hash or prior value makes the patch conflict.


Under RD-ARCH-001, the shared Unreal importer crossed the 400-line soft-review threshold. Runtime tests and G02 presentation are in separate modules. The importer remains the common owner for package integrity, asset import, placement and saving.
