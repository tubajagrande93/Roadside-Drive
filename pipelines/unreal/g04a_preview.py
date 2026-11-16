"""Create the G04A copy of the oriented G03 level, then save only new assets."""

import hashlib
import json
import os
import sys
from pathlib import Path

import unreal

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "src")]
from g04a_atmosphere import atmosphere
from g04a_materials import ROOT, create_pbr, import_asset
from import_world import measured_bounds
from verify_orientation import audit_landmarks

from roadside_drive.world.orientation import GEOGRAPHIC_EXCHANGE, local_to_ue_cm

PARENT = "/Game/RoadsideDrive/Levels/L_RD_G03_Corridor"
LEVEL = "/Game/RoadsideDrive/Levels/L_RD_G04A_Visual200"
CAMERAS = ("START", "100M", "200M", "250M", "SKY")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sealed(path):
    body = json.loads(path.read_bytes())
    seal = body.pop("content_sha256")
    raw = (
        json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()
    if digest(raw) != seal:
        raise RuntimeError(f"Unsealed manifest {path.name}")
    body["content_sha256"] = seal
    return body


def editor():
    project = Path(
        unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
    ).resolve()
    if (
        project != Path(os.environ["RD_G04A_PROJECT"]).resolve(strict=True)
        or not (project / ".roadside-g04a-disposable").is_file()
    ):
        raise RuntimeError("Use the designated disposable G04A clone")
    return project, *(
        unreal.get_editor_subsystem(cls)
        for cls in (
            unreal.LevelEditorSubsystem,
            unreal.EditorActorSubsystem,
            unreal.UnrealEditorSubsystem,
        )
    )


def native_features(actors, parent):
    features = {
        actor.get_editor_property("stable_id"): actor
        for actor in actors.get_all_level_actors()
        if isinstance(actor, unreal.RoadsideWorldFeatureActor)
    }
    if features.keys() != {item["stable_id"] for item in parent["objects"]}:
        raise RuntimeError("The copied level does not match the sealed G03 object set")
    return features


def setup_cameras(actors, preview, stations):
    options = {
        "START": (0, 166, -2, 0),
        "100M": (100, 166, -8, 24),
        "200M": (200, 305, -24, 120),
        "250M": (250, 172, -4, 0),
        "SKY": (100, 225, 25, 0),
    }
    for label, (station, height, pitch, turn) in options.items():
        sample = stations[str(station)]
        p = unreal.Vector(*local_to_ue_cm((*sample["local_m"], height / 100)))
        facing = unreal.Rotator(pitch=pitch, yaw=sample["yaw_deg"] + turn)
        camera = actors.spawn_actor_from_class(unreal.CameraActor, p, facing)
        camera.set_actor_label("RD G04A " + label)
        if label == "START":
            preview.set_level_viewport_camera_info(p, facing)


def install_overlays(actors, folder, records, instances, profiles):
    actual = {}
    for name, spec in records.items():
        mesh = import_asset(
            folder / spec["file"], f"{ROOT}/Meshes/{name}", unreal.StaticMesh
        )
        bounds = measured_bounds(
            mesh,
            {"stable_id": spec["id"], "bounds_m": spec["bounds_m"]},
            GEOGRAPHIC_EXCHANGE,
        )
        material = instances[spec["texture_set"]]
        if material.get_path_name().split(".")[0] != spec["material"]:
            raise RuntimeError(f"G04A material path mismatch for {name}")
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector())
        actor.set_actor_label("RD G04A " + name)
        actor.set_editor_property("tags", [spec["id"]])
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        comp.set_static_mesh(mesh)
        comp.set_material(0, material)
        comp.set_collision_profile_name(profiles)
        comp.set_editor_property("generate_overlap_events", False)
        if (
            comp.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION
            or comp.get_material(0) != material
        ):
            raise RuntimeError(f"Overlay collision or binding failed for {name}")
        actual[name] = {"material": material.get_path_name(), "bounds_cm": bounds}
    return actual


def run():
    project, level, actors, preview = editor()
    overlay_path = Path(os.environ["RD_G04A_OVERLAY"]).resolve(strict=True)
    parent_path = Path(os.environ["RD_G04A_PARENT_SCENE"]).resolve(strict=True)
    textures = Path(os.environ["RD_G04A_TEXTURES"]).resolve(strict=True)
    overlay = sealed(overlay_path)
    parent = sealed(parent_path)
    if (
        overlay["parent_scene_sha256"] != parent["content_sha256"]
        or overlay["exchange_coordinates"] != parent["exchange_coordinates"]
        or parent["exchange_coordinates"] != GEOGRAPHIC_EXCHANGE
        or overlay["collision_profile"] != "NoCollision"
    ):
        raise RuntimeError("This overlay requires its exact signed G03 parent")
    for item in overlay["surfaces"].values():
        path = overlay_path.parent / item["file"]
        if path.name != item["file"] or digest(path.read_bytes()) != item["sha256"]:
            raise RuntimeError("Overlay mesh failed digest verification")
    pbr_path = textures / "texture_manifest.json"
    if digest(pbr_path.read_bytes()) != overlay["texture_manifest_sha256"]:
        raise RuntimeError("Texture manifest differs from the overlay package")
    pbr = json.loads(pbr_path.read_bytes())
    for name, spec in pbr["assets"].items():
        if (
            Path(name).name != name
            or digest((textures / name).read_bytes()) != spec["sha256"]
        ):
            raise RuntimeError("Texture differs from the original sealed asset")
    if (
        project / "Content" / (LEVEL.removeprefix("/Game/") + ".umap")
    ).exists() or unreal.EditorAssetLibrary.does_directory_exist(ROOT):
        raise RuntimeError("G04A writer needs a fresh generated content namespace")
    if not level.load_level(PARENT):
        raise RuntimeError("The original signed G03 level could not be opened")
    route = json.loads(parent_path.with_name("validation.json").read_bytes())[
        "corridor"
    ]
    controls = json.loads(Path(os.environ["RD_G04A_G03_ORIENTATION"]).read_bytes())
    parent_orientation = audit_landmarks(
        controls, route, native_features(actors, parent), parent["content_sha256"]
    )
    if not level.new_level_from_template(LEVEL, PARENT):
        raise RuntimeError("Could not create G04A level from G03 template")
    features = native_features(actors, parent)
    current_orientation = audit_landmarks(
        controls, route, features, parent["content_sha256"]
    )
    if current_orientation != parent_orientation:
        raise RuntimeError("G04A clone changed absolute positions of G03 landmarks")
    instances = create_pbr(textures, pbr)
    actual = install_overlays(
        actors,
        overlay_path.parent,
        overlay["surfaces"],
        instances,
        overlay["collision_profile"],
    )
    stations = overlay["stations"]
    atmosphere(
        actors,
        unreal.Vector(*local_to_ue_cm((*stations["100"]["local_m"], 0))),
        stations["100"]["yaw_deg"],
    )
    setup_cameras(actors, preview, stations)
    if (
        not unreal.EditorAssetLibrary.save_directory(ROOT, True, False)
        or not level.save_current_level()
    ):
        raise RuntimeError("Could not persist new G04A assets and level")
    return {
        "status": "G04A_NATIVE_SAVE_PASS",
        "scene_sha256": overlay["content_sha256"],
        "level": LEVEL,
        "parent_actor_count": len(features),
        "geographic_orientation": current_orientation,
        "overlay_actors": actual,
    }


if __name__ == "__main__":
    result = run()
    Path(os.environ["RD_G04A_BUILD_EVIDENCE"]).write_text(json.dumps(result, indent=2))
    unreal.log(f"RD_G04A_SAVE: {json.dumps(result)}")
