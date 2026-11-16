"""Native checks for projected landmark controls on the directed corridor."""

from roadside_drive.world.orientation import camera_right_m, local_to_ue_cm


def audit_landmarks(document, route, actors, scene_sha):
    if (
        document["scene_sha256"] != scene_sha
        or document["graph_sha256"] != route["graph_sha256"]
    ):
        raise RuntimeError(
            "Orientation controls do not match the imported scene and route"
        )
    result = {}
    for item in document["controls"]:
        actor = actors[item["id"]]
        center, extent = actor.get_actor_bounds(False)
        scale = actor.get_actor_scale3d()
        if any(abs(value - 1) > 1e-6 for value in (scale.x, scale.y, scale.z)):
            raise RuntimeError(
                f"Unexpected actor scale in orientation audit: {item['name']}"
            )
        x, y, _ = local_to_ue_cm((*item["point_local_m"], 0))
        if abs(x - center.x) > extent.x + 2 or abs(y - center.y) > extent.y + 2:
            raise RuntimeError(
                f"Source point missing from native bounds: {item['name']}"
            )
        rx, ry, _ = local_to_ue_cm((*item["closest_road_local_m"], 0))
        fx, fy = item["road_forward_enu"]
        sample_x, sample_y = (x, y) if item.get("grouped") else (center.x, center.y)
        from_right = camera_right_m(
            (fx, -fy), ((sample_x - rx) / 100, (sample_y - ry) / 100)
        )
        if (
            abs(from_right) < 1
            or ("LEFT" if from_right < 0 else "RIGHT") != item["side"]
        ):
            raise RuntimeError(
                f"Landmark handedness mismatch: {item['name']} {from_right:.2f}m"
            )
        result[item["name"]] = {
            "id": item["id"],
            "side": item["side"],
            "camera_right_m": round(from_right, 3),
            "native_center_cm": [center.x, center.y, center.z],
            "source_point_within_native_bounds": True,
        }
    return result
