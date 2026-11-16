"""Reopen a saved disposable G02 level and capture native review evidence."""

from __future__ import annotations

import json
import os
import runpy
import time
from pathlib import Path

import unreal

LEVEL = "/Game/RoadsideDrive/Levels/L_RD_G02_Corridor"
NAMES = ("START", "MID", "END")


def run():
    project = Path(
        unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
    ).resolve(strict=True)
    if (
        project != Path(os.environ["RD_G02_REVIEW_PROJECT"]).resolve(strict=True)
        or not (project / ".roadside-g01-disposable").is_file()
    ):
        raise RuntimeError("Review must use a registered disposable Roadside project")
    out = project / "Saved" / "RoadsideG02Review"
    out.mkdir(parents=True, exist_ok=False)
    preflight = os.environ.get("RD_G02_KIT_PREFLIGHT")
    if preflight:
        runpy.run_path(preflight)
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(LEVEL):
        raise RuntimeError("Could not reopen the serialized G02 level")
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    if (
        world.get_world_settings().get_editor_property("default_game_mode")
        != unreal.RoadsideCorridorGameMode.static_class()
    ):
        raise RuntimeError("The G02 GameMode override did not persist")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actors.get_all_level_actors()
    found = {
        actor.get_actor_label(): actor
        for actor in all_actors
        if isinstance(actor, unreal.CameraActor)
    }
    cameras = [found[f"RD G02 {name} viewpoint"] for name in NAMES]
    features = [
        actor
        for actor in all_actors
        if isinstance(actor, unreal.RoadsideWorldFeatureActor)
    ]
    ids = {actor.get_editor_property("stable_id") for actor in features}
    if len(ids) != len(features) or not ids:
        raise RuntimeError("The saved level lost unique feature identities")
    road = next(
        actor
        for actor in features
        if actor.get_editor_property("feature_type") == "road"
    )
    building = next(
        actor
        for actor in features
        if actor.get_editor_property("feature_type") == "building"
    )

    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from inspection_feedback import capture_issue_context

    selected = {}
    for name, actor in (("road", road), ("building", building)):
        actors.set_selected_level_actors([actor])
        context = capture_issue_context()
        selected[name] = str(context.relative_to(project))
    actors.set_selected_level_actors([])

    result = {
        "status": "PENDING",
        "level": LEVEL,
        "unique_feature_actors": len(ids),
        "selected_issue_contexts": selected,
        "screenshots": {},
    }

    base = time.monotonic()
    frames = 0
    shot_index = 0
    screenshot = None
    deadline = base + 180
    handle = None

    def stop():
        unreal.unregister_slate_post_tick_callback(handle)
        (out / "review.json").write_text(json.dumps(result), encoding="utf-8")
        unreal.log(f"RD_G02_REOPEN: {json.dumps(result)}")
        unreal.EditorPythonScripting.set_keep_python_script_alive(False)

    def tick(_delta_seconds):
        nonlocal frames, shot_index, screenshot
        try:
            now = time.monotonic()
            if now > deadline:
                raise RuntimeError("Timed out waiting for native screenshot capture")
            if "editor_fps_sample" not in result:
                frames += 1
                if now - base < 2.0:
                    return
                result["editor_fps_sample"] = round(frames / (now - base), 2)
            if shot_index == len(cameras):
                result["status"] = "NATIVE_REOPEN_AND_RENDER_PASS"
                stop()
                return
            filename = out / f"{NAMES[shot_index].lower()}.png"
            if screenshot is None:
                screenshot = unreal.AutomationLibrary.take_high_res_screenshot(
                    1440, 900, str(filename), cameras[shot_index], delay=0.25
                )
            elif (
                screenshot.is_task_done()
                and filename.is_file()
                and filename.stat().st_size > 0
            ):
                result["screenshots"][NAMES[shot_index]] = filename.name
                shot_index += 1
                screenshot = None
        except (KeyError, RuntimeError, TypeError, AttributeError, OSError) as error:
            result.update(status="FAIL", error=str(error))
            stop()

    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    handle = unreal.register_slate_post_tick_callback(tick)


if __name__ == "__main__":
    run()
