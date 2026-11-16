"""Deterministic synthetic ScenePackage build and independent verification."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from collections import Counter
from io import BytesIO
from pathlib import Path

import numpy as np
import trimesh
from pydantic import TypeAdapter
from shapely.geometry import LineString

from .contracts import (
    BuildingFeature,
    CorrectionPatch,
    ObjectRecord,
    SceneManifest,
    Source,
    apply_corrections,
    canonical,
    digest,
)
from .geometry import PLACEHOLDER_HEIGHT_M, mesh_corridor, mesh_features
from .projections import engine_coordinates, projected_crs

MESH_NAME = re.compile(r"meshes/[a-f0-9]{64}\.glb\Z")
SYNTHETIC_LABEL = "SYNTHETIC — NOT BANJA LUKA"
CORRIDOR_LABEL = "OSM BANJA LUKA — PROVISIONAL GREYBOX"
CANDIDATE_LABEL = "OSM BANJA LUKA — ROUTE CANDIDATE"
GREYBOX_COLOURS = {
    "road": [57, 63, 70, 255],
    "building": [174, 177, 182, 255],
    "ground": [114, 124, 118, 255],
}


def confined(root, value):
    root = root.resolve(strict=True)
    form = Path(value)
    if form.is_absolute() or not form.parts or ".." in form.parts:
        raise ValueError("Use a confined repository-relative path")
    path = root
    for part in form.parts:
        path /= part
        if path.is_symlink():
            raise ValueError("Symlink path is outside the package trust boundary")
    return path


def fresh_generated_path(root, value):
    path = confined(root, value)
    boundary = confined(root, "data/processed/world_builder")
    if boundary not in path.parents:
        raise ValueError("Output must be under data/processed/world_builder/")
    return path


def glb(faces, kind):
    index = {}
    ordered_faces = [
        [
            index.setdefault(engine_coordinates(vertex), len(index))
            for vertex in reversed(face)
        ]
        for face in faces
    ]
    mesh = trimesh.Trimesh(vertices=list(index), faces=ordered_faces, process=False)
    check_mesh(mesh)
    mesh.visual = trimesh.visual.TextureVisuals(
        material=trimesh.visual.material.PBRMaterial(
            name=kind,
            baseColorFactor=GREYBOX_COLOURS[kind],
            metallicFactor=0.0,
            roughnessFactor=1.0,
        )
    )
    return mesh.export(file_type="glb")


def check_mesh(mesh):
    if (
        not isinstance(mesh, trimesh.Trimesh)
        or not len(mesh.faces)
        or not np.isfinite(mesh.vertices).all()
        or np.any(mesh.area_faces <= 1e-8)
    ):
        raise ValueError("Mesh has missing, nonfinite or degenerate triangles")
    return mesh


def build_fixture(root, config, output, patches_path=None):
    settings = json.loads(confined(root, config).read_bytes())
    if (
        set(settings) != {"schema_version", "fixture", "deterministic_seed"}
        or settings["schema_version"] != 1
        or settings["deterministic_seed"] != 0
    ):
        raise ValueError("Unsupported deterministic fixture config")
    original = confined(root, settings["fixture"]).read_bytes()
    source = Source.model_validate_json(original)
    if (
        source.provenance.dataset_kind != "SYNTHETIC"
        or source.provenance.license_id != "PROJECT_TEST_DATA"
        or source.provenance.source_uri != "LOCAL_FIXTURE"
    ):
        raise ValueError("build-fixture accepts only attributed synthetic test data")
    projected_crs(source.projected_crs)
    return build_scene(root, output, source, original, patches_path)


def build_scene(root, output, source, original, patches_path=None, *, corridor=None):
    patch_bytes = confined(root, patches_path).read_bytes() if patches_path else b"[]"
    patches = TypeAdapter(tuple[CorrectionPatch, ...]).validate_json(patch_bytes)
    roads, buildings = apply_corrections(source, patches)
    target = fresh_generated_path(root, output)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".world-scene-", dir=target.parent))
    try:
        manifest = generate_scene(
            staging, source, original, patches, roads, buildings, corridor=corridor
        )
        validate_scene(staging / "scene_manifest.json")
        if target.exists():
            existing = validate_scene(target / "scene_manifest.json")
            if existing.content_sha256 != manifest.content_sha256:
                raise ValueError(
                    "Existing output differs. Select a new output to preserve it."
                )
        else:
            os.rename(staging, target)
        return manifest
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def generate_scene(staging, source, original, patches, roads, buildings, *, corridor):
    (staging / "meshes").mkdir()
    known = {item.stable_id: item for item in (*roads, *buildings)}
    raw = {item.stable_id: item for item in (*source.roads, *source.buildings)}
    records = []
    meshes = (
        sorted(mesh_corridor(roads, buildings, source.origin, corridor["floor"]))
        if corridor
        else mesh_features(roads, buildings, source.origin)
    )
    label = corridor["label"] if corridor else SYNTHETIC_LABEL
    for stable_id, faces in meshes:
        feature = known.get(stable_id)
        fixed = isinstance(feature, BuildingFeature)
        visual_height = (feature.height_m or PLACEHOLDER_HEIGHT_M) if fixed else None
        source_hash = (
            raw[stable_id].source_hash() if feature is not None else digest(original)
        )
        confidence = feature.confidence if feature is not None else "PLACEHOLDER"
        if fixed and feature.height_m is None:
            confidence = "PLACEHOLDER"
        kind = feature.kind if feature is not None else "ground"
        model = glb(faces, kind)
        file = f"meshes/{digest(stable_id.encode())}.glb"
        (staging / file).write_bytes(model)
        vertices = np.asarray(faces).reshape(-1, 3)
        bounds = [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()]
        records.append(
            ObjectRecord(
                stable_id=stable_id,
                kind=kind,
                source_hash=source_hash,
                file=file,
                sha256=digest(model),
                source_elements=feature.source_elements
                if feature is not None
                else (
                    ("provisional:flat-ground",) if corridor else ("synthetic:ground",)
                ),
                bounds_m=bounds,
                face_count=len(faces),
                confidence=confidence,
                visual_height_m=visual_height,
                height_basis=(
                    feature.height_basis
                    if feature.height_m is not None
                    else "PLACEHOLDER_6_M"
                )
                if fixed
                else None,
                material_category={
                    "road": "grey_road",
                    "building": "neutral_shell",
                    "ground": "flat_ground",
                }[kind],
            ).model_dump(mode="json")
        )
    normalized = canonical(
        {
            "roads": [f.model_dump(mode="json") for f in roads],
            "buildings": [f.model_dump(mode="json") for f in buildings],
        }
    )
    catalog = canonical(records)
    validation = canonical(
        {
            "status": "PASS",
            "network_requests": 0,
            "editor_import": "NOT_EXECUTED",
            "collision": "NOT_EXECUTED",
            "unit_control_m": 100,
            "road_lengths_m": {
                f.stable_id: LineString(f.centerline_m).length for f in roads
            },
            "crossings": 1 if not corridor else None,
            "label": label,
            **({"corridor": corridor["evidence"]} if corridor else {}),
        }
    )
    for filename, data in (
        ("normalized.json", normalized),
        ("object_catalog.json", catalog),
        ("validation.json", validation),
    ):
        (staging / filename).write_bytes(data)
    body = {
        "schema_version": 1,
        "build_tool_version": "0.1",
        "world_id": source.world_id,
        "label": label,
        "provenance": source.provenance.model_dump(mode="json"),
        "source_crs": source.source_crs,
        "projected_crs": source.projected_crs,
        "origin": source.origin.model_dump(),
        "elevation_status": "FLAT_PROVISIONAL_Z0",
        "unreal_units_per_meter": 100,
        "exchange_coordinates": "glTF metres: X east, Y up, Z north",
        "source_sha256": digest(original),
        "normalized_sha256": digest(normalized),
        "patch_set_sha256": digest(
            canonical([p.model_dump(mode="json") for p in patches])
        ),
        "normalized_file_sha256": digest(normalized),
        "catalog_sha256": digest(catalog),
        "validation_sha256": digest(validation),
        "aoi_geometry_wgs84": corridor["aoi"] if corridor else None,
        "aoi_approval_status": "APPROVED" if corridor else "NOT_APPLICABLE",
        "import_status": "NOT_EXECUTED",
        "source_feature_counts": {
            "road": len(source.roads),
            "building": len(source.buildings),
        },
        "generated_object_counts": dict(Counter(item["kind"] for item in records)),
        "confidence_summary": dict(Counter(item["confidence"] for item in records)),
        "objects": records,
    }
    manifest = SceneManifest.model_validate(
        {**body, "content_sha256": digest(canonical(body))}
    )
    (staging / "scene_manifest.json").write_bytes(
        canonical(manifest.model_dump(mode="json"))
    )
    return manifest


def validate_scene(manifest_path):
    if manifest_path.name != "scene_manifest.json" or manifest_path.is_symlink():
        raise ValueError("Expected a regular scene_manifest.json")
    parent = manifest_path.parent
    scene = SceneManifest.model_validate_json(manifest_path.read_bytes())
    if (
        digest(canonical(scene.model_dump(mode="json", exclude={"content_sha256"})))
        != scene.content_sha256
    ):
        raise ValueError("Manifest content hash mismatch")
    synthetic = (
        scene.label == SYNTHETIC_LABEL
        and scene.provenance.dataset_kind == "SYNTHETIC"
        and scene.provenance.license_id == "PROJECT_TEST_DATA"
    )
    osm = (
        scene.label in {CORRIDOR_LABEL, CANDIDATE_LABEL}
        and scene.provenance.dataset_kind == "OSM"
        and scene.provenance.license_id == "ODbL-1.0"
        and bool(scene.provenance.attribution)
        and scene.aoi_approval_status == "APPROVED"
        and bool(scene.aoi_geometry_wgs84)
    )
    if scene.provenance.forbidden_source or not (synthetic or osm):
        raise ValueError("Invalid scene source boundary or label")
    projected_crs(scene.projected_crs)
    files = {
        "scene_manifest.json",
        "object_catalog.json",
        "validation.json",
        "normalized.json",
        *[item.file for item in scene.objects],
    }
    if any(path.is_symlink() for path in parent.rglob("*")):
        raise ValueError("Symlink entries are not allowed in ScenePackages")
    actual = {
        path.relative_to(parent).as_posix()
        for path in parent.rglob("*")
        if not path.is_dir()
    }
    if actual != files:
        raise ValueError("Package has missing or unmanaged files")
    for name, expected in (
        ("normalized.json", scene.normalized_file_sha256),
        ("object_catalog.json", scene.catalog_sha256),
        ("validation.json", scene.validation_sha256),
    ):
        if digest(confined(parent, name).read_bytes()) != expected:
            raise ValueError(f"Artifact digest mismatch: {name}")
    ids = [item.stable_id for item in scene.objects]
    if ids != sorted(set(ids)) or len(files) != len(ids) + 4:
        raise ValueError("Expected stable unique ordered IDs and meshes")
    counts = Counter(item.kind for item in scene.objects)
    if (
        dict(counts) != scene.generated_object_counts
        or (synthetic and (counts["road"] != 2 or counts["building"] < 3))
        or (osm and counts["road"] == 0)
        or counts["ground"] != 1
    ):
        raise ValueError("Unexpected scene object counts")
    catalog = json.loads(confined(parent, "object_catalog.json").read_bytes())
    if catalog != [item.model_dump(mode="json") for item in scene.objects]:
        raise ValueError("Catalog disagrees with the scene manifest")
    for item in scene.objects:
        if (
            not MESH_NAME.fullmatch(item.file)
            or item.file != f"meshes/{digest(item.stable_id.encode())}.glb"
        ):
            raise ValueError("Unsafe or mismatched mesh path")
        data = confined(parent, item.file).read_bytes()
        if digest(data) != item.sha256 or data[:4] != b"glTF":
            raise ValueError("Mesh digest or format mismatch")
        mesh = check_mesh(
            trimesh.load(BytesIO(data), file_type="glb", force="mesh", process=False)
        )
        material = getattr(mesh.visual, "material", None)
        if material is None or not np.array_equal(
            material.baseColorFactor, GREYBOX_COLOURS[item.kind]
        ):
            raise ValueError("Mesh greybox material differs from the catalog category")
        if len(mesh.faces) != item.face_count:
            raise ValueError("Mesh face count mismatch")
        (x0, y0, z0), (x1, y1, z1) = item.bounds_m
        if not np.allclose(
            mesh.bounds, [[x0, z0, y0], [x1, z1, y1]], atol=0.0001, rtol=0
        ):
            raise ValueError("Mesh coordinates differ from catalog bounds")
        if item.kind in {"road", "ground"} and not np.all(
            mesh.face_normals[:, 1] > 0.99
        ):
            raise ValueError("Surface normals violate the Y-up exchange contract")
    return scene
