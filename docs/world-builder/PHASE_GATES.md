# Gate 01 verification

| Gate | Evidence and limits |
| --- | --- |
| G01.0–G01.4 / GO-01 | Versioned offline package and fixture. Verify scale, axes and origin, geometry, source IDs, placeholder heights, correction conflicts, source preservation, deterministic outputs, manifest tamper detection, no-network behavior and path safety with `tests/world`. |
| G01.5–G01.6 / GO-02 | Full-editor automation under UE 5.7.4 saved the isolated synthetic pilot, measured a 100 m road as 10,000 cm and passed the in-bounds and out-of-bounds native trace controls. The headless commandlet could not create the level due to a Slate assertion. The first full-editor run caught a north-axis sign mismatch, then the corrected GLB exchange passed. The spectator and Details inspector have targeted native smoke checks. Exhaustive input coverage and profiling are optional development verification. |
| Gate 02 | Real Banja Luka data, the approximately 2.2 km corridor and a separately approved OSM GO. See [Gate 02 entry](GATE_02_ENTRY.md). |
| G01.8 | Source commits, local checkpoint, isolated public reports, independently verified GitHub ref and exact next action. |

Report implementation, verification and operator acceptance separately. See the latest public handoff for exact execution evidence.
