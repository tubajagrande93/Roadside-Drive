"""Editor policy and runtime smoke for the bounded OSM corridor."""

from __future__ import annotations

import math

import unreal

LEVEL = "/Game/RoadsideDrive/Levels/L_RD_G02_Corridor"
GENERATED = "/Game/RoadsideDrive/Generated/G02"
CANDIDATE = "OSM BANJA LUKA — ROUTE CANDIDATE"
ACCEPTED = "OSM BANJA LUKA — PROVISIONAL GREYBOX"
HARVEST = "BANJA LUKA — SOURCE-BACKED ENVIRONMENT"
HARVEST_LEVEL = "/Game/RoadsideDrive/Levels/L_RD_G03_Corridor"
HARVEST_GENERATED = "/Game/RoadsideDrive/Generated/G03"


def preview(actors, route, label):
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    controls = route["checkpoints_local_m"]
    rotation = unreal.Rotator()
    rotation.pitch = -60
    rotation.yaw = -130
    for name, point in zip(("START", "MID", "END"), controls, strict=True):
        x, y = (axis * 100 for axis in point)
        viewpoint = unreal.Vector(x + 4500, y + 4500, 10500)
        camera = actors.spawn_actor_from_class(unreal.CameraActor, viewpoint, rotation)
        if camera is None:
            raise RuntimeError(f"Could not place {name} camera marker")
        camera.set_actor_label(f"RD G02 {name} viewpoint")
        if name == "START":
            editor.set_level_viewport_camera_info(viewpoint, rotation)

    x, y = (axis * 100 for axis in controls[0])
    start = actors.spawn_actor_from_class(
        unreal.PlayerStart, unreal.Vector(x, y, 500), unreal.Rotator(yaw=-130)
    )
    if start is None:
        raise RuntimeError("Could not place corridor player start")
    start.set_actor_label("RD G02 spectator start")

    light = actors.spawn_actor_from_class(
        unreal.DirectionalLight,
        unreal.Vector(x, y, 10000),
        unreal.Rotator(pitch=-42, yaw=35),
    )
    light.set_actor_label("RD G02 preview light")
    component = light.get_component_by_class(unreal.DirectionalLightComponent)
    component.set_mobility(unreal.ComponentMobility.MOVABLE)
    component.set_intensity(3.0)

    caption = actors.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(x - 1400, y + 600, 420)
    )
    caption.set_actor_label("RD G02 scope and OSM attribution")
    text = caption.get_component_by_class(unreal.TextRenderComponent)
    attribution = "© OpenStreetMap contributors · ODbL 1.0"
    if label == HARVEST:
        attribution += " · Overture Maps Foundation"
    text.set_text(unreal.Text(f"{label}\n{attribution}"))
    text.set_world_size(55)

    ruler = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(x + 6700, y + 550, 1)
    )
    cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
    mesh = ruler.get_component_by_class(unreal.StaticMeshComponent)
    mesh.set_static_mesh(cube)
    mesh.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    ruler.set_actor_scale3d(unreal.Vector(100, 0.20, 0.02))
    ruler.set_actor_label("RD G02 100 m native ruler")
    _, extent = ruler.get_actor_bounds(False)
    if abs(extent.x * 2 - 10000) > 2:
        raise RuntimeError(f"Native ruler failed 100 m scale control: {extent.x * 2}")
    return {"ruler_cm": extent.x * 2, "fixed_viewpoints": ["START", "MID", "END"]}


def exercise_corridor(pawn, player, route, building_point):
    if not isinstance(pawn, unreal.RoadsideCorridorSpectatorPawn):
        raise TypeError("G02 did not possess its 160 cm clearance pawn")
    player.set_control_rotation(unreal.Rotator())

    def point(xy, height):
        return unreal.Vector(xy[0] * 100, xy[1] * 100, height)

    def relocate(xy, height):
        pawn.set_actor_location(point(xy, height), False, True)

    def move(dx, dy, dz, dt=1.0):
        pawn.apply_flight_input(unreal.Vector(dx, dy, dz), dt, False)
        return pawn.get_actor_location()

    trail = route["route_local_m"]
    relocate(trail[0], 500)
    sample = []
    for x, y in trail[1:]:
        position = pawn.get_actor_location()
        dx, dy = x * 100 - position.x, y * 100 - position.y
        distance = math.hypot(dx, dy)
        if distance > 0.01:
            move(dx / distance, dy / distance, 0, distance / 1000.0)
        sample.append(move(0, 0, -1).z)
    end = pawn.get_actor_location()
    endpoint_error = math.hypot(trail[-1][0] * 100 - end.x, trail[-1][1] * 100 - end.y)

    relocate(building_point, 500)
    under_roof = move(0, 0, -1).z
    traverse_start = (building_point[0] - 15.0, building_point[1])
    relocate(traverse_start, 250)
    through = move(1, 0, 0, 3.0).x
    expected_through = (traverse_start[0] + 30) * 100
    rise = move(0, 0, 1, 10).z
    relocate((10000, 10000), 600)
    fallback = move(0, 0, -1).z

    checks = {
        "ordered_route_floor_samples": len(sample),
        "route_floor_range_cm": [min(sample), max(sample)],
        "destination_error_cm": endpoint_error,
        "under_roof_camera_z_cm": under_roof,
        "through_building_x_error_cm": abs(through - expected_through),
        "ascended_camera_z_cm": rise,
        "outside_floor_fallback_cm": fallback,
    }
    if (
        not all(146 <= value <= 162 for value in sample)
        or sum(abs(value - 160) < 2 for value in sample) < len(sample) * 0.7
        or endpoint_error > 3
        or not 146 <= under_roof <= 162
        or abs(through - expected_through) > 3
        or rise < 9000
        or not 146 <= fallback <= 162
    ):
        raise RuntimeError(f"G02 corridor spectator controls failed: {checks}")
    return checks


def verify_input(pawn, player):
    """Drive native input events through PlayerController over real PIE frames."""
    send = pawn.simulate_pie_input
    vector = pawn.get_actor_location

    def clock():
        return unreal.GameplayStatics.get_time_seconds(pawn)

    player.set_control_rotation(unreal.Rotator())
    start = vector()
    normal_started = clock()
    if not send("W", 1):
        raise RuntimeError("PIE key injection is unavailable")
    yield 0.20
    forward = vector().x - start.x
    normal_speed = forward / max(clock() - normal_started, 0.001)
    send("W", 0)
    start = vector()
    send("D", 1)
    yield 0.20
    right = vector().y - start.y
    send("D", 0)
    start = vector()
    send("S", 1)
    yield 0.20
    backward = start.x - vector().x
    send("S", 0)
    start = vector()
    send("A", 1)
    yield 0.20
    left = start.y - vector().y
    send("A", 0)
    start = vector()
    boost_started = clock()
    send("W", 1)
    send("LeftShift", 1)
    yield 0.22
    boosted = vector().x - start.x
    boost_speed = boosted / max(clock() - boost_started, 0.001)
    send("W", 0)
    send("LeftShift", 0)
    initial_z = vector().z
    send("SpaceBar", 1)
    yield 0.22
    up = vector().z - initial_z
    send("SpaceBar", 0)
    initial_z = vector().z
    send("LeftControl", 1)
    yield 0.24
    down = initial_z - vector().z
    send("LeftControl", 0)
    yaw = player.get_control_rotation().yaw
    pitch = player.get_control_rotation().pitch
    send("MouseX", 40)
    send("MouseY", 30)
    yield 0.2
    rotation = player.get_control_rotation()
    wheel_before = pawn.get_flight_speed_cm_per_second()
    send("MouseScrollUp", 1)
    yield 0.15
    wheel_after = pawn.get_flight_speed_cm_per_second()
    send("MouseScrollUp", 0)
    send("MouseScrollDown", 1)
    yield 0.15
    wheel_restored = pawn.get_flight_speed_cm_per_second()
    send("MouseScrollDown", 0)

    checks = {
        "W_forward_cm": forward,
        "D_right_cm": right,
        "S_backward_cm": backward,
        "A_left_cm": left,
        "Shift_boosted_forward_cm": boosted,
        "normal_speed_cm_s": normal_speed,
        "boost_speed_cm_s": boost_speed,
        "Space_ascend_cm": up,
        "Ctrl_descend_cm": down,
        "mouse_yaw_changed": abs(rotation.yaw - yaw) > 0.1,
        "mouse_pitch_changed": abs(rotation.pitch - pitch) > 0.1,
        "wheel_speed_before_cm_s": wheel_before,
        "wheel_speed_after_cm_s": wheel_after,
        "wheel_speed_restored_cm_s": wheel_restored,
    }
    if not (
        min(forward, right, backward, left, up, down) > 10
        and 750 <= normal_speed <= 1250
        and boost_speed > normal_speed * 2
        and checks["mouse_yaw_changed"]
        and checks["mouse_pitch_changed"]
        and wheel_after > wheel_before
        and abs(wheel_restored - wheel_before) < 0.01
    ):
        raise RuntimeError(f"PIE PlayerController controls failed: {checks}")
    return checks


def harvest_viewpoints(actors, harvest):
    views = []
    for name, point in sorted(harvest["landmark_positions_local_m"].items()):
        simplified = name.casefold()
        if not any(
            fragment in simplified
            for fragment in ("stojan", "boska", "боска", "стојан")
        ):
            continue
        x, y = (axis * 100 for axis in point)
        rotation = unreal.Rotator(pitch=-65, yaw=-135)
        view = actors.spawn_actor_from_class(
            unreal.CameraActor, unreal.Vector(x + 5500, y + 5500, 12000), rotation
        )
        if view is None:
            raise RuntimeError(f"Unable to place viewpoint for {name}")
        view.set_actor_label(f"RD G03 {name} viewpoint")
        views.append(name)
    return views
