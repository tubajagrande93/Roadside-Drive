# Gate 03 Source Expansion Handoff

Published source continuity for the accepted Banja Luka corridor. Successful entries below have verified local response bytes. Source data and images are retained privately.

## Scope and provenance

- Approved Gate 02 route: **2,145.684 m**, reviewed from the northern checkpoint toward Boska. The rendering and inventory use the Gate 02 EPSG:32633 origin and east/north frame.
- Source graph SHA-256: `69a8222ee92a48f99b1333688245bb1cb87e2e9d307c34e8cf2d6f9c1f939e8e`.
- OSM query SHA-256: `b0156d55445dbbe0e9131919b95333bb18d268c4a04180b9a8c7851d444561e9`. Four south-to-north tiles clipped to the approved 225 m route buffer. Three semantic groups per tile.
- Historical pre-orientation G03 ScenePackage SHA-256: `4eaa05f355043fb78083f536a2bc935823eda963b65f62b662bbbf994cdb89a6`.

The provider captures and OSM query are unchanged after the handedness fix. See the [orientation correction](../docs/world-builder/G03_ORIENTATION_FIX.md) for the refreshed native build.

## OpenStreetMap

Use the canonical harvest CLI to reconstruct the exact Overpass queries and tile polygons. All successes preserve original tags, geometry, provider record IDs and source vintage. Two FOSSGIS attempts for the southern buildings slot returned HTTP 502. The exact query succeeded through the Kumi mirror on an older snapshot. One mixed-vintage tile remains flagged in the evidence.

| Tile / group | Provider | Returned elements | Source UTC | Verified SHA-256 |
| --- | --- | ---: | --- | --- |
| 0 / buildings | Kumi | 254 | 2026-07-24T11:04:51Z | `2affaac66eda3a67161702c06b82059638ae42513a2768e19219aee968bba8a8` |
| 0 / public_realm | FOSSGIS | 93 | 2026-11-16T01:43:02Z | `70d2d51ac473f336c7b75621baec2cb2ae36614450737aa5eb90fd6631a70dc1` |
| 0 / street_detail | FOSSGIS | 856 | 2026-11-16T01:43:02Z | `99dceedd719525a2455a26b4e3b80a5a35d24e18e4ecd84eed6922614bf0bfe7` |
| 1 / buildings | FOSSGIS | 177 | 2026-11-16T01:44:01Z | `8698f6475c8defc2ae5c8f7d0403948d54af94481c83daccca0b68513f3370b7` |
| 1 / public_realm | FOSSGIS | 167 | 2026-11-16T01:44:01Z | `7f6403350511408364563065ac9524129b6d37014a1eac473efce2947869deec` |
| 1 / street_detail | FOSSGIS | 987 | 2026-11-16T01:45:05Z | `896f7a7a55a5b5cebc2bbf16c879f5905b5081b8ef48e5910927abfbc5f7d885` |
| 2 / buildings | FOSSGIS | 206 | 2026-11-16T01:46:05Z | `16028df29dcdb4d25db72b25ad153f8ca137a6c205ddadeb108b14a2747d2f5e` |
| 2 / public_realm | FOSSGIS | 90 | 2026-11-16T01:46:05Z | `2239a340fa15d8bb371cebc01247560dd9bac12c56f8e82e5606fdce93cc8372` |
| 2 / street_detail | FOSSGIS | 506 | 2026-11-16T01:47:04Z | `3d1c84d146333f56fe42dc3918c060f3b8fc559bbef9d603c5ddfe854fe2f359` |
| 3 / buildings | FOSSGIS | 359 | 2026-11-16T01:48:08Z | `195c9ca2b0e603a2da38f6698d72eb3638827ebb79cd05df3a4ca41ea7a33cbd` |
| 3 / public_realm | FOSSGIS | 75 | 2026-11-16T01:48:08Z | `a4529ad9ac14a50cd9dbdebedb1fd2714f887a01fddd4874d530a53a4f8d7771` |
| 3 / street_detail | FOSSGIS | 362 | 2026-11-16T01:48:08Z | `3645e6cb3145f9023be02bc631b8fd38ce921e4cf5f6c8d49f825d5f726b4e75` |

Verified response bytes: 2,310,420. Normalization produced 4,027 unique in-scope OSM features across the three groups. Source attribution: © OpenStreetMap contributors. [ODbL and attribution](https://www.openstreetmap.org/copyright)

## Overture Maps Foundation

Official STAC pinned release **2026-10-21.0**, CLI 2.1.1. Bbox in west, south, east, north order: `17.1849451,44.7667291,17.2064986,44.7864026`. STAC response SHA-256: `1b633d2ced749b39e90db0ceed74e920806ee8f18103e7d62de27746ed63df25`.

| Type | Returned | License family | Verified SHA-256 |
| --- | ---: | --- | --- |
| building | 3788 | ODbL-1.0 | `f0f2a3c4c9b12a48169849a329b16eb1aaa474dc5bb97ac2d63de503895757cd` |
| building_part | 7 | ODbL-1.0 | `dfd8c1dcd228f128a875e00abecf294f7d068f42777f1d9939e624a27d238d0b` |
| place | 2215 | CDLA-Permissive-2.0 | `ab2e8ff951e6a5db6fa0e03ace057587dd41d2d88817c74c98263aabb13f80d5` |

After polygon filtering, 2,030 Overture features remained across the three themes. Footprint fusion linked 903 duplicate candidates to OSM and queued 42 overlaps for review. Source attribution includes Overture Maps Foundation and applicable upstream providers. [Theme attribution](https://docs.overturemaps.org/attribution/)

## Wikimedia Commons reference photographs

Photographs are local references. Photographer coordinates describe viewpoints. Street and religious photographs lacked verified camera position in the retrieved metadata. No image-derived height or mesh was produced.

| File | Photographer date | License | Image SHA-256 | Metadata SHA-256 |
| --- | --- | --- | --- | --- |
| File:Park Mladen Stojanovic Banja Luka.jpg | 2025-05-11 17:11:02 | CC0 | `65f08657558f01246484c1a17b13161145f4e4bf1291acbf2669594187564048` | `2f64c362ed090be722b300f80abf6371e4a3d2f2d14a2a0208185bacd6ba6d87` |
| File:Ulica Kralja Petra Prvog Karadjordjevica Banja Luka.jpg | 2025-04-29 15:21:25 | CC0 | `d45cbaeaf2a716f130cf2505ebb16cbcd033fcda83854270c3a48efe9d7eae64` | `a5ab3f0e6c5ee82ed26164c0732e66dadf3b39a70421ba037795a89c5ed33c78` |
| File:Hram Hrista Spasitelja, Banja Luka.jpg | 2021-01-13 | CC BY-SA 4.0 | `d55e0dea49d710afab288a237706c73701b5cba6c327efbe9994da971b614d72` | `24e0c90c5e40608c344671143a49eaaa8dfe80113214e81b961844ea8ce80889` |

## Verified limits and attempted access

- OpenBuildingMap: GFZ DOI and tile index returned HTTP 200. Quadkey 120233 is `building.120233.gpkg.bz2`; the index reports 1.0 GB. The tile exceeds the bounded acquisition budget and was not downloaded. Its GEM taxonomy is categorical evidence. [DoI and dataset description](https://doi.org/10.5880/GFZ.LKUT.2025.002)
- RGURS and MapSoft public documentation returned HTTP 200. No downloadable, rights-confirmed LoD2, LiDAR or orthophoto subset for this corridor was located. **NEEDS_ACCESS**. Obtain the exact corridor coverage, acquisition vintage, horizontal CRS, vertical datum, delivery format and redistribution terms through official access. [RGURS Geoportal](https://www.rgurs.org/stranica/geoportal) · [MapSoft 3D models](https://mapsoft.rs/sr/capabilities/3d-models)
- KartaView: three HTTPS requests to the documented photo endpoint failed. Zero metadata records and zero pixels. [KartaView API](https://kartaview.org/doc/photos)
- Mapillary and OpenTopography: authenticated acquisition not executed. Reuse licensed metadata when credentials are already provided. A 30 m DSM should not drive building height or road grade.

## Reuse and expansion

1. Read the [Gate 03 runbook](../docs/world-builder/GATE_03_RUNBOOK.md). Anchor any expansion to an approved directed route and preserve existing correction records.
2. Export the new query plan before networking. Reuse archived provider+release+polygon+query hashes. Reharvest only uncovered adjacent tiles, keeping date or release separate from request date. The CLI can resume failed OSM slots without touching prior bytes.
3. Pin the Overture release from official STAC, fetch only the approved bbox, and apply the exact metric polygon locally. Review IoU 0.15–0.65 conflicts and use individual height source evidence. Keep historical data separated when change matters.
4. Preserve raw payloads, thumbnail metadata, errors, licenses and checksums under ignored storage. Publish only sanitized manifests, source counts, hashes and repeat commands. Treat newly released files as a new source revision.
