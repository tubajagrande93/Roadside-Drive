"""Run in Unreal's Python console to capture the selected Roadside object and camera."""

import json
import uuid
from pathlib import Path

import unreal


def capture_issue_context():
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    selection = actors.get_selected_level_actors()
    if len(selection) != 1 or not isinstance(
        selection[0], unreal.RoadsideWorldFeatureActor
    ):
        raise RuntimeError("Select exactly one imported Roadside object")
    actor = selection[0]
    feature_id = actor.get_editor_property("stable_id")
    hashes = [
        str(tag).removeprefix("rd_source_hash:")
        for tag in actor.get_editor_property("tags")
        if str(tag).startswith("rd_source_hash:")
    ]
    if len(hashes) != 1:
        raise RuntimeError("The selected actor has no unambiguous source hash")
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    camera = editor.get_level_viewport_camera_info()
    if not camera:
        raise RuntimeError("The editor viewport has no available camera transform")
    position, rotation = camera
    actor_center, _ = actor.get_actor_bounds(False)
    context = {
        "object_id": feature_id,
        "object_source_hash": hashes[0],
        "location_world_cm": [actor_center.x, actor_center.y, actor_center.z],
        "camera_xyz_cm": [position.x, position.y, position.z],
        "camera_yaw_pitch_deg": [rotation.yaw, rotation.pitch],
    }
    output = Path(
        unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
    )
    output = output / "RoadsideIssues"
    output.mkdir(parents=True, exist_ok=True)
    record = output / f"selection-{uuid.uuid4().hex}.json"
    with record.open("x", encoding="utf-8") as stream:
        json.dump(context, stream)
    unreal.log(f"Roadside issue context: {record}")
    return record
