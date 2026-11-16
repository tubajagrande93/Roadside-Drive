import pytest
from shapely.geometry import LineString, Point, box

from roadside_drive.world.visual.route_slice import build_slice, station_window
from roadside_drive.world.visual.surfaces import pedestrian_surfaces


def test_station_window_cuts_both_ends_and_keeps_parallel_carriageway():
    route, segment = build_slice([(0, 0), (100, 0), (100, 200)], 0, 200)
    window = station_window(segment, 24)
    assert segment.length == pytest.approx(200)
    assert window.covers(Point(20, 12))
    assert window.covers(route.interpolate(200))
    assert not window.intersects(route.interpolate(250).buffer(1))
    assert not window.intersects(Point(-0.01, 0))
    with pytest.raises(ValueError, match="Duplicate"):
        build_slice([(0, 0), (0, 0), (400, 0)], 0, 200)


def test_curbs_and_fallback_sidewalks_avoid_crossing_and_existing_path():
    roads = box(0, -3, 200, 3)
    extent = box(0, -10, 200, 10)
    opening = box(90, 2, 96, 8)
    path = LineString([(120, 4), (140, 4)]).buffer(0.4)
    sidewalk, sources, curbs = pedestrian_surfaces(
        roads, extent, extent, [opening], path, {}, {}, 1.6, 0.16
    )
    assert sources["provisional-road-edge"][1] == "ESTIMATED_NOT_SURVEYED"
    assert sidewalk.covers(Point(50, 4))
    assert not sidewalk.intersects(Point(92, 4))
    assert not sidewalk.intersects(Point(130, 4))
    assert not curbs["provisional-road-edge"].intersects(Point(92, 3.1))
