"""Explicit geographic, metric and Unreal coordinate boundaries."""

from math import isfinite

from pyproj import CRS, Transformer

from .orientation import CM_PER_METRE, local_to_ue_cm

MAX_PILOT_OFFSET_M = 10_000


def projected_crs(value):
    crs = CRS.from_user_input(value)
    if not crs.is_projected or any(
        axis.unit_conversion_factor != 1 for axis in crs.axis_info[:2]
    ):
        raise ValueError("The working CRS must use projected metres")
    return crs


def project_wgs84(point, target):
    lon, lat = point
    crs = projected_crs(target)
    if crs.area_of_use is None:
        raise ValueError("Projected CRS needs a verified area of use")
    west, south, east, north = crs.area_of_use.bounds
    if not (west <= lon <= east and south <= lat <= north):
        raise ValueError("Longitude/latitude outside CRS area of use")
    return Transformer.from_crs(4326, crs, always_xy=True).transform(
        lon, lat, errcheck=True
    )


def meters_to_unreal(point, origin):
    local = (point[0] - origin.east_m, point[1] - origin.north_m, point[2] - origin.z_m)
    if any(not isfinite(axis) or abs(axis) > MAX_PILOT_OFFSET_M for axis in local):
        raise ValueError("Point outside finite local pilot envelope")
    return local_to_ue_cm(local)


def unreal_to_meters(point, origin):
    if any(
        not isfinite(axis) or abs(axis) > MAX_PILOT_OFFSET_M * CM_PER_METRE
        for axis in point
    ):
        raise ValueError("Unreal transform outside local pilot envelope")
    return (
        point[0] / CM_PER_METRE + origin.east_m,
        origin.north_m - point[1] / CM_PER_METRE,
        point[2] / CM_PER_METRE + origin.z_m,
    )
