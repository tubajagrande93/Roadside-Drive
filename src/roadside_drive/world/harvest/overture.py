"""Acquire three bbox-scoped Overture themes with a release pinned from STAC."""

import json
import re
import subprocess
from datetime import UTC, datetime

import requests
from shapely.ops import unary_union

from ..contracts import canonical, digest
from ..exports import confined

CATALOG = "https://stac.overturemaps.org/catalog.json"
TYPES = {
    "building": "ODbL-1.0",
    "building_part": "ODbL-1.0",
    "place": "CDLA-Permissive-2.0",
}


def capture_overture(root, scope, cli):
    response = requests.get(CATALOG, timeout=30)
    response.raise_for_status()
    release = response.json()["latest"]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}\.\d+", release):
        raise ValueError("Unexpected Overture release identifier")
    bbox = tuple(round(axis, 7) for axis in unary_union(scope.tiles).bounds)
    identity = {"catalog": CATALOG, "release": release, "bbox": bbox, "types": TYPES}
    target = confined(root, f"data/raw/g03/overture/{digest(canonical(identity))}")
    target.mkdir(parents=True, exist_ok=False)
    (target / "catalog.json").write_bytes(response.content)
    records = {}
    for kind, license_id in TYPES.items():
        output = target / f"{kind}.geojson"
        arguments = [
            "download",
            "--bbox=" + ",".join(map(str, bbox)),
            "--release",
            release,
            "--type",
            kind,
            "-f",
            "geojson",
            "-o",
            str(output),
            "--connect_timeout",
            "15",
            "--request_timeout",
            "35",
        ]
        record = {"license": license_id, "captured_utc": datetime.now(UTC).isoformat()}
        try:
            result = subprocess.run(
                [str(cli), *arguments], capture_output=True, timeout=300, check=False
            )
            (target / f"{kind}.log").write_bytes(result.stderr)
            result.check_returncode()
            if not output.is_file() or output.stat().st_size > 25 * 1024 * 1024:
                raise ValueError("Missing or over-limit Overture output")
            data = output.read_bytes()
            features = json.loads(data)["features"]
            record.update(
                status="OK", count=len(features), sha256=digest(data), file=output.name
            )
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
            record.update(status="FAILED", error=type(error).__name__)
        records[kind] = record
        print(
            f"Overture {release} {kind}: {record['status']} {record.get('count', '')}",
            flush=True,
        )
    result = {
        **identity,
        "records": records,
        "catalog_sha256": digest(response.content),
    }
    (target / "result.json").write_bytes(canonical(result))
    return result
