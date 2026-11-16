# Latest public handoff

[Immutable record](history/20261116T001909Z_RD-G01_95f4aa9.md)

# Roadside Drive — Gate 01 offline greybox and native preview

- Task and UTC: RD-G01-WORLD-FOUNDATION · 20261116T001909Z
- Gate status: PARTIAL
- Source ref: refs/heads/codex/gate01-world-foundation
- Local HEAD and independently verified remote SHA: 95f4aa92f1ded88842801e18a5f21ca5f10050b4
- Main remains at 31431f98135ccd28553e3cf9f31c3037a8c28c76
- Operator acceptance: PENDING

## What works

GO-01 synthetic World Builder is verified. Two 100 m roads form one intersection, three building footprints and provisional ground. The package has 44 mesh triangles and stable IDs, explicit material categories and confidence. Same inputs generated identical canonical hashes. One building keeps null source height with a labeled visual placeholder. Corrections replay separately; stale or duplicate patches, invalid geometry, altered artifacts and unsafe paths are rejected. WGS 84 longitude/latitude is explicit. EPSG:32633 remains a real-pilot candidate. The synthetic local XYZ exchange verified one metre per 100 UE centimetres.

GO-02 imported package SHA 059d892af1baec393f45a125ec5f7e57d4e9ce3fbd11ae9b783103a64dc1f2ff in a disposable UE 5.7.4 project and saved /Game/RoadsideDrive/Levels/L_RD_WorldPilot. All six mesh objects and their imported materials were verified. The control road measured 10000 cm. Collision hit the road and missed the outside control. Editor API movement and stable-road selection passed. The rendered Intel viewport visibly showed the crossing and buildings. Right mouse with W moved the viewport forward on the preceding lighting commit. Full keyboard/mouse coverage and runtime spectator are still open.

The direct commandlet hit a Slate assertion. Full-editor execution reached GLB import and exposed a mirrored north axis. Changing the verified exchange orientation corrected the issue. The generated level and its raw logs remain local. The source provides a reproducible importer and [operator runbook](https://github.com/tubajagrande93/Roadside-Drive/blob/95f4aa92f1ded88842801e18a5f21ca5f10050b4/docs/world-builder/OPERATOR_QA.md).

## Tests and publication

On 95f4aa92f1ded88842801e18a5f21ca5f10050b4, pytest tests/world passed 11, the AgentOps contract suite passed 24, Ruff and AgentOps verify returned 0, and a clean clone recovered the documented task state. Two packages compared byte-for-byte at the canonical manifest. Native full-editor automation returned exit 0 and the explicit import, trace, viewport API and saved-level checks passed. The OSM command returned expected exit 2 with the approval absent. No live geographic request was made.

Git transport and the GitHub API independently matched source SHA and all 61 source blobs. No local assets, generated outputs, logs, raw datasets or credentials were published.

## OSM GO boundary

GO-03 has the bounded proposal and gate code. GO-04 remains blocked pending a reviewed exact centerline and buffered EPSG:4326 polygon. Candidate only: a segment near Ulica kralja Petra I Karađorđevića, 500–1000 m. Two logical queries cover drive roads and building footprints and their existing tags, using the configured Overpass endpoint under ODbL. Limits are 0.5 km² and 1.5 km maximum span. Counts and download size are unmeasured. [Source and license register](https://github.com/tubajagrande93/Roadside-Drive/blob/95f4aa92f1ded88842801e18a5f21ca5f10050b4/docs/world-builder/SOURCES_AND_LICENSES.md).

NEXT_EXACT_ACTION: Confirm the real pilot endpoints and buffered polygon with the operator. Run prepare-aoi, show its query fingerprint and request scoped OSM GO before any live geographic download.
