"""Append-only local issue records tied to a sealed ScenePackage object."""

from __future__ import annotations

import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from pydantic import StringConstraints

from .contracts import Contract, Digest, Identifier, canonical
from .exports import confined, validate_scene

Message = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
]


class EditorSelection(Contract):
    object_id: Identifier
    object_source_hash: Digest
    location_world_cm: tuple[float, float, float]
    camera_xyz_cm: tuple[float, float, float]
    camera_yaw_pitch_deg: tuple[float, float]


def report_issue(
    root, scene_path, editor_context, observed, expected, severity, screenshot=None
):
    scene = validate_scene(confined(root, scene_path))
    context = EditorSelection.model_validate_json(
        confined(root, editor_context).read_bytes()
    )
    objects = {item.stable_id: item for item in scene.objects}
    item = objects.get(context.object_id)
    if item is None or context.object_source_hash != item.source_hash:
        raise ValueError("Editor selection is stale or absent from the sealed scene")
    reference = None
    if screenshot:
        file = confined(root, screenshot)
        if (
            confined(root, "output/agentops") not in file.parents
            or not file.is_file()
            or file.suffix.lower() not in {".png", ".jpg", ".jpeg"}
        ):
            raise ValueError("Screenshot must be a local image under output/agentops")
        reference = file.relative_to(root).as_posix()

    from pydantic import TypeAdapter

    message = TypeAdapter(Message)
    stamp = datetime.now(UTC)
    issue = {
        "schema_version": "rd.issue.v1",
        "issue_id": f"G02-{stamp:%Y%m%dT%H%M%SZ}-{uuid4().hex[:12]}",
        "object_id": item.stable_id,
        "object_source_hash": item.source_hash,
        "source_revision": scene.source_sha256,
        "scene_sha256": scene.content_sha256,
        "issue": severity,
        "observed": message.validate_python(observed),
        "expected": message.validate_python(expected),
        "severity": severity,
        "status": "OPEN",
        "created_utc": stamp.isoformat(),
        "location_world_cm": context.location_world_cm,
        "camera": {
            "xyz_cm": context.camera_xyz_cm,
            "yaw_pitch_deg": context.camera_yaw_pitch_deg,
        },
        "screenshot_local_path": reference,
    }
    output = confined(root, "output/agentops/gate02/issues")
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"{issue['issue_id']}.json"
    with tempfile.TemporaryDirectory(prefix=".issue-", dir=output) as scratch:
        path = Path(scratch) / target.name
        path.write_bytes(canonical(issue))
        os.link(path, target)
    return {
        "status": issue["status"],
        "issue_id": issue["issue_id"],
        "path": target.relative_to(root).as_posix(),
    }
