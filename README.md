# Roadside Drive

Roadside Drive is a modular simulation platform for building and driving through real-world streets. Phase 1 is the World Builder. Its first target is an editable 500–1000 m street segment in Banja Luka, Bosnia and Herzegovina.

## Project baseline

- The Unreal Engine 5.7 project descriptor and default configuration live under `apps/unreal/RoadsideDrive/`. The configured default game map is the engine's OpenWorld template.
- `pyproject.toml`, `uv.lock` and `.python-version` define the Python 3.12 geospatial environment. It supplies OSM ingestion, projection and geometry libraries for future pipeline work.
- World Builder, vehicle building and physics are planned modules. Streets, buildings, terrain, collision, source provenance, correction layers and spectator controls are Phase 1 design work. The current baseline contains the project configuration and testable toolchain.
- [GRAND_MASTER.md](GRAND_MASTER.md) is the canonical record. [CURRENT_STATE.md](_agent_context/CURRENT_STATE.md) gives the current milestone and next action.

## Set up a local checkout

Install Git LFS, uv, Python 3.12 and Unreal Engine 5.7 with the tools appropriate for your platform. Use your existing installations when available. From the repository root:

```sh
git lfs install --local
uv sync --locked --python 3.12 --no-python-downloads
uv lock --check --offline --no-python-downloads
uv run --locked --no-sync python -c 'import osmnx, geopandas, shapely, pyproj, pyogrio, trimesh'
```

If uv cannot find a suitable interpreter, point `--python` at an existing Python 3.12 executable. The lockfile pins the package graph. A fresh environment requires access to the package index or a populated uv cache. The commands target the repository-local environment. [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)

LFS rules cover Unreal packages and supported asset formats such as FBX, GLB and GeoTIFF. Review source, size and license before staging either an asset or geographic data. Keep generated Unreal directories and local environments out of Git.

## Open Unreal on macOS

Set `ROADSIDE_UNREAL_ROOT` to your installed Unreal 5.7 engine root. The [.env.example](.env.example) records the two local settings. You can copy it to an ignored `.env` to keep your own configuration. The launch command uses the shell variable.

```sh
export ROADSIDE_UNREAL_ROOT="/path/to/UE_5.7"
"$ROADSIDE_UNREAL_ROOT/Engine/Binaries/Mac/UnrealEditor" \
  "$PWD/apps/unreal/RoadsideDrive/RoadsideDrive.uproject"
```

For the UE‑01 manual smoke test, use a disposable checkout. Verify that the editor opens the project, load the engine OpenWorld template or run Play, confirm viewport rendering, and record any missing plugins, project or Metal/RHI errors. Quit, then check that Git has no tracked edits. Record the commit, engine version, CPU/GPU and observed result. Static inspection found the UE 5.7.4 editor with an Intel slice, the project’s editor plugin and the configured engine map. Native runtime and packaging remain unverified.

The public baseline disables Unreal Android File Server and its network connection and leaves its token empty. Keep any future device-specific deployment credentials local.

## Tests and agent workflows

```sh
uv run --locked --no-sync python tools/agentops.py doctor --json
uv run --locked --no-sync python tools/agentops.py verify
uv run --locked --no-sync python tools/agentops.py bootstrap --dry-run
uv run --locked --no-sync python -m unittest discover -s tests -p test_agentops_contract.py -v
uv run --locked --no-sync ruff check tools tests
git lfs version
```

Start with [AGENTS.md](AGENTS.md). Use [Context Shark](_agent_modules/CONTEXT_SHARK.md) for bounded source discovery and [MAX POWERBRAIN](_agent_modules/MAX_POWERBRAIN.md) for source-backed planning.

```sh
uv run --locked --no-sync python tools/agentops.py route --task 'ROADSIDE DRIVE — GATE 01 WORLD BUILDER FOUNDATION' --json
uv run --locked --no-sync python tools/agentops.py powerbrain --task 'ROADSIDE DRIVE — GATE 01 WORLD BUILDER FOUNDATION' --out output/agentops/gate01_powerbrain.md
```

Read the [verified public handoff](https://github.com/tubajagrande93/Roadside-Drive/blob/agent-output/AgentOutput/LATEST.md) for GitHub-only continuation. Detailed local plans, checkpoints and raw evidence are ignored. Follow the [publication policy](.agent_rules/30-evidence-and-publication.md) for source and report branches.
