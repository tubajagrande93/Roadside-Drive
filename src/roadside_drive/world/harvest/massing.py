"""Low-cost, source-backed corridor massing with explicit provisional roof shapes."""

import itertools
from collections import defaultdict

from shapely import intersection, normalize, set_precision
from shapely.affinity import translate
from shapely.geometry import LineString, Point, box
from shapely.geometry.polygon import orient
from shapely.ops import split

from ..geometry import triangles


def polygon_parts(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == "Polygon":
        return [geometry]
    return [
        part for part in getattr(geometry, "geoms", ()) if part.geom_type == "Polygon"
    ]


def polygon_shell(polygon, height, roof_shape=None, rise=None):
    """Retain courtyard holes and support tagged gables on near-rectangular footprints."""
    roof = [polygon]
    x1, y1, x2, y2 = polygon.bounds

    def top(_x, _y):
        return height

    if (
        roof_shape in {"gabled", "gable"}
        and rise
        and not polygon.interiors
        and polygon.area >= (x2 - x1) * (y2 - y1) * 0.7
    ):
        x_axis = (x2 - x1) >= (y2 - y1)
        mid = (y1 + y2) / 2 if x_axis else (x1 + x2) / 2
        half = (y2 - y1) / 2 if x_axis else (x2 - x1) / 2
        ridge = (
            LineString([(x1 - 1, mid), (x2 + 1, mid)])
            if x_axis
            else LineString([(mid, y1 - 1), (mid, y2 + 1)])
        )
        roof = polygon_parts(split(polygon, ridge))

        def top(x, y):
            return height - rise * min(abs((y if x_axis else x) - mid) / half, 1)

    faces = [
        tuple((x, y, top(x, y)) for x, y, _ in face)
        for plane in roof
        for face in triangles(plane, 0.0)
    ]
    for plane in roof:
        boundary = orient(plane, sign=1)
        for ring in [boundary.exterior, *boundary.interiors]:
            pts = list(ring.coords)
            for a, b in itertools.pairwise(pts):
                if roof != [polygon] and not polygon.boundary.covers(
                    LineString([a, b])
                ):
                    continue
                a0, b0, a1, b1 = (*a, 0.0), (*b, 0.0), (*a, top(*a)), (*b, top(*b))
                faces.extend(((a0, b0, b1), (a0, b1, a1)))
    return faces, len(roof) > 1


def local(geometry, origin):
    return set_precision(translate(geometry, -origin.east_m, -origin.north_m), 0.02)


def name_group(feature):
    return str(feature.attributes.get("name", ""))


def parks(scope, features, origin):
    output = []
    for feature in features:
        if feature.attributes.get("leisure") not in {"park", "garden"}:
            continue
        geometry = feature.geometry.intersection(scope.boundary)
        polygons = sorted(
            polygon_parts(local(geometry, origin)), key=lambda part: normalize(part).wkb
        )
        faces = [
            face
            for poly in polygons
            if poly.area > 5
            for face in triangles(poly, -0.04)
        ]
        if faces:
            output.append(
                (
                    feature.identity,
                    "park",
                    faces,
                    [feature.identity],
                    name_group(feature),
                )
            )
    return output


def surface_faces(geometry, boundary, z):
    clipped = intersection(geometry, boundary, grid_size=0.02)
    return [
        face
        for part in polygon_parts(clipped)
        if part.area > 0.2
        for face in triangles(part, z)
    ]


def street_meshes(scope, features, origin, classify):
    boundary = local(scope.boundary, origin)
    groups = defaultdict(list)
    for feature in features:
        tags = feature.attributes
        geometry = local(feature.geometry, origin)
        name = None
        if tags.get("natural") == "tree" and geometry.geom_type == "Point":
            x, y = geometry.x, geometry.y
            trunk = box(x - 0.22, y - 0.22, x + 0.22, y + 0.22)
            faces, _ = polygon_shell(trunk, 2.4)
            base = list(Point(x, y).buffer(1.7, quad_segs=2).exterior.coords)
            faces += [
                ((*a, 2.30), (*b, 2.30), (x, y, 5.0))
                for a, b in itertools.pairwise(base)
            ]
            name = "vegetation"
        elif (
            tags.get("highway") in {"footway", "path", "pedestrian", "cycleway"}
            and geometry.geom_type == "LineString"
        ):
            surface = geometry.buffer(0.75, cap_style="flat")
            if surface.area < 0.2:
                continue
            faces = surface_faces(surface, boundary, -0.02)
            name = "path"
        elif (
            tags.get("highway") in {"crossing", "traffic_signals"}
            and geometry.geom_type == "Point"
        ):
            x, y = geometry.x, geometry.y
            footprint = box(x - 0.25, y - 0.25, x + 0.25, y + 0.25)
            height = 2.2 if tags.get("highway") == "traffic_signals" else 0.05
            faces, _ = polygon_shell(footprint, height)
            name = "street"
        elif (
            tags.get("junction") == "roundabout" and geometry.geom_type == "LineString"
        ):
            surface = geometry.buffer(3, cap_style="flat")
            faces = surface_faces(surface, boundary, -0.015)
            name = "street"
        elif tags.get("leisure") in {"pitch", "playground"}:
            faces = surface_faces(geometry, boundary, -0.01)
            name = "path"
        if not name or not faces:
            continue
        where = classify(scope, feature.geometry)["station"]
        groups[name, where].append((feature.identity, faces))
    return [
        (
            f"g03:{name}:{index}",
            name,
            [face for _, faces in group for face in faces],
            [identifier for identifier, _ in group],
            f"Station {index + 1:02d} {name}",
        )
        for (name, index), group in sorted(groups.items())
    ]


def surroundings(scope, origin):
    extension = local(scope.boundary, origin)
    return [
        face
        for polygon in polygon_parts(extension)
        for face in triangles(polygon, -0.16)
    ]
