"""Shape a reviewed OSM corridor for the canonical ScenePackage writer."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime

from pyproj import Transformer
from shapely import line_merge, normalize, set_precision, transform
from shapely.affinity import translate
from shapely.geometry import LineString, MultiLineString, Point, Polygon, shape

from .contracts import (
    BuildingFeature,
    Contract,
    Digest,
    Origin,
    Positive,
    Provenance,
    RoadFeature,
    Source,
    canonical,
    digest,
)
from .corridor_route import lon_lat, on_main_axis, review_route
from .exports import CANDIDATE_LABEL, CORRIDOR_LABEL, build_scene, confined
from .normalize import metres, read_capture, stable_id, tags

WIDTH_POLICY = "configs/worlds/banja_luka_gate02_widths.json"
PREVIEW_BUFFER_M = 65


class WidthPolicy(Contract):
    lane_width_m: Positive
    class_width_m: dict[str, Positive]


class RouteApproval(Contract):
    operator_decision: str
    operator_reference: str
    recorded_utc: datetime
    review_sha256: Digest
    graph_sha256: Digest
    candidate_id: str


def verify_route(root, capture, report_path, candidate_id, approval_path):
    report = json.loads(confined(root, report_path).read_bytes())
    if canonical(report) != canonical(review_route(capture)):
        raise ValueError(
            "Review does not match the current hashed capture and route solver"
        )
    candidates = {item["id"]: item for item in report["candidates"]}
    if candidate_id not in candidates:
        raise ValueError("Unknown route candidate")
    if approval_path is None:
        return report, candidates[candidate_id], None
    approval_file = confined(root, approval_path)
    if confined(root, "data/raw/world_builder/approvals") not in approval_file.parents:
        raise ValueError("Route approval must be a local approval record")
    approval = RouteApproval.model_validate_json(approval_file.read_bytes())
    if (
        approval.operator_decision != "ACCEPT_ROUTE"
        or not approval.operator_reference.strip()
        or approval.recorded_utc.utcoffset() is None
        or approval.review_sha256 != report["content_sha256"]
        or approval.graph_sha256 != report["graph_sha256"]
        or approval.candidate_id != candidate_id
    ):
        raise ValueError("Operator route approval does not match this exact review")
    return report, candidates[candidate_id], approval


def width_for(edge, policy):
    width = metres(edge.get("width"))
    lanes_tag = str(edge.get("lanes", ""))
    lanes = (
        int(lanes_tag) if lanes_tag.isdecimal() and 0 < int(lanes_tag) <= 12 else None
    )
    if width is not None and 0.5 <= width <= 40:
        return width, "OSM_WIDTH_TAG_UNVERIFIED", "ESTIMATED", lanes
    if lanes is not None:
        return (
            lanes * policy.lane_width_m,
            "OSM_LANES_TIMES_ESTIMATED_LANE_WIDTH",
            "ESTIMATED",
            lanes,
        )
    fallback = policy.class_width_m.get(
        edge.get("highway"), policy.class_width_m["default"]
    )
    return fallback, "ROAD_CLASS_PLACEHOLDER", "PLACEHOLDER", None


def road_edges(graph, candidate, route, project):
    selected = {tuple(item["key"]) for item in candidate["edges"]}
    ways = defaultdict(dict)
    for u, v, key, data in graph.edges(keys=True, data=True):
        direct = (u, v, key) in selected
        if not direct and not on_main_axis(data):
            continue
        points = [project(*lon_lat(graph, node)) for node in (u, v)]
        part = LineString(points)
        if part.is_empty or part.length <= 0:
            continue
        if not direct:
            a, b = map(Point, points)
            if (
                max(a.distance(route), b.distance(route)) > 42
                or abs(route.project(a) - route.project(b)) < 0.55 * part.length
            ):
                continue
        way = str(data["osmid"])
        pair = tuple(sorted([u, v]))
        existing = ways[way].get(pair)
        if existing is None or direct:
            ways[way][pair] = part, data, direct
    return ways


def road_features(graph, candidate, route, project, policy):
    result = []
    extras = []
    for way, parts in sorted(road_edges(graph, candidate, route, project).items()):
        merged = line_merge(MultiLineString([part for part, *_ in parts.values()]))
        lines = list(merged.geoms) if hasattr(merged, "geoms") else [merged]
        for line in sorted(lines, key=lambda item: normalize(item).wkb):
            owned = [
                (pair, edge, direct)
                for pair, (part, edge, direct) in parts.items()
                if line.covers(part)
            ]
            direct = any(item[2] for item in owned)
            if not direct:
                extras.append(way)
            data = owned[0][1]
            width, basis, confidence, lanes = width_for(data, policy)
            nodes = sorted({node for pair, _, _ in owned for node in pair})
            properties = tags(data, {"geometry", "osmid", "length", "reversed"})
            properties["corridor_role"] = (
                "DIRECTED_ROUTE" if direct else "PARALLEL_NAMED_WAY_CANDIDATE"
            )
            result.append(
                RoadFeature(
                    stable_id=stable_id("road", [way, nodes]),
                    source_elements=(f"way/{way}",),
                    centerline_m=tuple(normalize(line).coords),
                    width_m=width,
                    width_basis=basis,
                    highway_class=data.get("highway"),
                    lanes=lanes,
                    oneway=data.get("oneway"),
                    raw_tags=properties,
                    confidence=confidence,
                )
            )
    return tuple(sorted(result, key=lambda feature: feature.stable_id)), sorted(
        set(extras)
    )


def building_features(records, boundary, project):
    result = []
    discarded = Counter()
    for record in records:
        geometry = shape(record["geometry"])
        props = record["properties"]
        metric = transform(geometry, project, interleaved=False)
        if not metric.intersects(boundary):
            continue
        if not metric.is_valid:
            discarded["invalid_footprint"] += 1
            continue
        if not boundary.covers(metric):
            discarded["extends_past_scene_boundary"] += 1
            continue
        parts = metric.geoms if metric.geom_type == "MultiPolygon" else (metric,)
        for ordinal, part in enumerate(
            sorted(parts, key=lambda item: normalize(item).wkb)
        ):
            if part.interiors or part.area < 1:
                discarded["courtyard_or_tiny_footprint"] += 1
                continue
            element = f"{props['element']}/{props['id']}"
            height = metres(props.get("height"))
            result.append(
                BuildingFeature(
                    stable_id=stable_id("building", [element, ordinal]),
                    source_elements=(element,),
                    footprint_m=tuple(normalize(part).exterior.coords),
                    height_m=height,
                    height_basis="OSM_TAG_UNVERIFIED" if height else "UNKNOWN",
                    raw_tags=tags(props, {"element", "id"}),
                    confidence="ESTIMATED" if height else "PLACEHOLDER",
                )
            )
    return tuple(sorted(result, key=lambda feature: feature.stable_id)), dict(discarded)


def build_corridor(
    root,
    capture_path,
    review_path,
    candidate_id,
    output,
    patches=None,
    approval_path=None,
):
    captured = read_capture(root, capture_path)
    report, candidate, approval = verify_route(
        root, captured, review_path, candidate_id, approval_path
    )
    data = captured.manifest
    crs = data["projected_crs_candidate"]
    project = Transformer.from_crs(4326, crs, always_xy=True).transform
    unproject = Transformer.from_crs(crs, 4326, always_xy=True).transform
    east, north = project(*data["centerline_wgs84"][0])
    route = transform(shape(candidate["geometry"]), project, interleaved=False)
    acquired = Polygon([project(*point) for point in data["polygon_wgs84"]])
    floor = route.buffer(PREVIEW_BUFFER_M).intersection(acquired)
    roads, parallel = road_features(
        captured.graph,
        candidate,
        route,
        project,
        WidthPolicy.model_validate_json(confined(root, WIDTH_POLICY).read_bytes()),
    )
    buildings, discarded = building_features(captured.buildings, floor, project)
    provenance = Provenance(
        title=data["title"],
        dataset_kind="OSM",
        source_uri=data["source"],
        license_id=data["license"],
        attribution=data["attribution"],
        captured_utc=data["fetched_utc"],
        derivative_status="DERIVED",
    )
    source = Source(
        schema_version=1,
        world_id=f"osm-{data['query_sha256'][:16]}",
        source_crs="EPSG:4326",
        projected_crs=crs,
        origin=Origin(east_m=east, north_m=north, z_m=0),
        provenance=provenance,
        roads=roads,
        buildings=buildings,
    )
    if floor.geom_type != "Polygon":
        raise ValueError("Route floor must cover one contiguous corridor")
    checkpoints = [route.interpolate(part, normalized=True) for part in (0, 0.5, 1)]
    corridor = {
        "label": CORRIDOR_LABEL if approval else CANDIDATE_LABEL,
        "aoi": tuple(unproject(x, y) for x, y in floor.exterior.coords),
        "floor": set_precision(translate(floor, -east, -north), 0.01),
        "evidence": {
            "route_review_sha256": report["content_sha256"],
            "route_candidate": candidate_id,
            "route_status": "OPERATOR_ACCEPTED"
            if approval
            else "ROUTE_REVIEW_REQUIRED",
            "route_acceptance_sha256": digest(
                canonical(approval.model_dump(mode="json"))
            )
            if approval
            else None,
            "route_length_geodesic_m": candidate["length_m"],
            "route_names": candidate["names"],
            "query_sha256": data["query_sha256"],
            "graph_sha256": report["graph_sha256"],
            "snap": candidate["snap"],
            "adjacent_named_way_candidates": parallel,
            "road_width_bases": dict(Counter(road.width_basis for road in roads)),
            "building_discards": discarded,
            "building_heights_unknown": sum(
                item.height_m is None for item in buildings
            ),
            "checkpoints_local_m": [
                [point.x - east, point.y - north] for point in checkpoints
            ],
            "route_local_m": [[x - east, y - north] for x, y in route.coords],
            "object_source_centers_wgs84": {
                feature.stable_id: unproject(center.x, center.y)
                for feature in (*roads, *buildings)
                for center in (
                    LineString(feature.centerline_m).centroid
                    if isinstance(feature, RoadFeature)
                    else Polygon(feature.footprint_m).centroid,
                )
            },
            "building_smoke_point_local_m": next(
                (
                    [point.x - east, point.y - north]
                    for feature in buildings
                    for point in (Polygon(feature.footprint_m).representative_point(),)
                    if (feature.height_m is None or feature.height_m > 3.0)
                ),
                None,
            ),
            "floor_offset_m": -0.12,
            "route_checkpoints_wgs84": [
                unproject(point.x, point.y) for point in checkpoints
            ],
        },
    }
    return build_scene(
        root,
        output,
        source,
        canonical(source.model_dump(mode="json")),
        patches,
        corridor=corridor,
    )
