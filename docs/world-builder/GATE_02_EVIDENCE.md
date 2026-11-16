# Gate 02 verification ledger

The Banja Luka road choice is operator-approved. Overall visual acceptance remains pending. The accepted ScenePackage has SHA-256 `f0c0969d45e0085fd2db204c80d31b93713f38ca2bd706296b97c1ea676e7027`. It contains 28 road surfaces, 154 building shells and one provisional ground surface. See the [runbook](GATE_02_RUNBOOK.md) for commands and the [public handoff](https://github.com/tubajagrande93/Roadside-Drive/blob/agent-output/AgentOutput/LATEST.md) for source identity.

| Gate | Result | Executed evidence |
| --- | --- | --- |
| G02-01 | PASS | Kit verify and 19 unit tests reproduced the exact pins and 2,148.247 m chord. |
| G02-02 | PASS | Canonical prepare-aoi projected the exact 350 m buffer. The polygon area is 1.8883 km². |
| G02-03 | PASS | Canonical and kit dry runs wrote no capture and sent zero data requests. |
| G02-04 | PASS | The missing-live-flag and missing-approval test rejected acquisition. |
| G02-05 | PASS | The out-of-polygon control rejected a widened AOI. The actual Overpass requests used a polygon filter. |
| G02-06 | PASS | Two responses saved. UTC source times were 00:58:05 and 00:59:05 on 2026-11-16, with ODbL attribution and six hashed local artifacts. |
| G02-07 | PASS | Both route solvers returned the same connected 2,145.684 m drive route over 71 directed edge traversals. |
| G02-08 | PASS | START snapped 4.494 m and END 1.590 m. Nearest road-node selection is limited to 85 m. |
| G02-09 | PASS | Names, intersection anchors and geometry were reviewed against the operator references. The operator accepted the route overlay. |
| G02-10 | PASS | Directed one-way graph preserved. The reverse route takes different streets. Deduplicated physical ways include two separately mapped adjacent named ways. This is a forward corridor preview. |
| G02-11 | PASS | The kit EPSG:32633 projection round trip passed. |
| G02-12 | PASS | Unreal measured the native ruler at 10,000 cm and matched the GLB bounds to the package. |
| G02-13 | PASS | Package validation checked finite vertices, nondegenerate triangles, upward normals and matching bounds. |
| G02-14 | PASS | Accepted build replay matched exactly. The width-patched build replay also matched exactly. |
| G02-15 | PASS | All six capture artifacts retained their exact SHA-256 during correction replay. |
| G02-16 | PASS | A stale source hash failed before output publication. |
| G02-17 | PASS | All 28 widths used lane-count estimates. 152 of the 154 building shells retained unknown-height placeholders. |
| G02-18 | PASS | UE 5.7.4 Intel rendered and reopened the saved map. Three viewport renders were observed. |
| G02-19 | PASS | The editor worked in an isolated project with G02-only level and asset namespaces. Existing product configuration and maps were preserved. |
| G02-20 | PASS | Native PlayerController WASD and mouse events drove the possessed pawn across real PIE frames. |
| G02-21 | PASS | Native Space and Ctrl moved vertically. Shift changed 1,000 to 3,000 cm/s. Wheel raised speed to 1,250 and restored 1,000 cm/s. |
| G02-22 | PASS | Traversal through a footprint shell completed with zero horizontal error. Its roof did not become a floor. |
| G02-23 | PASS | All 71 ordered road samples clamped to 160 cm. |
| G02-24 | PASS | Ground and outside fallback held 148 cm in world Z, 160 cm above the provisional ground at −12 cm. |
| G02-25 | PASS | The ascent control reached 10,250 cm without a ceiling. |
| G02-26 | PASS | Reopened native road and building selections returned stable IDs, source hashes and metric positions. |
| G02-27 | PASS | A local issue generated from native selection captured actor location, camera pose and scene/source SHA. The optional screenshot path stays local. |
| G02-28 | PASS | A controlled width patch changed its mesh, rebuilt identically and preserved the raw hashes. A stale source hash was rejected. |
| G02-29 | PASS | LFS filters checked. Only source, configs, tests and docs staged. |
| G02-30 | See handoff | Independently verified Git refs and source blobs are in the publication handoff. |
| G02-31 | See handoff | Clean clone execution and limits are in the publication handoff. |
| G02-32 | PENDING | Route selection accepted. Native scene acceptance awaits the operator’s preview. |

The initial PIE boost assertion compared equal intended wall-clock durations and encountered a longer first frame. The repeat measured displacement per second of native game time. The final saved-map review sampled 58.15 editor frames per second over two seconds before the screenshots. This is a local point measurement. Terrain height, lane width, traffic controls and architectural details are unsurveyed.
