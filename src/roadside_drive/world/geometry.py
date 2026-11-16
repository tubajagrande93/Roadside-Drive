"""Small, deterministic road and building greybox meshing."""

from __future__ import annotations

from itertools import pairwise
from math import isfinite

from shapely import constrained_delaunay_triangles, normalize, union_all
from shapely.geometry import LineString, Polygon, box
from shapely.geometry.polygon import orient

from .projections import MAX_PILOT_OFFSET_M

PLACEHOLDER_HEIGHT_M = 6.0


def checked_polygon(points):
    polygon = Polygon(points)
    if not polygon.is_valid or polygon.area <= 0:
        raise ValueError("Invalid or zero-area footprint")
    return polygon


def triangles(polygon, z):
    if polygon.geom_type == "MultiPolygon":
        return [
            face
            for part in sorted(polygon.geoms, key=lambda item: normalize(item).wkb)
            for face in triangles(part, z)
        ]
    if polygon.is_empty or polygon.geom_type != "Polygon" or not polygon.is_valid:
        raise ValueError("Road or building surface must be a valid non-empty polygon")
    result = []
    for tri in constrained_delaunay_triangles(normalize(polygon)).geoms:
        if tri.area <= 0:
            raise ValueError("Degenerate polygon triangle")
        ring = list(orient(tri, sign=1).exterior.coords)[:-1]
        start = min(range(3), key=ring.__getitem__)
        ring = ring[start:] + ring[:start]
        result.append(tuple((float(x), float(y), z) for x, y in ring))
    if not result:
        raise ValueError("Missing triangles")
    return sorted(result)


def building_shell(polygon, height):
    top = triangles(polygon, height)
    faces = [*top, *(tuple((x, y, 0.0) for x, y, _ in reversed(face)) for face in top)]
    ring = list(orient(polygon, sign=1).exterior.coords)
    for a, b in pairwise(ring):
        a0, b0, a1, b1 = (*a, 0.0), (*b, 0.0), (*a, height), (*b, height)
        faces.extend(((a0, b0, b1), (a0, b1, a1)))
    return faces


def local_points(points, origin):
    values = [(x - origin.east_m, y - origin.north_m) for x, y in points]
    if any(
        not isfinite(v) or abs(v) > MAX_PILOT_OFFSET_M
        for point in values
        for v in point
    ):
        raise ValueError("Synthetic feature exceeds local pilot bounds")
    return values


def mesh_features(roads, buildings, origin):
    """Yield ordered object meshes and validate the topology of the synthetic pilot."""
    if len(roads) != 2 or len(buildings) < 3:
        raise ValueError("Pilot requires two roads and at least three buildings")
    lines = [LineString(local_points(r.centerline_m, origin)) for r in roads]
    intersection = lines[0].intersection(lines[1])
    if any(line.length <= 0 or not line.is_simple for line in lines):
        raise ValueError("Roads must be nonzero simple lines")
    if not lines[0].crosses(lines[1]) or intersection.geom_type != "Point":
        raise ValueError("Roads must meet at one interior crossing")
    surfaces = [
        line.buffer(f.width_m / 2, cap_style="flat", join_style="mitre")
        for line, f in zip(lines, roads, strict=True)
    ]
    if surfaces[0].intersection(surfaces[1]).area <= 0:
        raise ValueError("Road surface connectivity failed")
    occupied = union_all(surfaces)
    meshes = [
        (str(roads[0].stable_id), triangles(surfaces[0], 0.0)),
        (str(roads[1].stable_id), triangles(surfaces[1].difference(surfaces[0]), 0.0)),
    ]
    footprints = []
    for feature in buildings:
        footprint = checked_polygon(local_points(feature.footprint_m, origin))
        if footprint.intersection(occupied).area > 0 or any(
            footprint.intersection(other).area > 0 for other in footprints
        ):
            raise ValueError("Buildings must not overlap other pilot surfaces")
        footprints.append(footprint)
        meshes.append(
            (
                str(feature.stable_id),
                building_shell(
                    footprint,
                    feature.height_m
                    if feature.height_m is not None
                    else PLACEHOLDER_HEIGHT_M,
                ),
            )
        )
    x0, y0, x1, y1 = union_all([occupied, *footprints]).bounds
    meshes.append(("ground", triangles(box(x0 - 10, y0 - 10, x1 + 10, y1 + 10), -0.05)))
    return sorted(meshes)
