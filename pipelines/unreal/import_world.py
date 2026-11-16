"""Unreal 5.7 editor script for a first isolated synthetic pilot import."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corridor_editor
from verify_spectator import exercise_spectator, start_pie

LEVEL = "/Game/RoadsideDrive/Levels/L_RD_WorldPilot"
GENERATED = "/Game/RoadsideDrive/Generated/G01"
SYNTHETIC = "SYNTHETIC — NOT BANJA LUKA"
MESH_PATH = re.compile(r"meshes/[a-f0-9]{64}\.glb\Z")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def editor_context():
    project = Path(
        unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
    ).resolve()
    target = Path(os.environ["RD_G01_DISPOSABLE_PROJECT"]).resolve(strict=True)
    if project != target or not (project / ".roadside-g01-disposable").is_file():
        raise RuntimeError("Use the disposable project from run_editor_smoke.py")
    return project


def read_scene():
    manifest = Path(os.environ["RD_G01_SCENE"]).resolve(strict=True)
    scene = json.loads(manifest.read_bytes())
    body = dict(scene)
    seal = body.pop("content_sha256")
    canonical = (
        json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()
    if (
        sha(canonical) != seal
        or scene["schema_version"] != 1
        or scene["unreal_units_per_meter"] != 100
        or scene["import_status"] != "NOT_EXECUTED"
    ):
        raise RuntimeError("The importer requires a sealed ScenePackage")
    synthetic = (
        scene["label"] == SYNTHETIC
        and scene["provenance"]["dataset_kind"] == "SYNTHETIC"
    )
    osm = (
        scene["label"]
        in (
            corridor_editor.CANDIDATE,
            corridor_editor.ACCEPTED,
            corridor_editor.HARVEST,
        )
        and scene["provenance"]["dataset_kind"] == "OSM"
        and scene["provenance"]["license_id"] == "ODbL-1.0"
    )
    if not (synthetic or osm):
        raise RuntimeError("The ScenePackage source and expected label disagree")
    files = {}
    for name, seal in (
        ("validation", "validation_sha256"),
        ("normalized", "normalized_file_sha256"),
    ):
        artifact = manifest.parent / f"{name}.json"
        if artifact.is_symlink() or sha(artifact.read_bytes()) != scene[seal]:
            raise RuntimeError(f"ScenePackage integrity failed: {name}")
        files[name] = json.loads(artifact.read_bytes())
    if osm:
        status = files["validation"]["corridor"]["route_status"]
        expected = (
            "ROUTE_REVIEW_REQUIRED"
            if scene["label"] == corridor_editor.CANDIDATE
            else "OPERATOR_ACCEPTED"
        )
        if status != expected:
            raise RuntimeError("OSM route approval and preview label disagree")
    for item in scene["objects"]:
        name = item["file"]
        if not MESH_PATH.fullmatch(name):
            raise RuntimeError("Unsafe package mesh path")
        mesh = manifest.parent / name
        if (
            mesh.is_symlink()
            or mesh.parent.is_symlink()
            or sha(mesh.read_bytes()) != item["sha256"]
        ):
            raise RuntimeError("Package mesh failed integrity check")
    return manifest.parent, scene, files


def measured_bounds(mesh, record):
    box = mesh.get_bounding_box()
    measured = [[p.x, p.y, p.z] for p in (box.min, box.max)]
    expected = [[x * 100 for x in row] for row in record["bounds_m"]]
    if any(
        not math.isfinite(value) or abs(value - target) > 2.0
        for row, expected_row in zip(measured, expected, strict=True)
        for value, target in zip(row, expected_row, strict=True)
    ):
        raise RuntimeError(
            f"World scale or axis mismatch for {record['stable_id']}: {measured} vs {expected}"
        )
    return measured


def import_mesh(folder, record, generated):
    task = unreal.AssetImportTask()
    area = generated + "/" + re.sub(r"[:-]", "_", record["stable_id"])
    for name, value in {
        "filename": str(folder / record["file"]),
        "destination_path": area,
        "automated": True,
        "replace_existing": False,
        "save": False,
    }.items():
        task.set_editor_property(name, value)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    meshes = [
        asset for asset in task.get_objects() if isinstance(asset, unreal.StaticMesh)
    ]
    if len(meshes) != 1 or not meshes[0].get_path_name().startswith(area + "/"):
        raise RuntimeError(
            f"GLB import did not create one owned mesh for {record['stable_id']}"
        )
    mesh = meshes[0]
    bounds = measured_bounds(mesh, record)
    body = mesh.get_editor_property("body_setup")
    if body is None:
        raise RuntimeError("Static mesh did not provide collision BodySetup")
    body.set_editor_property(
        "collision_trace_flag",
        unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE,
    )
    material = mesh.get_material(0)
    if material is None or not material.get_path_name().startswith(area + "/"):
        raise RuntimeError(
            f"Missing imported greybox material for {record['stable_id']}"
        )
    return mesh, bounds, material.get_path_name()


def trace(actor, x, y):
    return unreal.SystemLibrary.line_trace_single_by_profile(
        actor,
        unreal.Vector(x, y, 100),
        unreal.Vector(x, y, -2),
        "BlockAll",
        True,
        [],
        unreal.DrawDebugTrace.NONE,
        ignore_self=False,
    )


def prepare_preview(actors, road_actor):
    light_rotation = unreal.Rotator()
    light_rotation.pitch = -42
    light_rotation.yaw = 35
    light = actors.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0, 0, 10000), light_rotation
    )
    if light is None:
        raise RuntimeError("Could not create the synthetic preview light")
    light.set_actor_label("Synthetic pilot preview light")
    light_component = light.get_component_by_class(unreal.DirectionalLightComponent)
    light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    light_component.set_intensity(8.0)

    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    rotation = unreal.Rotator()
    rotation.pitch = -38
    rotation.yaw = 45
    view = unreal.Vector(-11500, -11500, 12500)
    editor.set_level_viewport_camera_info(view, rotation)
    first = editor.get_level_viewport_camera_info()
    editor.set_level_viewport_camera_info(
        unreal.Vector(view.x + 100, view.y, view.z), rotation
    )
    second = editor.get_level_viewport_camera_info()
    editor.set_level_viewport_camera_info(view, rotation)
    actors.set_selected_level_actors([road_actor])
    matched = [
        str(tag)
        for actor in actors.get_selected_level_actors()
        for tag in actor.get_editor_property("tags")
    ]
    return {
        "directional_light": True,
        "camera_api_move": "PASS"
        if first and second and abs(second[0].x - first[0].x - 100) < 1
        else "NOT_VERIFIED",
        "selection_api": "PASS"
        if "rd_id:road-east-west" in matched
        else "NOT_VERIFIED",
        "camera_start_cm": [view.x, view.y, view.z],
    }


def synthetic_preview(actors, road_actor):
    player_start = actors.spawn_actor_from_class(
        unreal.PlayerStart, unreal.Vector(-3500, 0, 450)
    )
    if player_start is None:
        raise RuntimeError("Could not place the pilot player start")
    player_start.set_actor_label("Roadside spectator start")

    return prepare_preview(actors, road_actor)


def run(mode):
    project = editor_context()
    if mode == "probe":
        return {
            "status": "NATIVE_API_PASS",
            "asset_import_task": hasattr(unreal, "AssetImportTask"),
            "level_subsystem": hasattr(unreal, "LevelEditorSubsystem"),
            "editor_actor_subsystem": hasattr(unreal, "EditorActorSubsystem"),
        }
    folder, scene, files = read_scene()
    route = files["validation"].get("corridor")
    harvest = files["validation"].get("harvest")
    level_path = corridor_editor.LEVEL if route else LEVEL
    generated = corridor_editor.GENERATED if route else GENERATED
    if harvest:
        level_path, generated = (
            corridor_editor.HARVEST_LEVEL,
            corridor_editor.HARVEST_GENERATED,
        )
    features = {
        item["stable_id"]: item
        for key in ("roads", "buildings")
        for item in files["normalized"][key]
    }
    if unreal.EditorAssetLibrary.does_asset_exist(
        level_path
    ) or unreal.EditorAssetLibrary.does_directory_exist(generated):
        raise RuntimeError(
            "Pilot level or generated namespace already exists. Use a new disposable project."
        )
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not level or not actors or not level.new_level(level_path):
        raise RuntimeError("Could not create isolated pilot level")
    records = []
    road_actor = None
    building_actor = None
    for item in scene["objects"]:
        stable_id = item["stable_id"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9:-]{0,79}", stable_id):
            raise RuntimeError("Unsupported feature ID")
        mesh, bounds, material = import_mesh(folder, item, generated)
        actor = actors.spawn_actor_from_class(
            unreal.RoadsideWorldFeatureActor, unreal.Vector()
        )
        if actor is None:
            raise RuntimeError(f"Could not place generated mesh {stable_id}")
        display = harvest["labels"].get(stable_id, stable_id) if harvest else stable_id
        actor.set_actor_label(f"{scene['label']} / {display}")
        actor.set_editor_property(
            "tags",
            [
                f"rd_id:{stable_id}",
                f"rd_confidence:{item['confidence']}",
                f"rd_source_hash:{item['source_hash']}",
            ],
        )
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        component.set_static_mesh(mesh)
        component.set_collision_profile_name(
            "BlockAll"
            if item["kind"] in {"road", "building", "ground"}
            else "NoCollision"
        )
        low, high = item["bounds_m"]
        origin = scene["origin"]
        actor.initialize_catalog(
            stable_id,
            item["kind"],
            unreal.Vector(*low),
            unreal.Vector(*high),
            unreal.Vector(origin["east_m"], origin["north_m"], origin["z_m"]),
            scene["source_crs"],
            scene["provenance"]["dataset_kind"],
            item["confidence"],
        )
        feature = features.get(stable_id, {})
        point = route["object_source_centers_wgs84"].get(stable_id) if route else None
        actor.initialize_provenance(
            ", ".join(item["source_elements"]),
            route["graph_sha256"] if route else scene["source_sha256"],
            (
                f"{feature['width_m']:g} m · {feature['width_basis']}"
                if "width_m" in feature
                else (
                    f"{feature['height_m']:g} m · {feature['height_basis']}"
                    if feature.get("height_m") is not None
                    else (item["height_basis"] or scene["elevation_status"])
                )
            )
            if route
            else scene["elevation_status"],
            f"{point[0]:.8f}, {point[1]:.8f}" if point else "",
            item["material_category"],
        )
        if stable_id == "road-east-west" or (
            route and item["kind"] == "road" and road_actor is None
        ):
            road_actor = actor
        if item["kind"] == "building" and building_actor is None:
            building_actor = actor
        records.append(
            {
                "id": stable_id,
                "mesh": mesh.get_path_name(),
                "bounds_cm": bounds,
                "material": material,
            }
        )
    if road_actor is None:
        raise RuntimeError("Package lacked its control road")
    if not unreal.EditorAssetLibrary.save_directory(generated, only_if_is_dirty=True):
        raise RuntimeError("Could not save generated meshes and materials")
    editor_world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem
    ).get_editor_world()
    game_mode = (
        unreal.RoadsideCorridorGameMode if route else unreal.RoadsideSpectatorGameMode
    )
    editor_world.get_world_settings().set_editor_property(
        "default_game_mode", game_mode.static_class()
    )
    if route:
        preview = corridor_editor.preview(actors, route, scene["label"])
        if harvest:
            preview["landmark_viewpoints"] = corridor_editor.harvest_viewpoints(
                actors, harvest
            )
    else:
        preview = synthetic_preview(actors, road_actor)
    inspector = {
        "id": road_actor.get_editor_property("stable_id"),
        "type": road_actor.get_editor_property("feature_type"),
        "length_m": road_actor.get_editor_property("dimensions_m").x,
        "source": road_actor.get_editor_property("source_type"),
        "confidence": road_actor.get_editor_property("confidence"),
    }
    if not route and inspector != {
        "id": "road-east-west",
        "type": "road",
        "length_m": 100.0,
        "source": "SYNTHETIC",
        "confidence": "VERIFIED",
    }:
        raise RuntimeError(
            f"Inspector did not retain the control road's metadata: {inspector}"
        )
    if route:
        if building_actor is None:
            raise RuntimeError("G02 expected one native building inspection control")
        inspector["aabb_x_m"] = inspector["length_m"]
        inspector["length_m"] = files["validation"]["road_lengths_m"][inspector["id"]]
        inspector.update(
            {
                "source_elements": road_actor.get_editor_property("source_elements"),
                "longitude_latitude": road_actor.get_editor_property(
                    "source_longitude_latitude"
                ),
                "width_basis": road_actor.get_editor_property("width_or_height_basis"),
                "building_id": building_actor.get_editor_property("stable_id"),
                "building_source": building_actor.get_editor_property(
                    "source_elements"
                ),
            }
        )
        actors.set_selected_level_actors([road_actor])
    if not level.save_current_level():
        raise RuntimeError("The pilot level could not be saved")
    if route:
        middle = route["checkpoints_local_m"][1]
        trace_ok = trace(road_actor, middle[0] * 100, middle[1] * 100) is not None
        trace_ok = trace_ok and trace(road_actor, 1_000_000, 1_000_000) is None
    else:
        trace_ok = (
            trace(road_actor, 2500, 0) is not None
            and trace(road_actor, 30_000, 30_000) is None
        )
    evidence = {
        "status": "NATIVE_IMPORT_PASS",
        "level": level_path,
        "scene_sha256": scene["content_sha256"],
        "records": records,
        "collision_trace": "PASS" if trace_ok else "FAIL",
        "preview": preview,
        "editor_freecam": "NOT_EXECUTED",
        "runtime_spectator": "NOT_RUN",
        "object_inspector": inspector,
    }
    evidence["level_file_present"] = (
        project / ("Content/" + level_path.removeprefix("/Game/") + ".umap")
    ).is_file()
    return evidence, route


def write_evidence(result):
    Path(os.environ["RD_G01_NATIVE_EVIDENCE"]).write_text(
        json.dumps(result), encoding="utf-8"
    )
    unreal.log("RD_G01: " + json.dumps(result))


if __name__ == "__main__":
    mode = os.environ.get("RD_G01_MODE", "probe")
    try:
        if mode == "probe":
            write_evidence(run(mode))
        else:
            result, route = run(mode)
            if mode == "spectator":

                def exercise(pawn, player):
                    if route:
                        return corridor_editor.exercise_corridor(
                            pawn, player, route, route["building_smoke_point_local_m"]
                        )
                    return exercise_spectator(pawn, player)

                start_pie(
                    result,
                    write_evidence,
                    exercise,
                    corridor_editor.verify_input if route else None,
                )
            else:
                write_evidence(result)
    except Exception as error:
        write_evidence(
            {"status": "FAIL", "boundary": type(error).__name__, "error": str(error)}
        )
        raise
