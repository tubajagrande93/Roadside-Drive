"""Gate 03 scope derived from the approved Gate 02 route."""

from dataclasses import dataclass

from pyproj import Transformer
from shapely import transform
from shapely.geometry import Polygon, box, shape

from ..corridor_scene import verify_route
from ..normalize import read_capture

VISIBLE_M = 125
HARVEST_M = 225
STATION_M = 100


@dataclass(frozen=True)
class Scope:
    report: dict
    candidate: dict
    route: object
    boundary: object
    tiles: tuple
    project: object
    inverse: object
    base_capture: object


def approved_scope(root, capture, review, approval):
    captured = read_capture(root, capture)
    report, candidate, accepted = verify_route(
        root, captured, review, "directed-shortest", approval
    )
    if accepted is None:
        raise ValueError("Gate 03 requires the approved Gate 02 directed route")
    project = Transformer.from_crs(4326, 32633, always_xy=True).transform
    inverse = Transformer.from_crs(32633, 4326, always_xy=True).transform
    route = transform(shape(candidate["geometry"]), project, interleaved=False)
    approved_polygon = transform(
        Polygon(captured.manifest["polygon_wgs84"]), project, interleaved=False
    )
    boundary = route.buffer(HARVEST_M).intersection(approved_polygon)
    if boundary.geom_type != "Polygon" or not boundary.covers(route):
        raise ValueError("Harvest coverage cannot leave the approved corridor")
    west, south, east, north = boundary.bounds
    step = (north - south) / 4
    tiles = tuple(
        transform(
            boundary.intersection(
                box(west, south + i * step, east, south + (i + 1) * step)
            ),
            inverse,
            interleaved=False,
        )
        for i in range(4)
    )
    return Scope(report, candidate, route, boundary, tiles, project, inverse, captured)
