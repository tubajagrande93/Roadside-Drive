"""Reopen the saved G04A level, render five views, then run the native PIE control."""

import json
import os
import sys
import time
from pathlib import Path

import unreal

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "src")]
from corridor_editor import exercise_corridor, verify_input
from g04a_materials import LIB
from g04a_preview import CAMERAS, LEVEL, editor, native_features, sealed
from verify_orientation import audit_landmarks
from verify_spectator import start_pie


def transform(camera):
    p = camera.get_actor_location()
    r = camera.get_actor_rotation()
    return {
        "location_cm": [p.x, p.y, p.z],
        "pitch_yaw_roll_deg": [r.pitch, r.yaw, r.roll],
    }


def validate_surfaces(actors, manifest):
    report = {}
    items = {actor.get_actor_label(): actor for actor in actors}
    for label, spec in manifest["surfaces"].items():
        actor = items["RD G04A " + label]
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        current = comp.get_material(0)
        if not current:
            raise RuntimeError(f"Missing saved G04A material for {label}")
        tile = LIB.get_material_instance_scalar_parameter_value(current, "WorldUVScale")
        if (
            comp.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION
            or current.get_path_name().split(".")[0] != spec["material"]
            or abs(tile - 1 / (spec["tile_metres"] * 100)) > 1e-8
        ):
            raise RuntimeError(f"Saved G04A overlay binding differs for {label}")
        report[label] = {
            "collision": "NoCollision",
            "material": spec["material"],
            "uv_scale": tile,
        }
    return report


def verify_input_after_viewport_settles(pawn, player):
    # Let the PIE input stack receive updates after switching out of the
    # high-resolution editor capture viewport.
    yield 2.0
    return (yield from verify_input(pawn, player))


def run():
    project, level, actors, preview = editor()
    if not level.load_level(LEVEL):
        raise RuntimeError("Could not reopen saved G04A level")
    overlay = sealed(Path(os.environ["RD_G04A_OVERLAY"]))
    parent_path = Path(os.environ["RD_G04A_PARENT_SCENE"])
    parent = sealed(parent_path)
    route = json.loads(parent_path.with_name("validation.json").read_bytes())[
        "corridor"
    ]
    controls = json.loads(Path(os.environ["RD_G04A_G03_ORIENTATION"]).read_bytes())
    features = native_features(actors, parent)
    native_orientation = audit_landmarks(
        controls, route, features, parent["content_sha256"]
    )
    world = preview.get_editor_world()
    if (
        world.get_world_settings().get_editor_property("default_game_mode")
        != unreal.RoadsideCorridorGameMode.static_class()
    ):
        raise RuntimeError("G04A lost the original floor-only spectator GameMode")
    all_actors = actors.get_all_level_actors()
    cameras = {
        actor.get_actor_label(): actor
        for actor in all_actors
        if isinstance(actor, unreal.CameraActor)
    }
    screen = [(name, cameras[f"RD G04A {name}"]) for name in CAMERAS]
    primitives = validate_surfaces(all_actors, overlay)
    lighting = {
        cls.__name__: sum(isinstance(actor, cls) for actor in all_actors)
        for cls in (unreal.DirectionalLight, unreal.SkyAtmosphere, unreal.SkyLight)
    }
    if any(count != 1 for count in lighting.values()):
        raise RuntimeError(f"Unexpected saved sky setup: {lighting}")
    out = project / "Saved" / os.environ.get("RD_G04A_REVIEW_DIR", "RoadsideG04AReview")
    if out.parent != project / "Saved":
        raise ValueError("Review outputs must stay in the disposable Saved directory")
    out.mkdir(parents=True, exist_ok=False)
    result = {
        "status": "RUNNING",
        "level": LEVEL,
        "scene_sha256": overlay["content_sha256"],
        "parent_count": len(features),
        "geographic_orientation": native_orientation,
        "lighting": lighting,
        "surfaces": primitives,
        "screenshots": {},
    }

    def write(report):
        with (out / "review.json").open("x") as file:
            json.dump(report, file, indent=2)
        unreal.log(f"RD_G04A_REVIEW: {json.dumps(report)}")

    start = time.monotonic()
    deadline = start + 180
    shot = None
    view = 0

    def tick(_delta):
        nonlocal shot, view
        try:
            now = time.monotonic()
            if now > deadline:
                raise RuntimeError("Timed out waiting for native G04A screenshot")
            if now - start < 3:
                return
            if view == len(screen):
                unreal.unregister_slate_post_tick_callback(handle)
                result["status"] = "NATIVE_REOPEN_AND_RENDER_PASS"

                def exercise(pawn, player):
                    return exercise_corridor(
                        pawn, player, route, route["building_smoke_point_local_m"]
                    )

                start_pie(result, write, exercise, verify_input_after_viewport_settles)
                return
            label, camera = screen[view]
            file = out / (label.lower() + ".png")
            if shot is None:
                shot = unreal.AutomationLibrary.take_high_res_screenshot(
                    1440, 900, str(file), camera, delay=0.40
                )
            elif shot.is_task_done() and file.is_file() and file.stat().st_size:
                result["screenshots"][label] = {"file": file.name, **transform(camera)}
                shot = None
                view += 1
        except (
            KeyError,
            RuntimeError,
            AttributeError,
            OSError,
            TypeError,
            ValueError,
        ) as exc:
            unreal.unregister_slate_post_tick_callback(handle)
            result.update(status="FAIL", error=str(exc))
            write(result)
            unreal.EditorPythonScripting.set_keep_python_script_alive(False)

    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    handle = unreal.register_slate_post_tick_callback(tick)


if __name__ == "__main__":
    run()
