"""Normalize sealed acquisition records while preserving original provider IDs."""

import json
from collections import Counter
from dataclasses import dataclass

from shapely import transform
from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import polygonize, unary_union

from ..contracts import digest
from ..exports import confined
from ..normalize import metres


@dataclass(frozen=True)
class Feature:
    identity: str
    geometry: object
    attributes: dict
    source: str
    sha: str
    vintage: str | None


def tokens(row):
    return [(part["lon"], part["lat"]) for part in row.get("geometry", []) if part]


def osm_geometry(row):
    if row["type"] == "node":
        return Point(row["lon"], row["lat"])
    if row["type"] == "way":
        points = tokens(row)
        if len(points) < 2:
            return None
        tags = row.get("tags", {})
        area = any(
            key in tags for key in ("building", "building:part", "leisure", "landuse")
        )
        area |= tags.get("natural") in {"wood", "scrub"} or tags.get("area") == "yes"
        return (
            Polygon(points) if area and points[0] == points[-1] else LineString(points)
        )
    outers, inners = [], []
    for member in row.get("members", ()):
        pts = tokens(member)
        role = member.get("role")
        if len(pts) >= 2 and role in {"outer", "inner"}:
            (outers if role == "outer" else inners).append(LineString(pts))
    if not outers:
        return None
    shell = unary_union(list(polygonize(outers)))
    holes = unary_union(list(polygonize(inners)))
    return shell.difference(holes) if not shell.is_empty else None


def read_artifact(root, base, record):
    file = confined(root, base / record["file"])
    raw = file.read_bytes()
    if digest(raw) != record["sha256"]:
        raise ValueError(f"Raw artifact hash mismatch: {file.name}")
    return json.loads(raw)


def normalize_harvest(root, result_path, scope, provider):
    path = confined(root, result_path)
    manifest = json.loads(path.read_bytes())
    base = path.parent.relative_to(root)
    records = manifest["records"]
    kind = isinstance(records, dict)
    by_id = {}
    skipped = Counter()
    for group, record in records.items() if kind else enumerate(records):
        if record["status"] != "OK":
            skipped["failed_source_requests"] += 1
            continue
        payload = read_artifact(root, base, record)
        for row in payload["features" if kind else "elements"]:
            properties = row.get("properties" if kind else "tags", {})
            if kind:
                key = f"overture:{group}/{row.get('id') or properties.get('id')}"
                geometry = shape(row["geometry"]) if row.get("geometry") else None
                if group == "building_part":
                    properties = {**properties, "building:part": "yes"}
                elif group == "building":
                    properties = {**properties, "building": "yes"}
            else:
                key = f"osm:{row['type']}/{row['id']}"
                if not properties:
                    continue
                geometry = osm_geometry(row)
            if geometry is None or geometry.is_empty or not geometry.is_valid:
                skipped["unresolved_or_invalid_geometry"] += 1
                continue
            metric = transform(geometry, scope.project, interleaved=False)
            if not scope.boundary.intersects(metric):
                skipped["outside_polygon"] += 1
                continue
            feature = Feature(
                key,
                metric,
                properties,
                provider,
                record["sha256"],
                record.get("source_utc", manifest.get("release")),
            )
            if key in by_id:
                skipped["tile_duplicates"] += 1
            by_id[key] = feature
    return list(by_id.values()), dict(skipped)


def numeric_height(value):
    result = metres(value)
    return result if result is not None and 1 <= result <= 160 else None


def height_evidence(osm_tags, overture_tags):
    osm = numeric_height(osm_tags.get("height"))
    overture = numeric_height(overture_tags.get("height"))
    levels = numeric_height(
        osm_tags.get("building:levels") or overture_tags.get("num_floors")
    )
    if osm:
        return osm, "OSM_HEIGHT_TAG", "ESTIMATED"
    if overture:
        return overture, "OVERTURE_NUMERIC_HEIGHT", "ESTIMATED"
    if levels and levels <= 50:
        return levels * 3.1, "LEVELS_TIMES_3_1_M", "ESTIMATED"
    return 7.0, "PLACEHOLDER_7_M", "PLACEHOLDER"


def baseline_footprints(scope):
    """A previous licensed capture provides coverage when a semantic query fails."""
    manifest = scope.base_capture.manifest
    sha = manifest["artifacts_sha256"]["buildings.geojson"]
    for row in scope.base_capture.buildings:
        properties = row["properties"]
        geometry = shape(row["geometry"])
        if not geometry.is_valid:
            continue
        geometry = transform(geometry, scope.project, interleaved=False)
        if scope.boundary.intersects(geometry):
            identity = f"osm:{properties['element']}/{properties['id']}"
            yield Feature(
                identity,
                geometry,
                properties,
                "GATE02_OSM",
                sha,
                manifest["fetched_utc"],
            )
