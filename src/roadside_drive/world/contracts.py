"""Versioned source and correction contracts."""

from __future__ import annotations

import hashlib
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Identifier = Annotated[
    str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_:-]{0,79}$")
]
Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
XY = tuple[float, float]
Positive = Annotated[float, Field(gt=0)]
Confidence = Literal["VERIFIED", "ESTIMATED", "PLACEHOLDER"]


def canonical(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Origin(Contract):
    east_m: float
    north_m: float
    z_m: float


class Provenance(Contract):
    title: str
    dataset_kind: Literal["SYNTHETIC", "OSM"]
    source_uri: str
    license_id: str
    attribution: str
    captured_utc: str | None = None
    derivative_status: Literal["SYNTHETIC", "SOURCE", "DERIVED"]
    forbidden_source: bool = False


class Feature(Contract):
    stable_id: Identifier
    source_elements: Annotated[tuple[str, ...], Field(min_length=1)]
    raw_tags: dict[str, str] = Field(default_factory=dict)
    confidence: Confidence

    def source_hash(self):
        return digest(canonical(self.model_dump(mode="json")))


class RoadFeature(Feature):
    kind: Literal["road"] = "road"
    centerline_m: Annotated[tuple[XY, ...], Field(min_length=2)]
    width_m: Positive
    width_basis: str
    highway_class: str | None = None
    oneway: bool | None = None
    lanes: Annotated[int, Field(gt=0)] | None = None


class BuildingFeature(Feature):
    kind: Literal["building"] = "building"
    footprint_m: Annotated[tuple[XY, ...], Field(min_length=3)]
    height_m: Positive | None
    height_basis: str


class Source(Contract):
    schema_version: Literal[1]
    world_id: Identifier
    source_crs: str
    projected_crs: str
    origin: Origin
    provenance: Provenance
    roads: Annotated[tuple[RoadFeature, ...], Field(min_length=1)]
    buildings: tuple[BuildingFeature, ...]

    @model_validator(mode="after")
    def check_source(self):
        ids = [feature.stable_id for feature in (*self.roads, *self.buildings)]
        if len(set(ids)) != len(ids) or "ground" in ids:
            raise ValueError("Source IDs must be unique and ground is reserved")
        if self.provenance.forbidden_source:
            raise ValueError("Source is outside the approved provenance boundary")
        return self


class CorrectionPatch(Contract):
    schema_version: Literal[1]
    patch_id: Identifier
    target_stable_id: Identifier
    expected_source_hash: Digest
    field: Literal["width_m", "height_m", "centerline_m", "footprint_m"]
    expected_previous_value: float | list[XY] | None
    new_value: float | list[XY] | None
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    reference: str = ""
    operator_created_utc: str
    author_ref: str
    status: Literal["ACTIVE", "CONFLICT", "SUPERSEDED"] = "ACTIVE"


class ObjectRecord(Contract):
    stable_id: Identifier
    kind: Literal[
        "road", "building", "ground", "park", "path", "vegetation", "street", "context"
    ]
    source_elements: tuple[str, ...]
    source_hash: Digest
    file: str
    sha256: Digest
    bounds_m: tuple[tuple[float, float, float], tuple[float, float, float]]
    face_count: Annotated[int, Field(gt=0)]
    confidence: Confidence
    visual_height_m: Positive | None = None
    height_basis: str | None = None
    material_category: str
    collision: Literal["NATIVE_VALIDATION_REQUIRED"] = "NATIVE_VALIDATION_REQUIRED"


class SceneManifest(Contract):
    schema_version: Literal[1]
    build_tool_version: Literal["0.1"]
    world_id: Identifier
    label: str
    provenance: Provenance
    source_crs: str
    projected_crs: str
    origin: Origin
    elevation_status: Literal["FLAT_PROVISIONAL_Z0"]
    unreal_units_per_meter: Literal[100]
    exchange_coordinates: Literal[
        "glTF metres: X east, Y up, Z north", "glTF metres: X east, Y up, Z south"
    ]
    source_sha256: Digest
    normalized_sha256: Digest
    patch_set_sha256: Digest
    normalized_file_sha256: Digest
    catalog_sha256: Digest
    validation_sha256: Digest
    source_feature_counts: dict[str, int]
    generated_object_counts: dict[str, int]
    confidence_summary: dict[Confidence, int]
    aoi_geometry_wgs84: tuple[XY, ...] | None = None
    aoi_approval_status: Literal["NOT_APPLICABLE", "AOI_NOT_APPROVED", "APPROVED"]
    import_status: Literal["NOT_EXECUTED"]
    objects: tuple[ObjectRecord, ...]
    content_sha256: Digest


def apply_corrections(source, patches):
    """Replay active patches from the pristine source or fail without modifying it."""
    ids = [p.patch_id for p in patches]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate correction patch ID")
    originals = {f.stable_id: f for f in (*source.roads, *source.buildings)}
    result = dict(originals)
    for patch in patches:
        if patch.status == "SUPERSEDED":
            continue
        if patch.status != "ACTIVE":
            raise ValueError(f"Correction {patch.patch_id} is in conflict")
        initial = originals.get(patch.target_stable_id)
        if initial is None or initial.source_hash() != patch.expected_source_hash:
            raise ValueError(
                f"Correction {patch.patch_id} has unknown target or stale source hash"
            )
        current = result[patch.target_stable_id]
        data = current.model_dump(mode="json")
        if patch.field not in data or canonical(data[patch.field]) != canonical(
            patch.expected_previous_value
        ):
            raise ValueError(
                f"Correction {patch.patch_id} has a stale value or invalid field"
            )
        data[patch.field] = patch.new_value
        result[patch.target_stable_id] = type(current).model_validate(data)
    features = [result[k] for k in sorted(result)]
    return [f for f in features if isinstance(f, RoadFeature)], [
        f for f in features if isinstance(f, BuildingFeature)
    ]
