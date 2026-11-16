# Gate 03 evidence

This report records the original harvest before the [geographic handedness correction](G03_ORIENTATION_FIX.md).

- Confirmed road: 2,145.684 m. The approved local metric route matched every vertex to the Gate 02 scene. Road and floor GLB hashes stayed unchanged. All 183 original IDs survived. A replay with the earlier width patch retained all 183 base mesh hashes and the patch-set fingerprint.
- Final ScenePackage SHA-256: `4eaa05f355043fb78083f536a2bc935823eda963b65f62b662bbbf994cdb89a6`. It contains 633 features, including 512 buildings, 25 park groups and 22 groups each of paths, vegetation and street details. The package retains the Gate 02 floor and separate wider context ground.
- Twelve bounded OSM responses are archived. The southern building tile came from an older Kumi mirror after two HTTP 502 responses. The Overture release and Commons photo licenses and hashes are documented in the [Source Expansion Handoff](../../source_atlas/G03_SOURCE_EXPANSION_HANDOFF.md).
- The 22 × 2 station inventory has 43 cells with building candidates and one explicit gap. There are 352 left-side and 648 right-side candidates, 903 Overture links and 42 footprint conflicts queued. The full station index contains 6,057 records across building, place and environmental sources.
- Of the 510 newly rendered or refined building records, 3 use OSM heights, 1 an Overture height, 155 floor-count estimates and 351 a 7 m display placeholder. Two base buildings were carried forward. These figures are evidence classes. All preview roofs are provisional. The source supports distinct footprints for Boska, Christ the Saviour and St Bonaventure. A measured roof or facade awaits a verified geometry source.
- The dedicated native map includes camera viewpoints for Park Mladen Stojanović and Boska. The acceptance boundary is a source-backed park, low-poly streetscape, preserved native spectator and reviewable landmarks. See the immutable AgentOps handoff for the final native run results and links.
- Operator review of Gate 02 was deferred. Gate 03 operator acceptance of the preview is pending.

The initial Unreal render revealed path geometry beyond the modeled ground edge. The scoped mesh builder now clips paths and paved details to the actual harvest polygon, with a direct negative test for a crossing path.
