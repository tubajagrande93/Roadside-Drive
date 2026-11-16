"""Focused coverage of the Gate 02 boundary without live Overpass or Unreal."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import networkx as nx
import pytest

from roadside_drive.world.contracts import canonical
from roadside_drive.world.corridor_route import on_main_axis, review_route
from roadside_drive.world.corridor_scene import WidthPolicy, verify_route, width_for
from roadside_drive.world.osm_adapter import G02_ANCHORS, approved_query, proposal

CONFIG = Path("configs/worlds/banja_luka_gate02.json")


def test_exact_polygon_fingerprint_and_live_guard(tmp_path):
    _, request = proposal(Path.cwd(), CONFIG)
    assert request["network_requests"] == 0
    assert request["status"] == "OSM_GO_REQUIRED"
    assert set(request["overpass_ql"]) == {"roads", "buildings"}
    first_lon, first_lat = request["polygon_wgs84"][0]
    expected_prefix = f'(poly:"{first_lat:.12f} {first_lon:.12f} '
    assert all(
        expected_prefix in query and "[out:xml]" in query
        for query in request["overpass_ql"].values()
    )
    assert request["centerline_wgs84"] == G02_ANCHORS
    with pytest.raises(ValueError, match="OSM GO required"):
        approved_query(Path.cwd(), CONFIG, None, False)
    config = json.loads(CONFIG.read_bytes())
    config["polygon_wgs84"][5][0] += 0.04
    (tmp_path / CONFIG.name).write_bytes(canonical(config))
    with pytest.raises(ValueError, match="approved bounded-query envelope|authorized"):
        proposal(tmp_path, CONFIG.name)


def capture_fixture():
    graph = nx.MultiDiGraph()
    for i, (x, y) in enumerate((*G02_ANCHORS, (17.194, 44.7765))):
        graph.add_node(i, x=x, y=y)
    graph.add_edge(
        0, 2, length=1050, osmid=14, name="Dr Mladena Stojanovića", oneway=True
    )
    graph.add_edge(
        2, 1, length=1100, osmid=15, name="Краља Петра I Карађорђевића", oneway=True
    )
    manifest = {
        "scope": "banja-luka-g02",
        "projected_crs_candidate": "EPSG:32633",
        "polygon_wgs84": [
            [17.18, 44.76],
            [17.21, 44.76],
            [17.21, 44.79],
            [17.18, 44.79],
            [17.18, 44.76],
        ],
        "centerline_wgs84": G02_ANCHORS,
        "artifacts_sha256": {"graph.graphml": "0" * 64},
        "query_sha256": "1" * 64,
    }
    return SimpleNamespace(graph=graph, manifest=manifest)


def test_route_is_directed_and_approval_binds_exact_revision(tmp_path):
    capture = capture_fixture()
    review = review_route(capture)
    assert review["status"] == "ROUTE_REVIEW_REQUIRED"
    assert {i["id"] for i in review["candidates"]} == {
        "directed-shortest",
        "named-axis",
    }
    travel = review["candidates"][0]
    assert [row["way"] for row in travel["edges"]] == [14, 15]
    assert travel["snap"]["start"]["offset_m"] == travel["snap"]["end"]["offset_m"] == 0
    (tmp_path / "review.json").write_bytes(canonical(review))
    assert (
        verify_route(tmp_path, capture, "review.json", "directed-shortest", None)[2]
        is None
    )
    approval = tmp_path / "data/raw/world_builder/approvals/route.json"
    approval.parent.mkdir(parents=True)
    approval.write_bytes(
        canonical(
            {
                "operator_decision": "ACCEPT_ROUTE",
                "operator_reference": "test fixture",
                "recorded_utc": "2026-11-16T00:00:00Z",
                "review_sha256": "2" * 64,
                "graph_sha256": review["graph_sha256"],
                "candidate_id": "directed-shortest",
            }
        )
    )
    with pytest.raises(ValueError, match="does not match this exact review"):
        verify_route(
            tmp_path,
            capture,
            "review.json",
            "directed-shortest",
            approval.relative_to(tmp_path),
        )
    capture.graph.remove_edge(2, 1)
    with pytest.raises(ValueError, match="No reviewable route"):
        review_route(capture)


def test_width_priority_and_missing_width_confidence():
    policy = WidthPolicy(
        lane_width_m=3.2, class_width_m={"primary": 12.0, "default": 8.0}
    )
    assert width_for({"width": "7.5 m", "lanes": "3"}, policy) == (
        7.5,
        "OSM_WIDTH_TAG_UNVERIFIED",
        "ESTIMATED",
        3,
    )
    assert width_for({"width": "bad", "lanes": "2"}, policy) == (
        6.4,
        "OSM_LANES_TIMES_ESTIMATED_LANE_WIDTH",
        "ESTIMATED",
        2,
    )
    assert width_for({"highway": "primary"}, policy) == (
        12.0,
        "ROAD_CLASS_PLACEHOLDER",
        "PLACEHOLDER",
        None,
    )


def test_main_axis_matches_latin_and_cyrillic_osm_tags():
    assert all(
        on_main_axis({"name": label})
        for label in (
            "Dr Mladena Stojanovića",
            "Kralja Petra I Karađorđevića",
            "Краља Петра I Карађорђевића",
        )
    )
