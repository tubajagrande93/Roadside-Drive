"""Build and seal G04A derivatives without editing the approved input package."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from shapely import union_all
from shapely.geometry import mapping

from ..contracts import canonical, digest
from ..exports import G03_LABEL, glb, validate_scene
from ..geometry import triangles
from ..orientation import GEOGRAPHIC_EXCHANGE
from .route_slice import build_slice, camera_stations, station_window
from .surfaces import (
    area_only,
    mapped_pedestrian,
    parent_footprints,
    pedestrian_surfaces,
    solid_faces,
)

SCHEMA = "G04A-Visual200-v1"
ASSETS = "/Game/RoadsideDrive/Generated/G04A"


def document(path):
    return json.loads(path.read_bytes())


def package(base, osm, textures, config, out, root):
    if out.exists() or not out.is_relative_to(root):
        raise ValueError("Use a fresh overlay output within the artifact root")
    scene = validate_scene(base)
    if scene.label != G03_LABEL or scene.exchange_coordinates != GEOGRAPHIC_EXCHANGE:
        raise ValueError("A sealed, signed G03 baseline is required")
    if scene.projected_crs != "EPSG:32633":
        raise ValueError("The visual fixture requires the approved UTM 33N frame")
    rules = document(config)
    start, end = rules["chainage_start_m"], rules["chainage_end_m"]
    if rules["schema_version"] != SCHEMA or (start, end) != (0, 200):
        raise ValueError("This gate covers exactly station 0–200")
    provenance = document(base.with_name("validation.json"))["corridor"]
    route, segment = build_slice(provenance["route_local_m"], start, end)
    window = station_window(segment, rules["station_window_half_width_m"])
    footprints = parent_footprints(base.parent, scene, window.buffer(5))
    roads = [
        (record, geom) for record, geom in footprints.values() if record.kind == "road"
    ]
    asphalt_sources = {}
    for record, shape in roads:
        clipped = area_only(shape.intersection(window))
        if clipped.area > 0.005:
            asphalt_sources[record.stable_id] = (record, clipped)
    asphalt = union_all(
        [shape for _, shape in asphalt_sources.values()], grid_size=0.001
    )
    network = union_all([shape for _, shape in roads], grid_size=0.001)
    ground = union_all(
        [
            shape
            for rec, shape in footprints.values()
            if rec.kind in {"ground", "context"}
        ],
        grid_size=0.001,
    )
    exclusions = {
        key: shape
        for key, (rec, shape) in footprints.items()
        if rec.kind in {"building", "park"}
    }
    paths = {
        key: shape for key, (rec, shape) in footprints.items() if rec.kind == "path"
    }
    mapped, access, kerbs = mapped_pedestrian(root, osm, scene, window)
    exclusions.update(access)
    dimensions = rules["provisional_geometry"]
    sidewalk, walking, curb_by_source = pedestrian_surfaces(
        network,
        window,
        ground,
        exclusions.values(),
        union_all(list(paths.values())),
        mapped,
        kerbs,
        dimensions["sidewalk_width_m"],
        dimensions["curb_width_m"],
    )
    curbs = union_all(list(curb_by_source.values()), grid_size=0.001)
    geometry = {"road_overlay": asphalt, "sidewalks": sidewalk, "curbs": curbs}
    for name, shape in geometry.items():
        if shape.is_empty or shape.difference(window.buffer(0.002)).area > 0.0001:
            raise ValueError(f"{name} is empty or breaches the station window")
        if shape.intersects(route.interpolate(250).buffer(1)):
            raise ValueError(f"{name} is present at the station 250 negative control")
    if (
        sidewalk.intersection(network).area > 0.01
        or curbs.intersection(network).area > 0.01
    ):
        raise ValueError("Pedestrian geometry overlaps the parent road surface")
    texture_manifest = textures / "texture_manifest.json"
    texture_records = document(texture_manifest)
    if (
        texture_records["schema"] != "RD-G04A-PBR-1"
        or len(texture_records["assets"]) != 9
    ):
        raise ValueError("Nine original PBR maps are required")
    for name, item in texture_records["assets"].items():
        if (
            Path(name).name != name
            or digest((textures / name).read_bytes()) != item["sha256"]
        ):
            raise ValueError(f"Texture digest mismatch: {name}")
    chain = list(segment.coords)
    body = {
        "schema": SCHEMA,
        "generator_revision": SCHEMA,
        "parent_scene_sha256": scene.content_sha256,
        "parent_id_count": len(scene.objects),
        "parent_patch_set_sha256": scene.patch_set_sha256,
        "approved_route_sha256": provenance["route_acceptance_sha256"],
        "route_graph_sha256": provenance["graph_sha256"],
        "source_snapshot_sha256": scene.source_sha256,
        "osm_result_sha256": digest(osm.read_bytes()),
        "projected_crs": scene.projected_crs,
        "origin": scene.origin.model_dump(),
        "local_coordinates": "ENU metres",
        "exchange_coordinates": GEOGRAPHIC_EXCHANGE,
        "unreal_coordinates": "X east, Y south, Z up; 100 cm/m",
        "station_start_m": start,
        "station_end_m": end,
        "route_length_m": route.length,
        "segment_local_m": chain,
        "segment_sha256": digest(canonical(chain)),
        "station_window": mapping(window),
        "stations": camera_stations(route),
        "station_250_clear": True,
        "collision_profile": "NoCollision",
        "texture_manifest_sha256": digest(texture_manifest.read_bytes()),
        "mask_ids": sorted(exclusions.keys() | paths.keys()),
        "gap_policy": "Omit sidewalks and curbs at conflict footprints or mapped access openings",
        "surfaces": {},
    }
    assets = {
        "road_overlay": (
            triangles(asphalt, rules["overlay"]["z_bias_cm"] / 100),
            "asphalt",
            4,
        ),
        "sidewalks": (solid_faces(sidewalk, -0.12, 0.115), "paving", 2),
        "curbs": (
            solid_faces(curbs, -0.12, dimensions["curb_height_m"]),
            "concrete",
            1,
        ),
    }
    body["road_sources"] = [
        {
            "id": f"g04a:asphalt:{identity}:0-200",
            "source_geom_id": identity,
            "source_elements": record.source_elements,
            "height_confidence": "FLAT_PROVISIONAL_Z0",
            "start_m": start,
            "end_m": end,
            "area_m2": round(shape.area, 4),
        }
        for identity, (record, shape) in sorted(asphalt_sources.items())
    ]
    body["sidewalk_sources"] = [
        {
            "source_geom_id": identity,
            "confidence": value[1],
            "area_m2": round(value[0].area, 4),
            "start_m": start,
            "end_m": end,
        }
        for identity, value in sorted(walking.items())
    ]
    body["curb_sources"] = [
        {
            "source_geom_id": identity,
            "confidence": "ESTIMATED_NOT_SURVEYED",
            "area_m2": round(shape.area, 4),
            "start_m": start,
            "end_m": end,
        }
        for identity, shape in sorted(curb_by_source.items())
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".g04a-", dir=out.parent) as temp:
        staging = Path(temp) / "ready"
        staging.mkdir()
        for name, (faces, material, metres) in assets.items():
            model = glb(faces, "road", GEOGRAPHIC_EXCHANGE)
            filename = f"{name}.glb"
            (staging / filename).write_bytes(model)
            vertices = list(zip(*(vertex for face in faces for vertex in face)))
            body["surfaces"][name] = {
                "bounds_m": [[func(axis) for axis in vertices] for func in (min, max)],
                "id": f"g04a:{name}:0-200",
                "file": filename,
                "sha256": digest(model),
                "area_m2": round(geometry[name].area, 4),
                "face_count": len(faces),
                "material": f"{ASSETS}/Materials/MI_G04A_{material}",
                "texture_set": material,
                "tile_metres": metres,
                "collision": "NoCollision",
            }
        body["content_sha256"] = digest(canonical(body))
        (staging / "visual_manifest.json").write_bytes(canonical(body))
        staging.rename(out)
    return body
