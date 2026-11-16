"""Two polygon-scoped requests, with OSMnx parsing the preserved raw XML offline."""

from __future__ import annotations

from xml.etree import ElementTree

import requests
from shapely.geometry import Polygon

MAX_RESPONSE_BYTES = 16 * 1024 * 1024
USER_AGENT = "RoadsideDrive-G02/0.1 (+https://github.com/tubajagrande93/Roadside-Drive)"
UNDESIRED_HIGHWAYS = (
    "abandoned|bridleway|bus_guideway|construction|corridor|cycleway|elevator|"
    "escalator|footway|path|pedestrian|planned|platform|proposed|raceway|razed|"
    "steps|track"
)


def polygon_queries(ring):
    # Overpass poly syntax is latitude longitude with an implicit closing edge.
    polygon = " ".join(f"{lat:.12f} {lon:.12f}" for lon, lat in ring[:-1])
    scope = f'(poly:"{polygon}")'
    # Retain public driving branches and connectors while excluding non-driving
    # ways and private motor access. Unsimplified XML keeps original way IDs.
    roads = (
        f'way["highway"]["highway"!~"^({UNDESIRED_HIGHWAYS})$"]["area"!="yes"]'
        f'["motor_vehicle"!="no"]["motorcar"!="no"]["access"!="private"]'
        f'["service"!~"^(parking_aisle|drive-through|driveway|emergency_access)$"]'
        f"{scope};"
    )
    buildings = (
        f'(way["building"]{scope};relation["building"]["type"="multipolygon"]{scope};);'
    )
    return {
        "roads": f"[out:xml][timeout:60];{roads}(._;>>;);out body qt;",
        "buildings": f"[out:xml][timeout:60];{buildings}(._;>>;);out body qt;",
    }


def download_xml(session, endpoint, query, target):
    """Preserve an entire valid response before the downstream parser runs."""
    temporary = target.with_suffix(".xml.tmp")
    with session.post(
        f"{endpoint}/interpreter",
        data={"data": query},
        headers={"User-Agent": USER_AGENT},
        timeout=(10, 90),
        stream=True,
        allow_redirects=False,
    ) as response:
        if response.status_code != 200:
            retry_after = response.headers.get("Retry-After")
            raise OSError(
                f"Overpass HTTP {response.status_code} for {target.stem}; "
                f"Retry-After: {retry_after or 'not provided'}"
            )
        count = 0
        with temporary.open("xb") as output:
            for part in response.iter_content(chunk_size=65536):
                count += len(part)
                if count > MAX_RESPONSE_BYTES:
                    raise ValueError("Overpass response exceeds the pilot byte cap")
                output.write(part)
    # Overpass can return HTTP 200 with a runtime error in a remark.
    root = ElementTree.parse(temporary).getroot()
    if root.tag != "osm" or root.find("remark") is not None:
        raise ValueError(f"{target.stem}: incomplete or invalid Overpass response")
    metadata = root.find("meta")
    source_date = metadata.get("osm_base") if metadata is not None else None
    if not source_date:
        raise ValueError(f"{target.stem}: missing OSM source timestamp")
    temporary.rename(target)
    return source_date


def capture_polygon(ox, request, output):
    with requests.Session() as session:
        raw = {
            name: download_xml(
                session, request["source"], query, output / f"{name}.xml"
            )
            for name, query in request["overpass_ql"].items()
        }
    graph = ox.graph.graph_from_xml(
        output / "roads.xml", simplify=False, retain_all=True
    )
    if not graph.number_of_edges():
        raise ValueError("Bounded capture returned no driving edges")
    buildings = ox.features.features_from_xml(
        output / "buildings.xml",
        polygon=Polygon(request["polygon_wgs84"]),
        tags={"building": True},
    )
    buildings = buildings[
        buildings.geometry.geom_type.isin(("Polygon", "MultiPolygon"))
    ]
    return graph, buildings, raw
