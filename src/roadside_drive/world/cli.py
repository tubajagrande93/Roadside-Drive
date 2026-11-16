"""Operator CLI. Exit 2 on invalid input, conflicts or missing OSM GO."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from pyproj.exceptions import ProjError
from shapely.errors import ShapelyError

from .contracts import canonical, digest
from .exports import build_fixture, confined, fresh_generated_path, validate_scene
from .normalize import normalized_capture
from .osm_adapter import ingest_osm, proposal


def parser():
    interface = argparse.ArgumentParser(description=__doc__)
    command = interface.add_subparsers(dest="command", required=True)
    command.add_parser("doctor")
    build = command.add_parser("build-fixture")
    build.add_argument("--config", required=True)
    build.add_argument("--output", required=True)
    build.add_argument("--patches")
    for name in ("validate", "export"):
        verify = command.add_parser(name)
        verify.add_argument("--scene", required=True)
        if name == "export":
            verify.add_argument("--output", required=True)
    normal = command.add_parser("normalize-capture")
    normal.add_argument("--capture", required=True)
    normal.add_argument("--output", required=True)
    for name in ("prepare-aoi", "ingest-osm"):
        data = command.add_parser(name)
        data.add_argument("--config", required=True)
        if name == "ingest-osm":
            data.add_argument("--approval")
            data.add_argument("--allow-network", action="store_true")
    return interface


def run(root, args):
    if args.command == "doctor":
        return {
            "status": "READY_OFFLINE",
            "units": "metres and Unreal centimetres",
            "native_qa": "NOT_EXECUTED",
            "live_osm": "OSM_GO_REQUIRED",
        }
    if args.command == "prepare-aoi":
        return proposal(root, args.config)[1]
    if args.command == "ingest-osm":
        return ingest_osm(root, args.config, args.approval, args.allow_network)
    if args.command == "normalize-capture":
        source = normalized_capture(root, args.capture)
        target = fresh_generated_path(root, args.output)
        if target.suffix != ".json":
            raise ValueError("Normalized capture output must be a new .json file")
        data = canonical(source.model_dump(mode="json"))
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=".normalize-", dir=target.parent
        ) as scratch:
            candidate = Path(scratch) / target.name
            candidate.write_bytes(data)
            os.link(candidate, target)
        return {
            "status": "NORMALIZED_REQUIRES_QA",
            "sha256": digest(data),
            "feature_counts": {
                "road": len(source.roads),
                "building": len(source.buildings),
            },
        }
    if args.command == "build-fixture":
        scene = build_fixture(root, args.config, args.output, args.patches)
    else:
        manifest = confined(root, args.scene)
        scene = validate_scene(manifest)
        if args.command == "export":
            target = fresh_generated_path(root, args.output)
            if target.exists():
                raise ValueError("Export target already exists")
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(
                prefix=".export-", dir=target.parent
            ) as scratch:
                staged = Path(scratch) / "package"
                shutil.copytree(manifest.parent, staged)
                validate_scene(staged / manifest.name)
                staged.rename(target)
    return {
        "status": "PASS",
        "sha256": scene.content_sha256,
        "objects": scene.generated_object_counts,
        "label": scene.label,
        "native_qa": scene.import_status,
    }


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        print(json.dumps(run(Path.cwd(), args), ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError, TypeError, KeyError, ProjError, ShapelyError) as error:
        print(f"World Builder: {error}", file=sys.stderr)
        return 2
    return 0
