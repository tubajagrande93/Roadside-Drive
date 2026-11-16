# Gate 01 operator QA

## Offline package

From the branch checkout:

```sh
uv sync --locked --offline
uv run --locked --no-sync --offline python scripts/world_builder.py doctor
uv run --locked --no-sync --offline python scripts/world_builder.py build-fixture \
  --config configs/worlds/synthetic_pilot.json \
  --output data/processed/world_builder/synthetic_pilot
uv run --locked --no-sync --offline python scripts/world_builder.py validate \
  --scene data/processed/world_builder/synthetic_pilot/scene_manifest.json
uv run --locked --no-sync --offline pytest tests/world -q
uv run --locked --no-sync --offline ruff check src scripts tests/world pipelines/unreal
python3 tools/agentops.py verify
```

Use the README online setup once if the registry cache is empty. A fresh run must print the synthetic label, the package digest and counts of 2 roads, 3 buildings and 1 provisional ground. Build twice to separate directories. Compare package digests. Repeat with a correction and compare source hashes. Omit the correction to recover the base.

## Native Unreal smoke

Set `ROADSIDE_UNREAL_ROOT` to the local installation. From the branch checkout:

```sh
uv run --locked --no-sync --offline python pipelines/unreal/run_editor_smoke.py \
  --engine "$ROADSIDE_UNREAL_ROOT" \
  --scene data/processed/world_builder/synthetic_pilot/scene_manifest.json \
  --output data/processed/world_builder/native-attempt-01 \
  --mode import
```

Choose a new attempt folder for every run. The runner installs editor-only scripting plugins in the disposable descriptor. It keeps process and editor logs, raw native evidence and the copy of the project. An exit without a native evidence record means the editor script was never reached. An imported mesh must match the catalog within 2 cm, and the in-bounds trace and outside control must agree. Use the saved isolated level only if the runner supplies evidence for it.

To continue from a working GUI session, open the disposable project, switch the viewport to a low-cost preview profile as needed, run the editor script with the variables described by the invocation and open the verified test level. Select the synthetic actors by stable ID and compare their bounds, source confidence and collision rationale to `object_catalog.json`. Use right mouse and WASD in the perspective viewport and verify camera speed, movement and selection. Record editor free navigation separately from runtime spectator.

Runtime spectator candidate after native editor proof: dedicate an Enhanced Input mapping context to mouse-look, WASD, Space and Ctrl elevation and Shift speed boost. Test no gravity, no collision, no visible mesh and restoration of the previous context on exit in the disposable test level. No Blueprint, native freecam PASS or runtime spectator claim follows from the offline test.
