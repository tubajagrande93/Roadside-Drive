"""Prepare geodetic controls for the verified Banja Luka Gate 03 snapshot."""

import argparse
import json
from io import BytesIO
from pathlib import Path

import trimesh
from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon

from roadside_drive.world.contracts import canonical
from roadside_drive.world.exports import validate_scene
from roadside_drive.world.harvest.features import read_artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--osm", type=Path, required=True)
    parser.add_argument("--legacy-evidence", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    scene = validate_scene(args.scene)
    artifacts = {record.stable_id: record for record in scene.objects}
    data = json.loads(args.scene.with_name("validation.json").read_bytes())
    route = LineString(data["corridor"]["route_local_m"])
    harvest = data["harvest"]
    controls = []

    def add(name, record, point, side, *, grouped=False):
        length = route.project(point)
        center = route.interpolate(length)
        a = route.interpolate(max(0, length - 2))
        b = route.interpolate(min(route.length, length + 2))
        dx, dy = b.x - a.x, b.y - a.y
        signed_m = (dx * (point.y - center.y) - dy * (point.x - center.x)) / a.distance(
            b
        )
        measured_side = "LEFT" if signed_m > 0 else "RIGHT"
        if measured_side != side or abs(signed_m) < 1:
            raise ValueError(f"{name}: unexpected geodetic side {measured_side}")
        (west, south, _), (east, north, _) = record.bounds_m
        if not (west <= point.x <= east and south <= point.y <= north):
            raise ValueError(f"{name}: source point missing from geometry envelope")
        controls.append(
            {
                "name": name,
                "id": record.stable_id,
                "point_local_m": [point.x, point.y],
                "closest_road_local_m": [center.x, center.y],
                "road_forward_enu": [dx, dy],
                "side": side,
                "source_left_m": round(signed_m, 3),
                "grouped": grouped,
            }
        )

    for name in ("Park Mladen Stojanović", "Boska", "Hram Hrista Spasitelja"):
        key = next(key for key, label in harvest["labels"].items() if label == name)
        add(
            name,
            artifacts[key],
            Point(harvest["landmark_positions_local_m"][name]),
            "LEFT",
        )

    right_control = next(
        item
        for item in scene.objects
        if item.kind == "building" and "way/1349089233" in item.source_elements
    )
    project = Transformer.from_crs(4326, scene.projected_crs, always_xy=True).transform
    east0, north0 = scene.origin.east_m, scene.origin.north_m

    def local(lon, lat):
        east, north = project(lon, lat)
        return east - east0, north - north0

    add(
        "Right-side building way/1349089233",
        right_control,
        Point(
            local(
                *data["corridor"]["object_source_centers_wgs84"][
                    right_control.stable_id
                ]
            )
        ),
        "RIGHT",
    )

    manifest = json.loads(args.osm.read_bytes())
    road_source = None
    for job, record in zip(manifest["jobs"], manifest["records"], strict=True):
        if job["group"] != "street_detail" or record["status"] != "OK":
            continue
        capture = read_artifact(Path.cwd(), args.osm.parent, record)
        for item in capture["elements"]:
            if (
                item["type"] == "way"
                and item["id"] == 693116547
                and item["tags"].get("alt_name") == "Gospodska"
            ):
                road_source = item
                break
        if road_source:
            break
    if road_source is None:
        raise ValueError("The captured Gospodska control way is missing")
    path = next(
        item for item in scene.objects if "osm:way/693116547" in item.source_elements
    )
    line = LineString(
        [local(item["lon"], item["lat"]) for item in road_source["geometry"]]
    )
    add(
        "Gospodska / Veselina Masleše",
        path,
        line.interpolate(0.5, normalized=True),
        "LEFT",
        grouped=True,
    )

    # The named pedestrian way is batched by station. Validate its real
    # centerline in the generated mesh, independently of the group AABB.
    sample = line.interpolate(0.5, normalized=True)
    mesh = trimesh.load(
        BytesIO((args.scene.parent / path.file).read_bytes()),
        file_type="glb",
        force="mesh",
        process=False,
    )
    if not any(
        Polygon([(x, -z) for x, _, z in triangle]).buffer(0.02).covers(sample)
        for triangle in mesh.triangles
    ):
        raise ValueError("Gospodska centerline is missing from the generated path mesh")
    controls[-1]["source_point_in_export_triangles"] = True

    normalized = json.loads(args.scene.with_name("normalized.json").read_bytes())
    parallel = next(
        item
        for item in normalized["roads"]
        if "way/785905277" in item["source_elements"]
        and item["raw_tags"]["corridor_role"] == "PARALLEL_NAMED_WAY_CANDIDATE"
    )
    parallel_line = LineString(
        [(x - east0, y - north0) for x, y in parallel["centerline_m"]]
    )
    add(
        "START parallel road way/785905277",
        artifacts[parallel["stable_id"]],
        parallel_line.interpolate(0.5, normalized=True),
        "LEFT",
        grouped=True,
    )

    document = {
        "scene_sha256": scene.content_sha256,
        "graph_sha256": data["corridor"]["graph_sha256"],
        "controls": controls,
    }
    if args.legacy_evidence:
        legacy = json.loads(args.legacy_evidence.read_bytes())
        natives = {item["id"]: item["bounds_cm"] for item in legacy["records"]}
        before = {}
        for row in controls:
            bounds = natives[row["id"]]
            x, y = (
                row["point_local_m"]
                if row["grouped"]
                else (
                    (bounds[0][0] + bounds[1][0]) / 200,
                    (bounds[0][1] + bounds[1][1]) / 200,
                )
            )
            if row["grouped"] and not all(
                low - 2 <= value * 100 <= high + 2
                for value, low, high in zip(
                    (x, y), bounds[0][:2], bounds[1][:2], strict=True
                )
            ):
                raise ValueError("Source point outside the legacy native group bounds")
            rx, ry = row["closest_road_local_m"]
            fx, fy = row["road_forward_enu"]
            side = (-fy * (x - rx) + fx * (y - ry)) / (fx * fx + fy * fy) ** 0.5
            before[row["name"]] = round(side, 3)
            if abs(side) < 1 or ("LEFT" if side < 0 else "RIGHT") == row["side"]:
                raise ValueError(
                    "The legacy native positions did not reproduce the mirrored side"
                )
        document["legacy_native_camera_right_m"] = before
    with args.output.open("xb") as target:
        target.write(canonical(document))


if __name__ == "__main__":
    main()
