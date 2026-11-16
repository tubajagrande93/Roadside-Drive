"""Directed chainage measured against the accepted local metric road."""

from itertools import pairwise
from math import dist, isfinite

from shapely.geometry import LineString, Polygon
from shapely.ops import substring

from ..orientation import start_yaw_deg

STATIONS = (0, 100, 200, 250)


def build_slice(points, start, end):
    if any(len(p) != 2 or not all(isfinite(v) for v in p) for p in points):
        raise ValueError("Route coordinates must be finite ENU pairs")
    if any(dist(a, b) <= 1e-9 for a, b in pairwise(points)):
        raise ValueError("Duplicate route vertices")
    route = LineString(points)
    if not route.is_simple or not 0 <= start < end < route.length:
        raise ValueError("Invalid route or station bounds")
    segment = substring(route, start, end)
    if abs(segment.length - (end - start)) > 0.01:
        raise ValueError("Clipped route length differs from the station interval")
    return route, segment


def station_window(segment, half_width):
    """Flat station gates and a lateral bound for associated junction pieces."""
    window = segment.buffer(half_width, cap_style="flat")
    coordinates = list(segment.coords)
    limit = segment.length + 4 * half_width
    for a, b in ((coordinates[0], coordinates[1]), (coordinates[-1], coordinates[-2])):
        magnitude = dist(a, b)
        dx, dy = ((b[0] - a[0]) / magnitude, (b[1] - a[1]) / magnitude)
        x, y = a
        half_plane = Polygon(
            [
                (x + s * dx - t * dy, y + s * dy + t * dx)
                for s, t in ((0, -limit), (limit, -limit), (limit, limit), (0, limit))
            ]
        )
        window = window.intersection(half_plane)
    return window


def camera_stations(route):
    result = {}
    for station in STATIONS:
        point = route.interpolate(station)
        # The same orientation owner that establishes the approved START yaw.
        probe = substring(route, station, route.length)
        result[str(station)] = {
            "local_m": [point.x, point.y],
            "yaw_deg": start_yaw_deg(list(probe.coords)),
        }
    return result
