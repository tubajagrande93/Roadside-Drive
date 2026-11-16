"""Approval-first, bounded OSM capture. Drafts and fixture builds are offline."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Literal

from pydantic import Field
from shapely.geometry import LineString, Polygon

from .bounded_overpass import capture_polygon, polygon_queries
from .contracts import XY, Contract, Digest, canonical, digest
from .exports import confined
from .projections import project_wgs84

G02_ANCHORS = ((17.203654, 44.784419), (17.187776, 44.768741))

ENDPOINT = "https://overpass-api.de/api"
ATTRIBUTION = "© OpenStreetMap contributors — https://www.openstreetmap.org/copyright"


class Pilot(Contract):
    title: str
    candidate_corridor: str
    source_crs: str
    projected_crs_candidate: str
    intended_centerline_length_m: tuple[int, int]
    centerline_wgs84: tuple[XY, ...] | None
    polygon_wgs84: tuple[XY, ...] | None
    scope: Literal["gate01", "banja-luka-g02"] = "gate01"


class Approval(Contract):
    operator_decision: str
    approved_utc: datetime
    query_sha256: Digest
    approved_source: str
    approved_license: str
    operator_reference: str = Field(min_length=1)


def proposal(root, config):
    pilot = Pilot.model_validate_json(confined(root, config).read_bytes())
    gate02 = pilot.scope == "banja-luka-g02"
    limits = (2000, 4000) if gate02 else (500, 1000)
    if pilot.source_crs != "EPSG:4326" or pilot.intended_centerline_length_m != limits:
        raise ValueError("Unexpected pilot source CRS or authorized length envelope")
    pending = pilot.centerline_wgs84 is None or pilot.polygon_wgs84 is None
    region = {
        "source_crs": pilot.source_crs,
        "projected_crs_candidate": pilot.projected_crs_candidate,
        "centerline_wgs84": pilot.centerline_wgs84,
        "polygon_wgs84": pilot.polygon_wgs84,
        "source": ENDPOINT,
        "license": "ODbL-1.0",
        "attribution": ATTRIBUTION,
        "queries": {"roads": "drive", "buildings": {"building": True}},
    }
    if not pending:
        validate_bounds(pilot)
        if gate02:
            region["scope"] = pilot.scope
            region["overpass_ql"] = polygon_queries(pilot.polygon_wgs84)
    return pilot, {
        **region,
        "title": pilot.title,
        "candidate_corridor": pilot.candidate_corridor,
        "query_sha256": digest(canonical(region)),
        "status": "AOI_NOT_APPROVED" if pending else "OSM_GO_REQUIRED",
        "network_requests": 0,
    }


def validate_bounds(pilot):
    gate02 = pilot.scope == "banja-luka-g02"
    if gate02 and (
        pilot.centerline_wgs84 != G02_ANCHORS
        or pilot.projected_crs_candidate != "EPSG:32633"
    ):
        raise ValueError(
            "Gate 02 requires the authorized Banja Luka anchor identity and projection"
        )
    if not (
        2 <= len(pilot.centerline_wgs84) <= 64
        and 4 <= len(pilot.polygon_wgs84) <= (128 if gate02 else 64)
        and pilot.polygon_wgs84[0] == pilot.polygon_wgs84[-1]
    ):
        raise ValueError("Pilot requires a bounded line and closed polygon")
    line = LineString(
        [
            project_wgs84(p, pilot.projected_crs_candidate)
            for p in pilot.centerline_wgs84
        ]
    )
    area = Polygon(
        [project_wgs84(p, pilot.projected_crs_candidate) for p in pilot.polygon_wgs84]
    )
    min_length, max_length = pilot.intended_centerline_length_m
    if (
        not line.is_simple
        or not min_length <= line.length <= max_length
        or not area.is_valid
        or not 0 < area.area <= (4_000_000 if gate02 else 500_000)
        or not area.covers(line)
    ):
        raise ValueError("Pilot lies outside its approved bounded-query envelope")
    west, south, east, north = area.bounds
    if gate02 and not line.buffer(350.01, quad_segs=24).covers(area):
        raise ValueError("Gate 02 AOI extends beyond the authorized 350 m buffer")
    if max(east - west, north - south) > (3000 if gate02 else 1500):
        raise ValueError("AOI span exceeds the bounded pilot")


def approved_query(root, config, approval_path, allow_network):
    if not allow_network or not approval_path:
        raise ValueError(
            "OSM GO required: explicit --allow-network and --approval are both mandatory"
        )
    pilot, request = proposal(root, config)
    if request["status"] != "OSM_GO_REQUIRED":
        raise ValueError(
            "OSM GO required: the pilot polygon and centerline are unresolved"
        )
    approval_file = confined(root, approval_path)
    approval_root = confined(root, "data/raw/world_builder/approvals")
    if approval_root not in approval_file.parents:
        raise ValueError(
            "OSM GO approval must use a local record in data/raw/world_builder/approvals"
        )
    approval = Approval.model_validate_json(approval_file.read_bytes())
    if (
        approval.operator_decision != "OSM GO"
        or approval.approved_utc.utcoffset() is None
        or approval.approved_utc > datetime.now(UTC)
        or approval.query_sha256 != request["query_sha256"]
        or approval.approved_source != ENDPOINT
        or approval.approved_license != "ODbL-1.0"
    ):
        raise ValueError("OSM GO approval does not match this exact query and source")
    return pilot, request, approval


def ingest_osm(root, config, approval_path, allow_network):
    pilot, request, approval = approved_query(
        root, config, approval_path, allow_network
    )
    if (
        not (root / ".git").exists()
        or not (root / "apps/unreal/RoadsideDrive/RoadsideDrive.uproject").is_file()
    ):
        raise ValueError("Capture must run at the Roadside Drive repository root")
    raw = confined(root, "data/raw/world_builder/snapshots")
    output = raw / request["query_sha256"]
    if output.is_symlink() or output.exists():
        raise ValueError(
            "Snapshot already exists. Preserve it and review before any new capture."
        )
    # Reserve the output before invoking the upstream library. Failed captures remain visibly
    # incomplete and prevent automatic retries over already acquired raw evidence.
    output.mkdir(parents=True, exist_ok=False)
    (output / "request.json").write_bytes(
        canonical({**request, "status": "CAPTURE_IN_PROGRESS"})
    )
    import osmnx as ox

    ox.settings.overpass_url = ENDPOINT
    ox.settings.use_cache = True
    ox.settings.cache_folder = output / "responses"
    ox.settings.requests_timeout = 30
    ox.settings.all_oneway = False
    source_dates = {}
    if pilot.scope == "banja-luka-g02":
        ox.settings.useful_tags_way = sorted(
            set(ox.settings.useful_tags_way)
            | {"width", "surface", "layer", "junction", "access"}
        )
        graph, buildings, source_dates = capture_polygon(ox, request, output)
    else:
        polygon = Polygon(pilot.polygon_wgs84)
        graph = ox.graph.graph_from_polygon(
            polygon, network_type="drive", simplify=False, retain_all=True
        )
        buildings = ox.features.features_from_polygon(polygon, {"building": True})
    ox.io.save_graphml(graph, filepath=output / "graph.graphml")
    (output / "buildings.geojson").write_text(
        buildings.reset_index().to_json(), encoding="utf-8"
    )
    files = {
        p.relative_to(output).as_posix(): digest(p.read_bytes())
        for p in output.rglob("*")
        if p.is_file()
    }
    status = {
        **request,
        "status": "CAPTURED_REQUIRES_QA",
        "fetched_utc": datetime.now(UTC).isoformat(),
        "approved_utc": approval.approved_utc.isoformat(),
        "counts": {
            "road_nodes": len(graph.nodes),
            "road_edges": len(graph.edges),
            "building_features": len(buildings),
        },
        "osm_source_dates": source_dates,
        "artifacts_sha256": files,
        "derivative_status": "SOURCE_CAPTURE",
    }
    # Preserve the exact offline proposal's zero-query count only in request.json.
    status.pop("network_requests")
    part = output / ".capture.tmp"
    part.write_bytes(canonical(status))
    os.replace(part, output / "capture_manifest.json")
    return {
        "status": status["status"],
        "location": output.relative_to(root).as_posix(),
        "counts": status["counts"],
    }
