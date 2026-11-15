# Profile

Roadside Drive project. Operator scope describes the simulator and Banja Luka intent. B0 discovery 2026-11-15 UTC. DISCOVERY_COVERAGE: PARTIAL (entrypoints, manifests, scoped file inventory and local tools).

# Git topology

B0: main unborn, no staged/tracked files, 11 untracked product/config paths. origin is the HTTPS GitHub repository `tubajagrande93/Roadside-Drive`. `git ls-remote origin` returned zero refs. `gh api .../branches` returned an empty array and repository API reported default_branch main, public, and push permission. Sandbox-default lookup failed DNS, authorized read succeeded. No CI workflow or prior agent instructions were found.

# Stack and entrypoints

`apps/unreal/RoadsideDrive/RoadsideDrive.uproject` and four Default*.ini files were observed locally. `pyproject.toml`, `.python-version` and `uv.lock` declare Python/GIS dependencies. `modules/{physics,vehicle-builder,world-builder}` and `pipelines/{geometry,osm,unreal}` exist locally as directory scaffolding. No domain code was discovered in them. The pre-existing product files were untracked and may be absent in a bootstrap-only clone.

# Local build and tests

`sw_vers`: macOS 26.7 (25G229). `uname -m`: x86_64. Xcode 26.6 (17F113), `xcrun --find metal` located the executable. Engine Build.version 5.7.4 CL 51494982. Git 2.56.0, Git LFS 3.8.1, gh 2.102.0, uv 0.13.8 and local venv Python 3.12.16 verified. GIS imports GeoPandas 1.2.0, Shapely 2.2.0, pyproj 3.8.0, OSMnx 2.1.2 and trimesh 5.2.1. For bootstrap run `python3 -m unittest discover -s tests -p test_agentops_contract.py -v`. Native unattended entry and product suites are open.

# Protected data

Existing source, settings and lockfiles, .env, .venv, assets, geodata and Unreal cache/saved state. Do not read private payloads for discovery. See preservation rules.

# Source map

## SOURCE_INVENTORY

| FACT | EVIDENCE_PATH_OR_COMMAND | CONFIDENCE | UNKNOWN | PRESERVATION_RISK |
| --- | --- | --- | --- | --- |
| No B0 index or HEAD | git ls-files, git status --porcelain=v1 -uall, git rev-parse HEAD | VERIFIED | Future integration of initial product files | Accidental inclusion in first commit |
| Local Unreal project configuration | apps/unreal/RoadsideDrive/RoadsideDrive.uproject, Config/Default*.ini | VERIFIED static | Runtime/native tests | Project identity, saved data |
| Local Python/GIS declaration and imports | pyproject.toml, uv.lock, .python-version, .venv/bin/python | VERIFIED static/import | Product GIS pipeline | Lockfile/env changes |
| LFS mappings and local ignore | .gitattributes, .gitignore, git lfs version | VERIFIED | Future asset publication | Oversized or private assets |
| Public remote with zero refs at B0 | git ls-remote origin, gh api repo and branches | VERIFIED at discovery | Authorization for first main ref | Unintended public source |
| No prior entry or canonical files discovered | rg filename inventory including nested paths | VERIFIED in scoped tree | Ignored content intentionally not inspected | Overriding child rules |

# Unknowns

Product owners beyond configuration, geographic data licenses, native test invocation, simulator behavior, release and CI. Use source and operator scope before implementation.

# INIT 00B foundation

`apps/unreal/RoadsideDrive/` and the Python/LFS/environment manifests listed above are now tracked project source. The lockfile uses public PyPI hosts. The Unreal Engine 5.7.4 install contains an Intel editor executable, the engine OpenWorld template and the Modeling Tools editor plugin. The local GeoReferencing and Enhanced Input plugins are integration candidates to validate. No tracked World Builder pipeline or native test suite was discovered. Setup and the manual native smoke test are in [README.md](../README.md).
