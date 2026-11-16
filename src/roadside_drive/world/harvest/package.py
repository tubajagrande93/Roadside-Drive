"""Add environment meshes to a sealed Gate 02 package without changing its road."""

from __future__ import annotations

import csv
import json
import os
import shutil
import tempfile
from collections import Counter

import numpy as np
from shapely import normalize
from shapely.geometry import Polygon

from ..contracts import ObjectRecord, SceneManifest, canonical, digest
from ..exports import (
    G03_LABEL,
    confined,
    fresh_generated_path,
    glb,
    reframe_legacy_glb,
    validate_scene,
)
from ..normalize import stable_id
from ..orientation import GEOGRAPHIC_EXCHANGE, LEGACY_EXCHANGE
from .features import baseline_footprints, normalize_harvest, numeric_height
from .fusion import baseline_osm, inventory, station
from .massing import (
    local,
    parks,
    polygon_parts,
    polygon_shell,
    street_meshes,
    surroundings,
)


def keep_road_frame(base, scope, route):
    local_route = route["route_local_m"]
    if (
        route["graph_sha256"] != scope.report["graph_sha256"]
        or route["route_review_sha256"] != scope.report["content_sha256"]
        or route["route_status"] != "OPERATOR_ACCEPTED"
        or len(local_route) != len(scope.route.coords)
    ):
        raise ValueError(
            "Base scene must bind the exact approved Gate 02 graph and geometry"
        )
    for (x, y), (lx, ly) in zip(scope.route.coords, local_route, strict=True):
        if (
            abs(x - base.origin.east_m - lx) > 1e-5
            or abs(y - base.origin.north_m - ly) > 1e-5
        ):
            raise ValueError("Gate 03 would move the base route frame")


def make_record(
    folder,
    identifier,
    kind,
    faces,
    sources,
    basis=None,
    confidence="PLACEHOLDER",
    height=None,
):
    mesh = glb(faces, kind, GEOGRAPHIC_EXCHANGE)
    relative = f"meshes/{digest(identifier.encode())}.glb"
    (folder / relative).write_bytes(mesh)
    verts = np.asarray(faces).reshape(-1, 3)
    return ObjectRecord(
        stable_id=identifier,
        kind=kind,
        source_elements=tuple(sources),
        source_hash=digest(canonical([identifier, list(sources), basis])),
        file=relative,
        sha256=digest(mesh),
        face_count=len(faces),
        bounds_m=(verts.min(axis=0).tolist(), verts.max(axis=0).tolist()),
        material_category=f"g03_{kind}",
        confidence=confidence,
        height_basis=basis,
        visual_height_m=height,
    )


def enrich(root, scope, base_path, osm_path, overture_path, output):
    previous = confined(root, base_path)
    base = validate_scene(previous)
    normal = json.loads((previous.parent / "normalized.json").read_bytes())
    evidence = json.loads((previous.parent / "validation.json").read_bytes())
    route = evidence["corridor"]
    keep_road_frame(base, scope, route)
    osm, osm_skips = normalize_harvest(root, osm_path, scope, "OSM")
    overture, over_skips = normalize_harvest(root, overture_path, scope, "OVERTURE")
    sources, rows, cells, review = inventory(
        scope,
        osm,
        overture,
        [*baseline_footprints(scope), *baseline_osm(normal, base.source_sha256)],
    )
    dest = fresh_generated_path(root, output)
    if dest.exists():
        raise ValueError("Use a new Gate 03 output directory")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".g03-", dir=dest.parent) as scratch:
        work = confined(root, output).parent / os.path.basename(scratch)
        package = work / "scene"
        package.mkdir()
        (package / "meshes").mkdir()
        objects = {record.stable_id: record for record in base.objects}
        for record in base.objects:
            original = previous.parent / record.file
            output_file = package / record.file
            if base.exchange_coordinates == LEGACY_EXCHANGE:
                reframed = reframe_legacy_glb(original.read_bytes())
                output_file.write_bytes(reframed)
                objects[record.stable_id] = record.model_copy(
                    update={"sha256": digest(reframed)}
                )
            else:
                shutil.copyfile(original, output_file)
        protected = base.patch_set_sha256 != digest(canonical([]))
        displayed = set()
        existing = set(objects)
        existing_sources = {
            "osm:" + source
            for item in base.objects
            if item.kind == "building"
            for source in item.source_elements
        }
        labels = {}
        centers = dict(route["object_source_centers_wgs84"])
        for item, row in zip(sources, rows, strict=True):
            if not item.geometry.intersects(scope.route.buffer(125)):
                continue
            if item.geometry.distance(scope.route) < 0.50:
                row["visualization_status"] = "OVERLAPS_ROUTE_REVIEW"
                continue
            parts = sorted(
                polygon_parts(item.geometry), key=lambda part: normalize(part).wkb
            )
            for i, polygon in enumerate(parts):
                identifier = stable_id(
                    "building", [item.identity.removeprefix("osm:"), i]
                )
                if item.identity.startswith("osm:"):
                    element, number = item.identity.removeprefix("osm:").split("/")
                    identifier = stable_id("building", [f"{element}/{number}", i])
                old = objects.get(identifier)
                if (old and protected) or (
                    item.identity in existing_sources and not old
                ):
                    row["visualization_status"] = "BASE_FEATURE_PRESERVED"
                    continue
                if old:
                    source = next(
                        entry
                        for entry in normal["buildings"]
                        if entry["stable_id"] == identifier
                    )
                    polygon = Polygon(source["footprint_m"])
                shape = local(polygon, base.origin)
                if shape.geom_type != "Polygon" or shape.area < 6:
                    continue
                mh = row["height_m"]
                rise = numeric_height(row["roof_height_raw"])
                faces, roof = polygon_shell(
                    shape,
                    mh,
                    row["roof_shape"],
                    rise if rise and rise < mh / 2 else None,
                )
                ids = [item.identity.removeprefix("osm:")]
                if row["overture_id"]:
                    ids.append(row["overture_id"])
                candidate = make_record(
                    package,
                    identifier,
                    "building",
                    faces,
                    ids,
                    row["height_basis"],
                    row["confidence"],
                    mh,
                )
                if old:
                    candidate = candidate.model_copy(
                        update={"source_hash": old.source_hash}
                    )
                objects[identifier] = candidate
                center = polygon.representative_point()
                centers[identifier] = scope.inverse(center.x, center.y)
                row.update(
                    visualization_status="MESHED",
                    object_id=identifier,
                    generated_mesh_hash=candidate.sha256,
                    roof_visualization="TAGGED_GABLE" if roof else "PROVISIONAL_FLAT",
                )
                if row["name"]:
                    labels[identifier] = row["name"]
                displayed.add(identifier)
        extras = [
            *parks(scope, osm, base.origin),
            *street_meshes(scope, osm, base.origin, station),
        ]
        extras.append(
            (
                "g03:context",
                "context",
                surroundings(scope, base.origin),
                ["provisional:ground-context"],
                "Wider provisional ground",
            )
        )
        for identifier, kind, faces, refs, name in extras:
            stable = stable_id(kind, [identifier])
            objects[stable] = make_record(package, stable, kind, faces, refs)
            labels[stable] = name
        selected = [
            {
                "source_id": item.identity,
                "name": item.attributes.get("name"),
                "station": station(scope, item.geometry),
                "source_sha256": item.sha,
            }
            for item in osm
            if item.attributes.get("name")
            and (
                item.attributes.get("leisure") == "park"
                or item.attributes.get("shop") == "mall"
                or item.attributes.get("amenity") == "place_of_worship"
                or item.attributes.get("junction") == "roundabout"
            )
        ]
        named_positions = {}
        for landmark in selected:
            feature = next(
                item for item in osm if item.identity == landmark["source_id"]
            )
            point = feature.geometry.representative_point()
            named_positions[landmark["name"]] = [
                point.x - base.origin.east_m,
                point.y - base.origin.north_m,
            ]
        for row in rows:
            row.setdefault("visualization_status", "P1_OR_OUTSIDE_RENDER_BAND")
        summary = {
            "osm_normalized": len(osm),
            "overture_normalized": len(overture),
            "osm_skips": osm_skips,
            "overture_skips": over_skips,
            "candidate_buildings": len(rows),
            "overture_links": sum(row["overture_id"] is not None for row in rows),
            "ambiguous_footprints": len(review),
            "new_or_refined_buildings": len(displayed),
            "preserved_base_object_count": len(existing),
            "height_bases": dict(Counter(row["height_basis"] for row in rows)),
            "landmarks": selected,
            "labels": labels,
            "landmark_positions_local_m": named_positions,
            "environment_sources": len(extras),
            "station_cells": len(cells),
        }
        evidence["corridor"]["object_source_centers_wgs84"] = centers
        write_package(package, base, evidence, normal, objects, summary)
        validate_scene(package / "scene_manifest.json")
        with (work / "frontage_inventory.csv").open(
            "w", newline="", encoding="utf-8"
        ) as stream:
            writer = csv.DictWriter(
                stream, fieldnames=sorted({key for row in rows for key in row})
            )
            writer.writeheader()
            writer.writerows(rows)
        details = []
        for item in sorted([*osm, *overture], key=lambda entry: entry.identity):
            tags = item.attributes
            detail = next(
                (
                    f"{key}={tags[key]}"
                    for key in (
                        "building:part",
                        "building",
                        "leisure",
                        "natural",
                        "junction",
                        "highway",
                        "barrier",
                        "amenity",
                        "shop",
                        "historic",
                        "tourism",
                    )
                    if key in tags
                ),
                "place_or_other",
            )
            details.append(
                {
                    "source_id": item.identity,
                    "provider": item.source,
                    "source_sha256": item.sha,
                    "source_vintage": item.vintage,
                    "category": detail,
                    "name": tags.get("name"),
                    **station(scope, item.geometry),
                }
            )
        with (work / "frontage_objects.csv").open(
            "w", newline="", encoding="utf-8"
        ) as stream:
            writer = csv.DictWriter(stream, fieldnames=list(details[0]))
            writer.writeheader()
            writer.writerows(details)
        height_review = []
        for row in rows:
            osm_height = numeric_height(row["height_osm_raw"])
            overture_height = numeric_height(row["height_overture_raw"])
            if (
                osm_height
                and overture_height
                and abs(osm_height - overture_height) > max(3, osm_height * 0.2)
            ):
                height_review.append(row["source_id"])
        (work / "frontage_review.json").write_bytes(
            canonical(
                {
                    "cells": cells,
                    "ambiguous_matches": review,
                    "height_conflicts": height_review,
                    "summary": summary,
                }
            )
        )
        os.rename(package, work / "package")
        os.rename(work, dest)
    return summary


def write_package(package, base, evidence, normal, objects, summary):
    artifacts = {
        "validation": canonical({**evidence, "label": G03_LABEL, "harvest": summary}),
        "normalized": canonical(normal),
        "object_catalog": canonical(
            [objects[key].model_dump(mode="json") for key in sorted(objects)]
        ),
    }
    for name, data in artifacts.items():
        (package / f"{name}.json").write_bytes(data)
    body = base.model_dump(mode="json", exclude={"content_sha256"})
    body.update(
        label=G03_LABEL,
        exchange_coordinates=GEOGRAPHIC_EXCHANGE,
        validation_sha256=digest(artifacts["validation"]),
        normalized_sha256=digest(artifacts["normalized"]),
        normalized_file_sha256=digest(artifacts["normalized"]),
        catalog_sha256=digest(artifacts["object_catalog"]),
        objects=[objects[key].model_dump(mode="json") for key in sorted(objects)],
        generated_object_counts=dict(
            Counter(record.kind for record in objects.values())
        ),
        confidence_summary=dict(
            Counter(record.confidence for record in objects.values())
        ),
    )
    manifest = SceneManifest.model_validate(
        {**body, "content_sha256": digest(canonical(body))}
    )
    (package / "scene_manifest.json").write_bytes(
        canonical(manifest.model_dump(mode="json"))
    )
