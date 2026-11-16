import json
import shutil
import socket
from hashlib import sha256
from pathlib import Path

import pytest
from pyproj import Transformer

from roadside_drive.world.cli import main
from roadside_drive.world.contracts import (
    CorrectionPatch,
    Origin,
    Source,
    apply_corrections,
)
from roadside_drive.world.exports import build_fixture, validate_scene
from roadside_drive.world.osm_adapter import approved_query, proposal
from roadside_drive.world.projections import (
    meters_to_unreal,
    project_wgs84,
    unreal_to_meters,
)

REPO = Path(__file__).resolve().parents[2]
CONFIG = "configs/worlds/synthetic_pilot.json"
AOI = "configs/worlds/banja_luka_pilot.json"
FIXTURE = "tests/fixtures/world/mini_crossroads.json"
OUTPUT = "data/processed/world_builder"


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    for name in (CONFIG, FIXTURE, AOI):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / name, path)

    def deny(*args, **kwargs):
        raise AssertionError("Test attempted an external network request")

    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket.socket, "connect", deny)
    return tmp_path


@pytest.fixture
def raw(sandbox):
    return Source.model_validate_json((sandbox / FIXTURE).read_bytes())


def test_projection_metres_axis_and_negative_controls():
    point = project_wgs84((17.19, 44.77), "EPSG:32633")
    origin = Origin(east_m=point[0], north_m=point[1], z_m=0)
    arbitrary = (point[0] + 100, point[1] + 1, 3.0)
    engine = meters_to_unreal(arbitrary, origin)
    assert engine == (10000, 100, 300)
    assert unreal_to_meters(engine, origin) == pytest.approx(arbitrary, abs=0.02)
    inverse = Transformer.from_crs(32633, 4326, always_xy=True)
    assert inverse.transform(*point) == pytest.approx((17.19, 44.77), abs=1e-9)
    with pytest.raises(ValueError, match="area of use"):
        project_wgs84((44.77, 17.19), "EPSG:32633")
    with pytest.raises(ValueError, match="projected metres"):
        project_wgs84((17.19, 44.77), "EPSG:4326")
    with pytest.raises(ValueError, match="finite"):
        meters_to_unreal((float("nan"), 2, 3), origin)
    with pytest.raises(ValueError, match="local pilot"):
        unreal_to_meters((300_000_000, 5, 0), origin)


def test_deterministic_offline_package_and_known_geometry(sandbox):
    a = build_fixture(sandbox, CONFIG, f"{OUTPUT}/a")
    b = build_fixture(sandbox, CONFIG, f"{OUTPUT}/b")
    assert a == b and a.label == "SYNTHETIC — NOT BANJA LUKA"
    assert a.generated_object_counts == {"road": 2, "building": 3, "ground": 1}
    assert a.unreal_units_per_meter == 100
    assert a.import_status == "NOT_EXECUTED"
    assert validate_scene(sandbox / OUTPUT / "a/scene_manifest.json") == a
    assert build_fixture(sandbox, CONFIG, f"{OUTPUT}/a") == a
    east = next(item for item in a.objects if item.stable_id == "road-east-west")
    assert east.bounds_m[1][0] - east.bounds_m[0][0] == 100
    unmeasured = next(item for item in a.objects if item.stable_id == "building-002")
    assert unmeasured.confidence == "PLACEHOLDER" and unmeasured.visual_height_m == 6
    data = json.loads((sandbox / OUTPUT / "a/normalized.json").read_bytes())
    assert (
        next(b for b in data["buildings"] if b["stable_id"] == "building-002")[
            "height_m"
        ]
        is None
    )


def test_tampered_mesh_and_unmanaged_package_fail(sandbox):
    scene = build_fixture(sandbox, CONFIG, f"{OUTPUT}/model")
    folder = sandbox / OUTPUT / "model"
    f = folder / scene.objects[0].file
    f.write_bytes(f.read_bytes() + b"untracked data")
    with pytest.raises(ValueError, match="Mesh digest"):
        validate_scene(folder / "scene_manifest.json")
    (folder / "unmanaged.txt").write_text("keep")
    with pytest.raises(ValueError, match="unmanaged"):
        build_fixture(sandbox, CONFIG, f"{OUTPUT}/model")
    assert (folder / "unmanaged.txt").read_text() == "keep"


@pytest.mark.parametrize(
    "foothold", ["bad-footprint", "disconnected", "negative-width"]
)
def test_invalid_feature_stops_before_output(sandbox, foothold):
    path = sandbox / FIXTURE
    data = json.loads(path.read_text())
    if foothold == "bad-footprint":
        data["buildings"][0]["footprint_m"] = [[10, 10], [20, 20], [10, 20], [20, 10]]
    elif foothold == "disconnected":
        data["roads"][1]["centerline_m"] = [[100, 0], [100, 50]]
    else:
        data["roads"][0]["width_m"] = -1
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        build_fixture(sandbox, CONFIG, f"{OUTPUT}/negative")
    assert not (sandbox / OUTPUT / "negative").exists()


def test_reversible_correction_source_preservation_and_conflicts(sandbox, raw):
    initial = (sandbox / FIXTURE).read_bytes()
    source_hash = sha256(initial).hexdigest()
    road = raw.roads[0]
    data = {
        "schema_version": 1,
        "patch_id": "trial-width",
        "target_stable_id": road.stable_id,
        "expected_source_hash": road.source_hash(),
        "field": "width_m",
        "expected_previous_value": 8.0,
        "new_value": 10.0,
        "reason": "Synthetic user correction",
        "operator_created_utc": "2026-11-16T00:00:00Z",
        "author_ref": "fixture",
    }
    patches = sandbox / "patches.json"
    patches.write_text(json.dumps([data]))
    vanilla = build_fixture(sandbox, CONFIG, f"{OUTPUT}/vanilla")
    corrected = build_fixture(sandbox, CONFIG, f"{OUTPUT}/corrected", "patches.json")
    assert vanilla.source_sha256 == corrected.source_sha256 == source_hash
    assert corrected.normalized_sha256 != vanilla.normalized_sha256
    assert corrected.content_sha256 != vanilla.content_sha256
    assert (
        build_fixture(sandbox, CONFIG, f"{OUTPUT}/again", "patches.json") == corrected
    )
    assert build_fixture(sandbox, CONFIG, f"{OUTPUT}/rollback") == vanilla
    assert (sandbox / FIXTURE).read_bytes() == initial and road.width_m == 8
    patch = CorrectionPatch.model_validate(data)
    with pytest.raises(ValueError, match="Duplicate correction"):
        apply_corrections(raw, [patch, patch])
    for change, expected in (
        ({"expected_previous_value": 9}, "stale value"),
        ({"target_stable_id": "does-not-exist"}, "unknown target"),
        ({"expected_source_hash": "0" * 64}, "stale source hash"),
    ):
        with pytest.raises(ValueError, match=expected):
            apply_corrections(raw, [CorrectionPatch.model_validate({**data, **change})])


def test_output_traversal_and_symlink_rejected(sandbox):
    with pytest.raises(ValueError, match="relative"):
        build_fixture(sandbox, CONFIG, "../unrelated")
    with pytest.raises(ValueError, match="under data/processed"):
        build_fixture(sandbox, CONFIG, "unrelated")
    outside = sandbox / "outside"
    outside.mkdir()
    (sandbox / "data").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="Symlink"):
        build_fixture(sandbox, CONFIG, f"{OUTPUT}/escape")
    assert not list(outside.iterdir())


def test_osm_go_blocks_all_draft_network_paths(sandbox, monkeypatch, capsys):
    _, pending = proposal(sandbox, AOI)
    assert pending["status"] == "AOI_NOT_APPROVED"
    assert pending["network_requests"] == 0
    with pytest.raises(ValueError, match="OSM GO"):
        approved_query(sandbox, AOI, None, True)
    monkeypatch.chdir(sandbox)
    assert main(["ingest-osm", "--config", AOI, "--allow-network"]) == 2
    assert "OSM GO required" in capsys.readouterr().err
    assert not (sandbox / "data/raw").exists()


def test_cli_exports_a_sealed_copy(sandbox, monkeypatch, capsys):
    monkeypatch.chdir(sandbox)
    build_fixture(sandbox, CONFIG, f"{OUTPUT}/before")
    assert (
        main(
            [
                "export",
                "--scene",
                f"{OUTPUT}/before/scene_manifest.json",
                "--output",
                f"{OUTPUT}/after",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["status"] == "PASS"


def test_osm_identity_parallel_edges_and_unknown_height_are_stable(sandbox):
    import networkx as nx

    from roadside_drive.world.contracts import Provenance
    from roadside_drive.world.normalize import normalize_osm

    extent = [(17.186, 44.766), (17.198, 44.766), (17.198, 44.776), (17.186, 44.776)]
    points = [(17.190, 44.770), (17.194, 44.772)]
    from shapely.geometry import LineString

    roads = [
        {
            "osmid": [2, 1],
            "width": "6 m",
            "geometry": LineString(points),
            "oneway": True,
        },
        {
            "osmid": [1, 2],
            "geometry": LineString([points[0], (17.191, 44.773), points[1]]),
        },
    ]
    output = []
    building = {
        "properties": {"element": "way", "id": 40, "building": "yes"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    (17.195, 44.773),
                    (17.196, 44.773),
                    (17.196, 44.774),
                    (17.195, 44.773),
                ]
            ],
        },
    }
    evidence = Provenance(
        title="Synthetic OSM-shaped test",
        dataset_kind="OSM",
        source_uri="LOCAL_TEST",
        license_id="PROJECT_TEST_DATA",
        attribution="Test",
        derivative_status="SYNTHETIC",
    )
    for ordering in (roads, list(reversed(roads))):
        graph = nx.MultiDiGraph()
        for n, (x, y) in enumerate(points):
            graph.add_node(n, x=x, y=y)
        for attributes in ordering:
            graph.add_edge(0, 1, **attributes)
        output.append(
            normalize_osm(
                graph,
                [building],
                crs="EPSG:32633",
                aoi=extent,
                query_sha="a" * 64,
                provenance=evidence,
            )
        )
    assert output[0] == output[1]
    assert len({road.stable_id for road in output[0].roads}) == 2
    assert {road.width_m for road in output[0].roads} == {6, 7}
    assert all(road.source_elements == ("way/1", "way/2") for road in output[0].roads)
    assert output[0].buildings[0].height_m is None
