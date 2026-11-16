# Latest public handoff

[Immutable record](history/20261116T005242Z_RD-G01-FINAL_9b37333.md)

# Roadside Drive — Gate 01 finalization

- Task and UTC: RD-G01-WORLD-FOUNDATION · 20261116T005242Z
- UAOS status: COMPLETE_VERIFIED
- Implementation: IMPLEMENTED
- Verification: VERIFIED for the targeted Gate 01 acceptance checks
- Operator acceptance: PENDING
- Local HEAD, origin/main and origin/codex/gate01-world-foundation: `9b37333ebcad3ff2511e0394d2bcb336d1443eea`

## Implementation and native result

The synthetic World Builder generates six metric objects, with stable IDs, canonical metadata and separate correction replay. The runtime spectator uses WASD, mouse, Space, Ctrl, Shift and wheel. Its camera queries only roads and ground and passes through buildings. The native Details panel exposes each object's stable ID, type, dimensions in metres, local and source coordinates, CRS, source type and confidence.

UE 5.7.4 built the project module on Intel, imported the six meshes and saved the pilot level. The Metal SM5 editor visibly displayed the crossing, three buildings and ground. In Play in Editor the possessed spectator entered a building at X 1450 cm and left at X 2950 cm. Descent stopped at Z 120 cm on the road, 115 cm on the ground, 115 cm inside the building and 115 cm outside the designated surface. Camera clearance was 120 cm relative to the sampled floor. The native road trace hit and outside control missed. The inspector returned `road-east-west`, 100 m, SYNTHETIC, VERIFIED.

## Verification and observed limitations

Python and GIS imports, fixture build and validation, scoped Ruff, AgentOps verify and the native smoke passed. ScenePackage SHA-256: `059d892af1baec393f45a125ec5f7e57d4e9ce3fbd11ae9b783103a64dc1f2ff`. The [operator runbook](https://github.com/tubajagrande93/Roadside-Drive/blob/9b37333ebcad3ff2511e0394d2bcb336d1443eea/docs/world-builder/OPERATOR_QA.md) gives the exact build and launch commands. Git transport and the GitHub API independently matched the source refs and source tree.

Cold shader startup timed out on the first attempt. NullRHI placement aborted in Unreal viewport hit-testing. The full-editor runner uses Metal for import and PIE. A parallel UE Python-wrapper startup abort was resolved by using the engine's single-threaded wrapper setting. The first PIE automation called an unavailable Python method. Its replacement uses `get_controlled_pawn`.

Manual coverage of every input, SM6 execution and Intel performance profiling were not run. Operator acceptance remains pending. Live OSM capture was outside Gate 01 and no live geographic request was made.

NEXT_EXACT_ACTION: When the operator starts [Gate 02](https://github.com/tubajagrande93/Roadside-Drive/blob/9b37333ebcad3ff2511e0394d2bcb336d1443eea/docs/world-builder/GATE_02_ENTRY.md), define the approximately 2.2 km Banja Luka corridor and buffered WGS84 AOI, then present the bounded query fingerprint and data rights for scoped OSM GO.
