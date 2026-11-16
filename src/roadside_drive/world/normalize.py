"""Normalize a licensed OSM capture without altering source geometry or tag evidence."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from pyproj import Transformer
from shapely import normalize, transform
from shapely.geometry import LineString, Point, Polygon, shape

from .contracts import (
    BuildingFeature,
    Origin,
    Provenance,
    RoadFeature,
    Source,
    canonical,
    digest,
)
from .exports import confined
from .projections import projected_crs

METRES = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*m?\Z")
OSM_WAY = re.compile(r"[1-9][0-9]*\Z")
ATTRIBUTION = "© OpenStreetMap contributors — https://www.openstreetmap.org/copyright"
WIDTH_FALLBACK_M = 7.0


def metres(value):
    match = METRES.fullmatch(str(value).strip())
    return float(match[1]) if match and float(match[1]) > 0 else None


def tags(properties, exclude):
    result = {}
    for name, value in properties.items():
        if name in exclude or value is None:
            continue
        result[name] = (
            value if isinstance(value, str) else canonical(value).decode().strip()
        )
    return result


def stable_id(kind, identity):
    return f"osm:{kind}:{digest(canonical(identity))}"


def normalize_osm(graph, features, *, crs, aoi, query_sha, provenance):
    """Keep source IDs and directed parallel-edge identities while clipping to the metric AOI."""
    project = Transformer.from_crs(4326, projected_crs(crs), always_xy=True).transform
    boundary = transform(Polygon(aoi), project, interleaved=False)
    if not boundary.is_valid or boundary.is_empty or boundary.area <= 0:
        raise ValueError("The licensed capture must have a valid projected AOI")
    x0, y0, _, _ = boundary.bounds
    roads = {}
    for u, v, edge in graph.edges(data=True):
        ids = edge["osmid"]
        ways = sorted(
            {str(i) for i in (ids if isinstance(ids, list | tuple) else [ids])}
        )
        if not ways or not all(OSM_WAY.fullmatch(way) for way in ways):
            raise ValueError("OSM road has missing or invalid way IDs")
        line = edge.get("geometry")
        if line is None:
            line = LineString(
                [(graph.nodes[n]["x"], graph.nodes[n]["y"]) for n in (u, v)]
            )
        projected = transform(line, project, interleaved=False)
        clipped = projected.intersection(boundary)
        parts = list(clipped.geoms) if hasattr(clipped, "geoms") else [clipped]
        for part in parts:
            if part.geom_type != "LineString" or part.is_empty or part.length <= 0:
                continue
            points = tuple(part.coords)
            if projected.project(Point(points[0])) > projected.project(
                Point(points[-1])
            ):
                points = tuple(reversed(points))
            feature_id = stable_id("road", [ways, str(u), str(v), points])
            width = metres(edge.get("width"))
            lane_tag = str(edge.get("lanes", ""))
            feature = RoadFeature(
                stable_id=feature_id,
                source_elements=tuple(f"way/{way}" for way in ways),
                centerline_m=points,
                width_m=width or WIDTH_FALLBACK_M,
                width_basis="OSM_TAG_UNVERIFIED"
                if width
                else "PILOT_WIDTH_FALLBACK_V1",
                highway_class=edge.get("highway")
                if isinstance(edge.get("highway"), str)
                else None,
                lanes=int(lane_tag)
                if lane_tag.isdigit() and int(lane_tag) > 0
                else None,
                oneway=edge["oneway"] if isinstance(edge.get("oneway"), bool) else None,
                raw_tags=tags(edge, {"geometry", "osmid"}),
                confidence="ESTIMATED",
            )
            if feature_id in roads and roads[feature_id] != feature:
                raise ValueError(
                    "Conflicting parallel road features share source and geometry identity"
                )
            roads[feature_id] = feature

    buildings = {}
    for item in features:
        properties = item["properties"]
        element, number = properties.get("element"), str(properties.get("id", ""))
        if element not in {"way", "relation"} or not OSM_WAY.fullmatch(number):
            raise ValueError("OSM footprint has missing or invalid source identity")
        geometry = shape(item["geometry"])
        if (
            geometry.geom_type not in {"Polygon", "MultiPolygon"}
            or not geometry.is_valid
        ):
            raise ValueError(
                f"Unsupported OSM footprint geometry for {element}/{number}"
            )
        parts = transform(geometry, project, interleaved=False).intersection(boundary)
        for part in parts.geoms if hasattr(parts, "geoms") else (parts,):
            if part.geom_type != "Polygon" or part.area <= 0:
                continue
            if part.interiors:
                raise ValueError(
                    f"Footprint holes need an extended schema for {element}/{number}"
                )
            points = tuple(normalize(part).exterior.coords)
            feature_id = stable_id("building", [element, number, points])
            height = metres(properties.get("height"))
            feature = BuildingFeature(
                stable_id=feature_id,
                source_elements=(f"{element}/{number}",),
                footprint_m=points,
                height_m=height,
                height_basis="OSM_TAG_UNVERIFIED" if height else "UNKNOWN",
                raw_tags=tags(properties, {"element", "id"}),
                confidence="ESTIMATED" if height else "PLACEHOLDER",
            )
            if feature_id in buildings and buildings[feature_id] != feature:
                raise ValueError(
                    "Conflicting building features share source and geometry identity"
                )
            buildings[feature_id] = feature
    return Source(
        schema_version=1,
        world_id=f"osm-{query_sha[:16]}",
        source_crs="EPSG:4326",
        projected_crs=crs,
        origin=Origin(east_m=x0, north_m=y0, z_m=0),
        provenance=provenance,
        roads=tuple(roads[key] for key in sorted(roads)),
        buildings=tuple(buildings[key] for key in sorted(buildings)),
    )


@dataclass(frozen=True)
class Capture:
    manifest: dict
    graph: object
    buildings: tuple


def read_capture(root, manifest_path):
    """Load only the hashed graph and building payloads from a reviewed local capture."""
    manifest = confined(root, manifest_path)
    boundary = confined(root, "data/raw/world_builder/snapshots")
    if boundary not in manifest.parents or manifest.name != "capture_manifest.json":
        raise ValueError("Expected a reviewed local capture manifest under data/raw")
    data = json.loads(manifest.read_bytes())
    if (
        data.get("status") != "CAPTURED_REQUIRES_QA"
        or data.get("license") != "ODbL-1.0"
        or data.get("attribution") != ATTRIBUTION
        or data.get("source_crs") != "EPSG:4326"
    ):
        raise ValueError("Capture is incomplete or lacks licensed source metadata")
    for name in ("graph.graphml", "buildings.geojson"):
        if digest(confined(manifest.parent, name).read_bytes()) != data[
            "artifacts_sha256"
        ].get(name):
            raise ValueError(f"Capture hash mismatch for {name}")
    from osmnx.io import load_graphml

    graph = load_graphml(manifest.parent / "graph.graphml")
    features = json.loads((manifest.parent / "buildings.geojson").read_bytes())
    return Capture(data, graph, tuple(features["features"]))


def normalized_capture(root, file):
    captured = read_capture(root, file)
    data = captured.manifest
    provenance = Provenance(
        dataset_kind="OSM",
        title=data["title"],
        source_uri=data["source"],
        license_id=data["license"],
        attribution=data["attribution"],
        captured_utc=data["fetched_utc"],
        derivative_status="DERIVED",
    )
    return normalize_osm(
        captured.graph,
        captured.buildings,
        crs=data["projected_crs_candidate"],
        aoi=data["polygon_wgs84"],
        query_sha=data["query_sha256"],
        provenance=provenance,
    )
