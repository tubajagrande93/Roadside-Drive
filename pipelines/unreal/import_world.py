"""Unreal 5.7 editor script for a first isolated synthetic pilot import."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from pathlib import Path

import unreal

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
        or scene["label"] != SYNTHETIC
        or scene["provenance"]["dataset_kind"] != "SYNTHETIC"
        or scene["unreal_units_per_meter"] != 100
        or scene["import_status"] != "NOT_EXECUTED"
    ):
        raise RuntimeError("The importer requires a verified synthetic ScenePackage")
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
    return manifest.parent, scene


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


def import_mesh(folder, record):
    task = unreal.AssetImportTask()
    area = GENERATED + "/" + record["stable_id"].replace("-", "_")
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
    if not unreal.EditorAssetLibrary.save_directory(area, only_if_is_dirty=False):
        raise RuntimeError("Unable to save the generated mesh and its material")
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


def run(mode):
    project = editor_context()
    if mode == "probe":
        return {
            "status": "NATIVE_API_PASS",
            "asset_import_task": hasattr(unreal, "AssetImportTask"),
            "level_subsystem": hasattr(unreal, "LevelEditorSubsystem"),
            "editor_actor_subsystem": hasattr(unreal, "EditorActorSubsystem"),
        }
    folder, scene = read_scene()
    if unreal.EditorAssetLibrary.does_asset_exist(
        LEVEL
    ) or unreal.EditorAssetLibrary.does_directory_exist(GENERATED):
        raise RuntimeError(
            "Pilot level or generated namespace already exists. Use a new disposable project."
        )
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not level or not actors or not level.new_level(LEVEL):
        raise RuntimeError("Could not create isolated pilot level")
    records = []
    road_actor = None
    for item in scene["objects"]:
        stable_id = item["stable_id"]
        if not re.fullmatch(r"[a-z0-9-]+", stable_id):
            raise RuntimeError("Unsupported synthetic feature ID")
        mesh, bounds, material = import_mesh(folder, item)
        actor = actors.spawn_actor_from_class(
            unreal.RoadsideWorldFeatureActor, unreal.Vector()
        )
        if actor is None:
            raise RuntimeError(f"Could not place generated mesh {stable_id}")
        actor.set_actor_label(f"{SYNTHETIC} / {stable_id}")
        actor.set_editor_property(
            "tags", [f"rd_id:{stable_id}", f"rd_confidence:{item['confidence']}"]
        )
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        component.set_static_mesh(mesh)
        component.set_collision_profile_name("BlockAll")
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
        if stable_id == "road-east-west":
            road_actor = actor
        records.append(
            {
                "id": stable_id,
                "mesh": mesh.get_path_name(),
                "bounds_cm": bounds,
                "material": material,
            }
        )
    if road_actor is None:
        raise RuntimeError("Synthetic package lacked its control road")
    editor_world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem
    ).get_editor_world()
    editor_world.get_world_settings().set_editor_property(
        "default_game_mode", unreal.RoadsideSpectatorGameMode.static_class()
    )
    player_start = actors.spawn_actor_from_class(
        unreal.PlayerStart, unreal.Vector(-3500, 0, 450)
    )
    if player_start is None:
        raise RuntimeError("Could not place the pilot player start")
    player_start.set_actor_label("Roadside spectator start")

    preview = prepare_preview(actors, road_actor)
    inspector = {
        "id": road_actor.get_editor_property("stable_id"),
        "type": road_actor.get_editor_property("feature_type"),
        "length_m": road_actor.get_editor_property("dimensions_m").x,
        "source": road_actor.get_editor_property("source_type"),
        "confidence": road_actor.get_editor_property("confidence"),
    }
    if inspector != {
        "id": "road-east-west",
        "type": "road",
        "length_m": 100.0,
        "source": "SYNTHETIC",
        "confidence": "VERIFIED",
    }:
        raise RuntimeError(
            f"Inspector did not retain the control road's metadata: {inspector}"
        )
    if not level.save_current_level():
        raise RuntimeError("The pilot level could not be saved")
    trace_ok = (
        road_actor is not None
        and trace(road_actor, 2500, 0) is not None
        and trace(road_actor, 30_000, 30_000) is None
    )
    evidence = {
        "status": "NATIVE_IMPORT_PASS",
        "level": LEVEL,
        "scene_sha256": scene["content_sha256"],
        "records": records,
        "collision_trace": "PASS" if trace_ok else "FAIL",
        "preview": preview,
        "editor_freecam": "NOT_EXECUTED",
        "runtime_spectator": "NOT_RUN",
        "object_inspector": inspector,
    }
    evidence["level_file_present"] = (
        project / "Content/RoadsideDrive/Levels/L_RD_WorldPilot.umap"
    ).is_file()
    return evidence


def exercise_spectator(pawn, player):
    """Exercise the same runtime movement method that consumes the live keys."""
    player.set_control_rotation(unreal.Rotator())

    def put(x, y, z):
        pawn.set_actor_location(unreal.Vector(x, y, z), False, True)

    def apply(x, y, z, dt=1.0, boost=False):
        pawn.apply_flight_input(unreal.Vector(x, y, z), dt, boost)
        return pawn.get_actor_location()

    put(2500, 0, 500)
    road = apply(0, 0, -1).z
    put(3500, 2000, 500)
    ground = apply(0, 0, -1).z
    put(950, 1500, 250)
    middle = apply(1, 0, 0, 0.5).x
    through = apply(1, 0, 0, 0.5, True).x
    put(1500, 1500, 250)
    inside = apply(0, 0, -1).z
    put(3500, 2000, 300)
    above = apply(0, 0, 1, 0.25).z
    put(30000, 30000, 500)
    fallback = apply(0, 0, -1).z
    checks = {
        "road_camera_z_cm": road,
        "ground_camera_z_cm": ground,
        "building_camera_z_cm": inside,
        "outside_camera_z_cm": fallback,
        "inside_building_x_cm": middle,
        "beyond_building_x_cm": through,
        "ascended_camera_z_cm": above,
    }
    if not (
        abs(road - 120) < 2
        and abs(ground - 115) < 2
        and abs(inside - 115) < 2
        and abs(fallback - 115) < 2
        and 1000 < middle < 2500
        and through > 2500
        and above > 300
    ):
        raise RuntimeError(f"Spectator movement or floor check failed: {checks}")
    return checks


def write_evidence(result):
    Path(os.environ["RD_G01_NATIVE_EVIDENCE"]).write_text(
        json.dumps(result), encoding="utf-8"
    )
    unreal.log("RD_G01: " + json.dumps(result))


def start_pie(result):
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    deadline = time.monotonic() + 45
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    handle = None

    def poll(_delta_seconds):
        try:
            world = editor.get_game_world()
            player = (
                unreal.GameplayStatics.get_player_controller(world, 0)
                if world
                else None
            )
            pawn = player.get_controlled_pawn() if player else None
            if pawn is None and time.monotonic() < deadline:
                return
            if not isinstance(pawn, unreal.RoadsideSpectatorPawn):
                raise TypeError(f"PIE did not possess RoadsideSpectatorPawn: {pawn}")
            result["spectator_checks"] = exercise_spectator(pawn, player)
            result["runtime_spectator"] = "PASS"
        except (RuntimeError, TypeError, AttributeError, ValueError) as error:
            result["runtime_spectator"] = "FAIL"
            result["runtime_error"] = str(error)
        unreal.unregister_slate_post_tick_callback(handle)
        write_evidence(result)
        if level.is_in_play_in_editor():
            level.editor_request_end_play()
        unreal.EditorPythonScripting.set_keep_python_script_alive(False)

    handle = unreal.register_slate_post_tick_callback(poll)
    level.editor_request_begin_play()


if __name__ == "__main__":
    mode = os.environ.get("RD_G01_MODE", "probe")
    try:
        result = run(mode)
        if mode == "spectator":
            start_pie(result)
        else:
            write_evidence(result)
    except Exception as error:
        write_evidence(
            {"status": "FAIL", "boundary": type(error).__name__, "error": str(error)}
        )
        raise
