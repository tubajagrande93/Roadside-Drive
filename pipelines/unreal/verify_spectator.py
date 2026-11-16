"""Unreal Play-in-Editor verification for imported Roadside worlds."""

import time

import unreal


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


def start_pie(result, write_evidence, exercise, verify_input=None):
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    deadline = time.monotonic() + 45
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    handle = None
    inputs = None
    next_input = 0.0

    def poll(_delta_seconds):
        nonlocal inputs, next_input
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
            if inputs is None:
                result["spectator_checks"] = exercise(pawn, player)
                if verify_input is not None:
                    inputs = verify_input(pawn, player)
            if inputs is not None:
                now = time.monotonic()
                if now < next_input:
                    return
                try:
                    next_input = now + next(inputs)
                    return
                except StopIteration as complete:
                    result["player_input_checks"] = complete.value
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
