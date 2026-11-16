# Gate 01 sources and licenses

| Source | Status | Evidence |
| --- | --- | --- |
| Synthetic crossroads | PROJECT_TEST_DATA | Authored fixture. Values describe a test world and have no association with Banja Luka data. |
| OpenStreetMap | OSM GO PENDING | The pilot config has no approved coordinates. Candidate corridor and metric limits are explicit. |
| Elevation, aerial and street imagery | Outside the pilot capture | Flat provisional ground. Evaluate licensing and vertical datum independently before adding another source. |

Use `prepare-aoi` to validate the locally proposed centerline and polygon and print the exact query fingerprint. Approve only a 500–1000 m bounded centerline and surrounding polygon. The optional pilot capture uses OSMnx drive edges and building footprints through the specified Overpass endpoint. Source tags, raw response cache, hashes, acquisition time, source and attribution stay under ignored data storage. A failed capture remains visible. Live capture requires both explicit `--allow-network` and a local approval record with decision `OSM GO`, timestamp, exact query SHA‑256, endpoint, license and operator reference. Never generate that record from a guessed AOI.

After a reviewed capture, `normalize-capture --capture <local-manifest> --output <new-generated-json>` validates the graph and footprint digests, preserves aggregated source IDs and keeps missing building height null. This derivative remains local. The current GLB package generator targets the synthetic fixture.

Before redistribution, review when attribution and ODbL obligations apply to the specific database, derivative or produced work. OSM data is offered by OpenStreetMap contributors under ODbL. Preserve attribution and add no proprietary imagery or unlicensed assets. The ignored `data/raw/` directory keeps capture artifacts and approval records out of source. [OpenStreetMap copyright and license](https://www.openstreetmap.org/copyright) · [OSMF attribution guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines)
