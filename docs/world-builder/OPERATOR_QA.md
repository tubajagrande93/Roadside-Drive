# Gate 01 operator runbook

From the source checkout, set `ROADSIDE_UNREAL_ROOT` to the UE 5.7.4 installation and prepare a new disposable pilot:

```sh
uv sync --locked --offline
uv run --locked --no-sync --offline python scripts/world_builder.py build-fixture \
  --config configs/worlds/synthetic_pilot.json \
  --output data/processed/world_builder/synthetic_pilot
uv run --locked --no-sync --offline python pipelines/unreal/run_editor_smoke.py \
  --engine "$ROADSIDE_UNREAL_ROOT" \
  --scene data/processed/world_builder/synthetic_pilot/scene_manifest.json \
  --output data/processed/world_builder/runtime-pilot \
  --mode spectator
```

If the uv cache is empty, use the README setup once. Use a new native output folder for each run. The runner builds the C++ project module with the installed Unreal Build Tool, imports to a disposable copy and exercises the spectator in Play in Editor. The logs, compiled module and saved level stay in the generated folder. The full editor uses Metal, which can fall back to SM5 on Intel. The launcher uses single-threaded UE Python wrapper generation after an observed startup crash in the parallel wrapper path.

Open the generated project and its level:

```sh
"$ROADSIDE_UNREAL_ROOT/Engine/Binaries/Mac/UnrealEditor" \
  "$PWD/data/processed/world_builder/runtime-pilot/project/RoadsideDrive.uproject" \
  /Game/RoadsideDrive/Levels/L_RD_WorldPilot \
  '-ini:Engine:[ConsoleVariables]:Engine.Python.ForceWrapperGenerationOnSingleThread=1'
```

1. In the editor, select a road, building or ground actor. Open **Details → Roadside Inspection**. Match the stable ID, object type, dimensions in metres, local/source coordinates, source type and confidence with `object_catalog.json`. The actor transform can be zero because the mesh vertices already carry the local position.
2. Press **Play** and click the viewport to capture input. **WASD** moves horizontally, **mouse** looks, **Space** ascends, **Ctrl** descends, **Shift** boosts and the **mouse wheel** adjusts speed.
3. Fly through a building and hold **Ctrl**. Its roof should never act as a floor. Over a road or ground, the camera stops 120 cm above the highest designated floor. Away from the pilot it holds the last sampled floor, or uses the configurable 0 cm fallback when no floor has been sampled.
4. Exit Play with **Esc**. Inspect only the disposable level. Keep generated meshes and Unreal saves out of Git.

The smoke test drives the same runtime movement method used by the player. It checks possession, traversal across a building, road and ground clearance, fallback and ascent. A passing automated movement check is separate from manually confirming every input and accepting the preview.
