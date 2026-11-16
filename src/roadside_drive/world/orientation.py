"""Pure coordinate boundary shared by the data builder and embedded Unreal Python."""

import math

LEGACY_EXCHANGE = "glTF metres: X east, Y up, Z north"
GEOGRAPHIC_EXCHANGE = "glTF metres: X east, Y up, Z south"
CM_PER_METRE = 100


def local_to_gltf(local_m, exchange):
    east, north, up = local_m
    return east, up, -north if exchange == GEOGRAPHIC_EXCHANGE else north


def local_to_ue_cm(local_m):
    east, north, up = local_m
    return east * CM_PER_METRE, -north * CM_PER_METRE, up * CM_PER_METRE


def ue_bounds_cm(bounds, exchange):
    (west, south, bottom), (east, north, top) = bounds
    if exchange == GEOGRAPHIC_EXCHANGE:
        return local_to_ue_cm((west, north, bottom)), local_to_ue_cm((east, south, top))
    return tuple(tuple(axis * CM_PER_METRE for axis in row) for row in bounds)


def gltf_bounds_m(bounds, exchange):
    (west, south, bottom), (east, north, top) = bounds
    if exchange == GEOGRAPHIC_EXCHANGE:
        return (west, bottom, -north), (east, top, -south)
    return (west, bottom, south), (east, top, north)


def start_yaw_deg(route_local_m):
    """Aim the initial camera along the first approximately 20 m of the route."""
    start_east, start_north = route_local_m[0]
    for east, north in route_local_m[1:]:
        dx, dy = east - start_east, start_north - north
        if math.hypot(dx, dy) >= 20:
            return math.degrees(math.atan2(dy, dx))
    raise ValueError("No usable initial corridor heading")


def camera_right_m(forward, point_offset):
    """Project an Unreal XY displacement onto the viewer's right axis."""
    x, y = forward
    east, south = point_offset
    return (-y * east + x * south) / math.hypot(x, y)
