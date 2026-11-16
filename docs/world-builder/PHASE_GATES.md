# Gate 01 verification

| Gate | Evidence and limits |
| --- | --- |
| G01.0–G01.4 / GO-01 | Versioned offline package and fixture. Verify scale, axes and origin, geometry, source IDs, placeholder heights, correction conflicts, source preservation, deterministic outputs, manifest tamper detection, no-network behavior and path safety with `tests/world`. |
| G01.5–G01.6 / GO-02 | Full-editor automation under UE 5.7.4 saved the isolated synthetic pilot, measured a 100 m road as 10,000 cm and passed the in-bounds and out-of-bounds native trace controls. The headless commandlet could not create the level due to a Slate assertion. The first full-editor run caught a north-axis sign mismatch, then the corrected GLB exchange passed. Free navigation, runtime spectator and Intel profiling have separate gates. |
| G01.7 / GO-03 | Offline request preparation and approval-gated OSM capture are available. Banja Luka corridor geometry and source approval are pending. |
| GO-04 | Requires a bounded operator OSM GO for real geodata. No live extraction or real-world reconstruction is included in offline QA. |
| G01.8 | Source commits, local checkpoint, isolated public reports, independently verified GitHub ref and exact next action. |

The offline package can pass while Gate 01 remains partial. See the latest public handoff for the exact SHA, executed gates and native boundary.
