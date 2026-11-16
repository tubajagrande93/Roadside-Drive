# Latest public handoff

[Immutable record](history/20261116T012723Z_RD-G02-CORRIDOR_ee67487.md)

# Roadside Drive — Gate 02 Banja Luka corridor

- Task and UTC: RD-G02-CORRIDOR · 20261116T012723Z
- Status: COMPLETE_VERIFIED
- Route selection: OPERATOR_ACCEPTED
- Operator acceptance of the native preview: PENDING
- Gate 01 baseline: 9b37333ebcad3ff2511e0394d2bcb336d1443eea
- Local main and independently verified origin/main and origin/codex/gate02-banja-luka: `ee674878624f69322dd983dc122bd87c49b9eecd`

## Route and source

The directed shortest and named-axis solutions both returned the same 2,145.684 m route along Dr Mladena Stojanovića and Kralja Petra I Karađorđevića. START snapped 4.494 m and END 1.590 m from the operator reference coordinates. The operator accepted the exact review SHA `46c52ad839e5f89d56573ea4834da2288939f47e498188a0b1e4f4fa0bab9666`. The accepted-route record SHA is `cb1686d0dc5efcbec747ea32e79516b397a119c8ddaa2993adb83288231a8adb`.

Two Overpass polygon queries covered 1.8883 km². They captured 2,450 road nodes, 3,890 directed graph edges and 1,537 building footprints. The 2026-11-16 UTC OSM source times were 00:58:05 for roads and 00:59:05 for buildings. OSM graph SHA-256 `69a8222ee92a48f99b1333688245bb1cb87e2e9d307c34e8cf2d6f9c1f939e8e`. © OpenStreetMap contributors, ODbL 1.0. [Source license](https://www.openstreetmap.org/copyright)

The accepted ScenePackage SHA-256 is `f0c0969d45e0085fd2db204c80d31b93713f38ca2bd706296b97c1ea676e7027`. It yielded 28 road surfaces, 154 buildings and one provisional floor. All 28 road widths use lane-count estimates. Of 154 shells, 152 use the unknown-height placeholder. The forward route includes two adjacent named parallel ways. The reverse drive route follows different streets. Grade is provisional.

## Native and correction evidence

UE 5.7.4 on Intel Metal compiled, imported and reopened `/Game/RoadsideDrive/Levels/L_RD_G02_Corridor` with 183 unique generated feature actors. Imported bounds matched the package. The native 100 m ruler measured 10,000 cm. START, MID and END viewport screenshots were rendered. A two-second editor sample was 58.15 FPS. A G02-only disposable project preserved the original project configuration and maps.

Native PIE held 160 cm over all 71 sampled road positions, traversed a building, ignored its roof and held a safe 148 cm world Z over the provisional ground and fallback. Actual Unreal PlayerController events verified WASD, mouse, Space, Ctrl, Shift and wheel. Measured Shift speed changed from 1,000 to 3,000 cm/s; wheel speed changed to 1,250 and restored. The first wall-time comparison was corrected to use game seconds.

Reopened road and building selections supplied stable source IDs, location and camera pose. Local reports included native selection and an optional local screenshot reference. Two builds with the same width patch had identical corrected hashes. The patch changed the road mesh and kept all six capture artifacts byte-identical. A stale source hash was rejected.

## Reproduction and continuity

The kit's 19 tests, 15 project world tests, focused Ruff and AgentOps verify passed. The accepted asset recipe and local native smoke passed. A clean clone at the exact commit, reusing the existing locked dependency environment, passed 15 world tests, AgentOps verify, Gate 01 fixture reproduction and Gate 02 zero-network query fingerprint regeneration. Git and the GitHub API independently matched both source refs and all 83 source blobs.

Source, configs and QA are published. The local kit, third-party references, raw OSM, generated Unreal assets, logs and screenshots remain local. The [Gate 02 runbook](https://github.com/tubajagrande93/Roadside-Drive/blob/ee674878624f69322dd983dc122bd87c49b9eecd/docs/world-builder/GATE_02_RUNBOOK.md) and [32-gate evidence ledger](https://github.com/tubajagrande93/Roadside-Drive/blob/ee674878624f69322dd983dc122bd87c49b9eecd/docs/world-builder/GATE_02_EVIDENCE.md) document the continuation.

NEXT_EXACT_ACTION: Open the saved L_RD_G02_Corridor for operator review and record the first measured geometry correction or explicit visual acceptance.
