"""Directed route candidates and review evidence for the Gate 02 pilot."""

from __future__ import annotations

import json
import unicodedata
from collections import defaultdict
from itertools import pairwise
from math import hypot

import networkx as nx
from pyproj import Geod, Transformer
from shapely.geometry import LineString, Polygon, mapping

from .contracts import canonical, digest
from .exports import fresh_generated_path
from .normalize import read_capture

MAX_SNAP_M = 85
MAX_LENGTH_M = 4000
GEODESIC = Geod(ellps="WGS84")
CYRILLIC = str.maketrans(
    dict(
        zip(
            "абвгдђежзијклљмнњопрстћуфхцчџш",
            (
                "a",
                "b",
                "v",
                "g",
                "d",
                "dj",
                "e",
                "z",
                "z",
                "i",
                "j",
                "k",
                "l",
                "lj",
                "m",
                "n",
                "nj",
                "o",
                "p",
                "r",
                "s",
                "t",
                "c",
                "u",
                "f",
                "h",
                "c",
                "c",
                "dz",
                "s",
            ),
            strict=True,
        )
    )
)


def normalized_name(label):
    text = str(label or "").lower().translate(CYRILLIC).replace("đ", "dj")
    return "".join(c for c in unicodedata.normalize("NFKD", text) if c.isascii())


def on_main_axis(edge):
    name = normalized_name(edge.get("name"))
    return "stojanovic" in name or "karadjordjevic" in name


def lon_lat(graph, node):
    return tuple(float(graph.nodes[node][key]) for key in ("x", "y"))


def snap_pool(graph, point, transform):
    x, y = transform(*point)
    near = []
    for node in graph:
        px, py = transform(*lon_lat(graph, node))
        distance = hypot(x - px, y - py)
        if distance <= MAX_SNAP_M:
            named = any(
                on_main_axis(edge) for *_, edge in graph.edges(node, data=True)
            ) or any(on_main_axis(edge) for *_, edge in graph.in_edges(node, data=True))
            near.append((distance, int(node), named))
    if not near:
        raise ValueError(f"No drivable node within {MAX_SNAP_M} m of an anchor")
    return sorted(near)


def choose_snap(pool, named):
    distance, node, _ = pool[0]
    if named:
        distance, node, _ = next(
            (item for item in pool if item[2] and item[0] <= distance + 25),
            pool[0],
        )
    return node, distance


def get_path(graph, start, end, named):
    def cost(edge):
        multiplier = 1 if not named or on_main_axis(edge) else 5
        return float(edge["length"]) * multiplier

    def weight(_u, _v, alternatives):
        return min(cost(edge) for edge in alternatives.values())

    try:
        nodes = nx.shortest_path(graph, start, end, weight=weight)
    except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
        raise ValueError("No directed road path between the snapped anchors") from exc
    if len(nodes) < 2:
        raise ValueError("Route anchors snap to a single graph node")
    selected = []
    for u, v in pairwise(nodes):
        key, edge = min(graph[u][v].items(), key=lambda item: (cost(item[1]), item[0]))
        selected.append((u, v, key, edge))
    return selected


def candidate(graph, mode, start, end, transform, boundary):
    a, d1 = choose_snap(start, named=mode == "named-axis")
    b, d2 = choose_snap(end, named=mode == "named-axis")
    length = 0.0
    coordinates = []
    edges = []
    groups = []
    length_by_name = defaultdict(float)
    for u, v, key, edge in get_path(graph, a, b, mode == "named-axis"):
        p, q = lon_lat(graph, u), lon_lat(graph, v)
        # Gate 02 acquisition deliberately leaves the graph unsimplified.
        points = [p, q]
        if edge.get("geometry") is not None:
            points = list(edge["geometry"].coords)
            origin = transform(*p)
            if hypot(
                *(s - t for s, t in zip(transform(*points[-1]), origin, strict=True))
            ) < hypot(
                *(s - t for s, t in zip(transform(*points[0]), origin, strict=True))
            ):
                points.reverse()
        if points[0] != p or points[-1] != q or (coordinates and coordinates[-1] != p):
            raise ValueError("Directed edge geometry does not join its graph endpoints")
        coordinates.extend(points if not coordinates else points[1:])
        distance = GEODESIC.line_length(*(zip(*points, strict=True)))
        name = str(edge.get("name") or "UNNAMED")
        if not groups or groups[-1] != name:
            groups.append(name)
        length_by_name[name] += distance
        length += distance
        edges.append(
            {
                "key": [int(u), int(v), int(key)],
                "way": edge["osmid"],
                "name": name,
                "oneway": edge["oneway"],
                "length_m": round(distance, 3),
            }
        )
    shape = LineString([transform(*point) for point in coordinates])
    if length > MAX_LENGTH_M or not boundary.covers(shape):
        raise ValueError("Candidate leaves the reviewed AOI or exceeds the route limit")
    return {
        "id": mode,
        "route_status": "CANDIDATE_REQUIRES_OPERATOR_VISUAL_REVIEW",
        "geometry": mapping(LineString(coordinates)),
        "edges": edges,
        "length_m": round(length, 3),
        "names": groups,
        "length_by_name_m": {
            key: round(value, 3) for key, value in length_by_name.items()
        },
        "snap": {
            "start": {
                "node": a,
                "position_wgs84": lon_lat(graph, a),
                "offset_m": round(d1, 3),
            },
            "end": {
                "node": b,
                "position_wgs84": lon_lat(graph, b),
                "offset_m": round(d2, 3),
            },
        },
    }


def review_route(capture):
    manifest = capture.manifest
    if manifest.get("scope") != "banja-luka-g02":
        raise ValueError("Route review requires a Gate 02 scoped capture")
    graph = capture.graph
    transform = Transformer.from_crs(
        4326, manifest["projected_crs_candidate"], always_xy=True
    ).transform
    boundary = Polygon([transform(*point) for point in manifest["polygon_wgs84"]])
    start, end = [
        snap_pool(graph, point, transform) for point in manifest["centerline_wgs84"]
    ]
    candidates = []
    errors = {}
    for mode in ("directed-shortest", "named-axis"):
        try:
            candidates.append(candidate(graph, mode, start, end, transform, boundary))
        except ValueError as error:
            errors[mode] = str(error)
    if not candidates:
        raise ValueError(f"No reviewable route: {errors}")
    body = {
        "schema_version": 1,
        "status": "ROUTE_REVIEW_REQUIRED",
        "graph_sha256": manifest["artifacts_sha256"]["graph.graphml"],
        "query_sha256": manifest["query_sha256"],
        "anchors_wgs84": manifest["centerline_wgs84"],
        "candidate_errors": errors,
        "candidates": candidates,
    }
    return {**body, "content_sha256": digest(canonical(body))}


def write_route_review(root, capture_path, output):
    capture = read_capture(root, capture_path)
    report = review_route(capture)
    folder = fresh_generated_path(root, output)
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "review.json").write_bytes(canonical(report))
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": item["id"],
                "geometry": item["geometry"],
                "properties": {
                    key: value
                    for key, value in item.items()
                    if key not in ("geometry", "edges")
                },
            }
            for item in report["candidates"]
        ],
    }
    (folder / "candidates.geojson").write_text(
        json.dumps(geojson, ensure_ascii=False), encoding="utf-8"
    )
    return report
