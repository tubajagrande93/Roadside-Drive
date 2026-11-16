"""Recover exact parent footprints and mask source-backed pedestrian skins."""

import json
from io import BytesIO
from math import dist

import numpy as np
import trimesh
from pyproj import Transformer
from shapely import union_all
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import transform

from ..geometry import triangles
from ..harvest.features import osm_geometry, read_artifact
from ..normalize import metres
from ..orientation import GEOGRAPHIC_EXCHANGE, local_to_gltf


def area_only(shape):
    if shape.geom_type in {"Polygon", "MultiPolygon"}:
        return shape
    return union_all([part for part in getattr(shape, "geoms", ()) if part.area])


def parent_footprints(path, scene, envelope):
    # The orthonormal basis from the shared ENU writer decodes GLB positions.
    basis = np.array([local_to_gltf(axis, GEOGRAPHIC_EXCHANGE) for axis in np.eye(3)])
    result = {}
    for record in scene.objects:
        if record.kind not in {"road", "ground", "context", "building", "park", "path"}:
            continue
        low, high = record.bounds_m
        if not envelope.intersects(box(*low[:2], *high[:2])):
            continue
        mesh = trimesh.load(
            BytesIO((path / record.file).read_bytes()),
            file_type="glb",
            force="mesh",
            process=False,
        )
        local = mesh.vertices @ basis.T
        faces = local[mesh.faces, :2]
        loops = [Polygon(face) for face in faces]
        shape = union_all([poly for poly in loops if poly.area > 1e-9], grid_size=0.001)
        if not shape.is_empty:
            result[record.stable_id] = (record, shape)
    return result


def mapped_pedestrian(root, osm_file, scene, window):
    """Use existing sealed OSM tiles. Capture widths are display estimates if absent."""
    if not osm_file.is_relative_to(root):
        raise ValueError("OSM result must be inside the local artifact root")
    result = json.loads(osm_file.read_bytes())
    project = Transformer.from_crs(4326, scene.projected_crs, always_xy=True).transform
    pedestrian, exclusions, kerbs = {}, {}, {}

    def local(lon, lat):
        east, north = project(lon, lat)
        return east - scene.origin.east_m, north - scene.origin.north_m

    filter_area = window.buffer(5)
    for job, record in zip(result["jobs"], result["records"], strict=True):
        if record["status"] != "OK" or job["group"] == "buildings":
            continue
        payload = read_artifact(root, osm_file.parent.relative_to(root), record)
        for row in payload["elements"]:
            tags = row.get("tags", {})
            highway = tags.get("highway")
            sidewalk = tags.get("footway") == "sidewalk" or highway == "pedestrian"
            crossing = tags.get("footway") == "crossing" or highway == "crossing"
            access = highway in {
                "service",
                "living_street",
                "residential",
                "unclassified",
            }
            curb = tags.get("barrier") == "kerb" and row["type"] != "node"
            if not (sidewalk or crossing or access or curb):
                continue
            raw = osm_geometry(row)
            if raw is None or raw.is_empty or not raw.is_valid:
                continue
            shape = transform(local, raw)
            if not filter_area.intersects(shape):
                continue
            identity = f"osm:{row['type']}/{row['id']}"
            width = metres(tags.get("width"))
            if curb and shape.geom_type == "LineString":
                kerbs[identity] = shape
            elif crossing or access:
                exclusions[identity] = shape.buffer((width or (3 if access else 4)) / 2)
            elif sidewalk:
                pedestrian[identity] = (
                    shape
                    if shape.area
                    else shape.buffer((width or 1.6) / 2, cap_style="flat"),
                    "MAPPED_GEOMETRY" if shape.area else "ESTIMATED_NOT_SURVEYED",
                )
    return pedestrian, exclusions, kerbs


def pedestrian_surfaces(
    roads, window, ground, masks, paths, mapped, kerbs, sidewalk_width, curb_width
):
    domain = window.intersection(ground)
    # The full parent road network stays in this mask, including junction mouths.
    safe = domain.difference(union_all([roads, *masks], grid_size=0.001))
    walking = {}
    for identity, (shape, confidence) in sorted(mapped.items()):
        piece = area_only(shape.intersection(safe))
        if piece.area >= 0.005:
            walking[identity] = piece, confidence
    inferred = area_only(
        safe.difference(paths)
        .intersection(roads.buffer(sidewalk_width))
        .difference(
            union_all([shape for shape, _ in walking.values()], grid_size=0.001)
        )
    )
    if inferred.area >= 0.005:
        walking["provisional-road-edge"] = inferred, "ESTIMATED_NOT_SURVEYED"
    combined = union_all([shape for shape, _ in walking.values()], grid_size=0.001)
    curb = {}
    for identity, line in sorted(kerbs.items()):
        piece = area_only(
            line.buffer(curb_width / 2, cap_style="flat").intersection(combined)
        )
        if piece.area >= 0.005:
            curb[identity] = piece
    inferred_curb = area_only(
        combined.intersection(roads.buffer(curb_width)).difference(
            union_all(list(curb.values()), grid_size=0.001)
        )
    )
    if inferred_curb.area >= 0.005:
        curb["provisional-road-edge"] = inferred_curb
    sidewalks = area_only(
        combined.difference(union_all(list(curb.values()), grid_size=0.001))
    )
    return sidewalks, walking, curb


def solid_faces(shape, bottom, top):
    """Triangulate planar tops/holes and cap each boundary including cuts."""
    faces = triangles(shape, top)
    polygons = [shape] if shape.geom_type == "Polygon" else shape.geoms
    for polygon in polygons:
        polygon = orient(polygon, sign=1)
        for ring in (polygon.exterior, *polygon.interiors):
            for a, b in zip(ring.coords, list(ring.coords)[1:]):
                if dist(a, b) < 1e-8:
                    continue
                a0, b0, a1, b1 = (*a, bottom), (*b, bottom), (*a, top), (*b, top)
                faces.extend(((a0, b0, b1), (a0, b1, a1)))
    return faces
