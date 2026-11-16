from types import SimpleNamespace

import pytest
from shapely.geometry import LineString, Point, Polygon, box

from roadside_drive.world.harvest.features import Feature, height_evidence, osm_geometry
from roadside_drive.world.harvest.fusion import associate, station
from roadside_drive.world.harvest.massing import polygon_shell, surface_faces


def test_station_side_uses_direction_not_compass():
    east = SimpleNamespace(route=LineString([(0, 0), (230, 0)]))
    west = SimpleNamespace(route=LineString([(230, 0), (0, 0)]))
    assert station(east, Point(109, 12)) == {
        "station": 1,
        "side": "LEFT",
        "along_m": 109.0,
        "offset_m": 12.0,
        "priority": "P0",
    }
    assert station(west, Point(109, 12))["side"] == "RIGHT"
    assert station(east, Point(230, 140))["station"] == 2


def test_conflict_and_footprint_fusion():
    outline = box(0, 0, 10, 10)
    osm = Feature("osm:way/1", outline, {"building": "yes"}, "OSM", "a", None)
    duplicate = Feature(
        "overture:1", box(0.2, 0, 10, 10), {"building": "yes"}, "OVERTURE", "b", None
    )
    review = Feature(
        "overture:2", box(5, 3, 14, 10), {"building": "yes"}, "OVERTURE", "c", None
    )
    distant = Feature(
        "overture:3", box(40, 40, 50, 50), {"building": "yes"}, "OVERTURE", "d", None
    )
    _, linked, other, conflicts = associate([osm], [distant, duplicate, review])
    assert linked[osm.identity][0] == duplicate
    assert other == [distant]
    assert conflicts[0][:2] == (osm.identity, review.identity)


def test_building_surface_retains_holes_and_tagged_gable():
    base = Polygon(box(0, 0, 10, 10).exterior.coords, [box(3, 3, 6, 6).exterior.coords])
    mesh, shaped = polygon_shell(base, 8)
    roofs = [f for f in mesh if all(v[2] == 8 for v in f)]
    assert not shaped
    assert sum(Polygon([(x, y) for x, y, _ in f]).area for f in roofs) == pytest.approx(
        91
    )
    gable, shaped = polygon_shell(box(0, 0, 10, 10), 8, "gabled", 2)
    assert shaped
    assert {z for f in gable for *_, z in f} == {0, 6, 8}


def test_height_evidence_is_never_claimed_measured():
    assert height_evidence(
        {"height": "14 m", "building:levels": "3"}, {"height": 13}
    ) == (14, "OSM_HEIGHT_TAG", "ESTIMATED")
    assert height_evidence({"building:levels": "3"}, {"height": 13}) == (
        13,
        "OVERTURE_NUMERIC_HEIGHT",
        "ESTIMATED",
    )
    assert height_evidence({}, {}) == (7, "PLACEHOLDER_7_M", "PLACEHOLDER")


def test_osm_relation_assembles_courtyard():
    def coords(points):
        return [{"lon": x, "lat": y} for x, y in points]

    value = osm_geometry(
        {
            "type": "relation",
            "members": [
                {
                    "role": "outer",
                    "geometry": coords(box(0, 0, 10, 10).exterior.coords),
                },
                {"role": "inner", "geometry": coords(box(3, 3, 6, 6).exterior.coords)},
            ],
        }
    )
    assert value.area == 91
    assert not value.covers(Point(4, 4))


def test_rendered_paths_are_clipped_at_context_ground_edge():
    footprint = box(0, 0, 10, 10)
    path = LineString([(3, 4), (25, 6)]).buffer(0.75)
    faces = surface_faces(path, footprint, -0.02)
    assert faces
    assert max(x for face in faces for x, _, _ in face) == pytest.approx(10)
