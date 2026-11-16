"""Bounded semantic Overpass acquisition with immutable raw response evidence."""

import json
import time
from datetime import UTC, datetime

import requests

from ..bounded_overpass import USER_AGENT
from ..contracts import canonical, digest
from ..exports import confined

ENDPOINT = "https://overpass-api.de/api/interpreter"
MIRROR_ENDPOINT = "https://overpass.kumi.systems/api/interpreter"
GROUPS = {
    "buildings": ('["building"]', '["building:part"]'),
    "public_realm": (
        '["leisure"]',
        '["landuse"~"^(grass|forest|recreation_ground|village_green)$"]',
        '["amenity"~"^(place_of_worship|theatre|townhall|marketplace|parking|fountain)$"]',
        '["historic"]',
        '["tourism"~"^(museum|attraction|artwork)$"]',
        '["shop"="mall"]',
    ),
    "street_detail": (
        '["natural"~"^(tree|tree_row|wood|scrub)$"]',
        '["highway"~"^(traffic_signals|crossing|footway|path|pedestrian|cycleway)$"]',
        '["barrier"]',
        '["crossing"]',
        '["junction"="roundabout"]',
        '["amenity"~"^(bench|bicycle_parking|waste_basket)$"]',
    ),
}
MB = 1024 * 1024


def query_plan(scope):
    jobs = []
    for index, tile in enumerate(scope.tiles):
        if tile.geom_type != "Polygon" or tile.is_empty:
            raise ValueError("Expected four nonempty corridor tiles")
        coordinates = " ".join(
            f"{lat:.10f} {lon:.10f}" for lon, lat in list(tile.exterior.coords)[:-1]
        )
        for name, filters in GROUPS.items():
            selector = "".join(f'nwr{tag}(poly:"{coordinates}");' for tag in filters)
            query = f"[out:json][timeout:120][maxsize:26214400];({selector});out body geom qt;"
            jobs.append(
                {"tile": index, "group": name, "bounds": tile.bounds, "query": query}
            )
    return {
        "endpoint": ENDPOINT,
        "query_sha256": digest(canonical(jobs)),
        "jobs": jobs,
        "graph_sha256": scope.report["graph_sha256"],
        "license": "ODbL-1.0",
    }


def download(session, query, limit, endpoint=ENDPOINT):
    with session.post(
        endpoint,
        data={"data": query},
        timeout=(10, 170),
        stream=True,
        allow_redirects=False,
    ) as response:
        if response.status_code != 200:
            after = response.headers.get("Retry-After", "unspecified")
            raise OSError(f"HTTP {response.status_code}, Retry-After {after}")
        raw = bytearray()
        for chunk in response.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > limit:
                raise ValueError("Overpass response exceeded remaining byte limit")
    data = json.loads(raw)
    vintage = data.get("osm3s", {}).get("timestamp_osm_base")
    if data.get("remark") or not vintage or not isinstance(data.get("elements"), list):
        raise ValueError(
            f"Incomplete Overpass result: {data.get('remark', 'missing metadata')}"
        )
    return bytes(raw), len(data["elements"]), vintage


def capture_osm(root, scope, live=False):
    plan = query_plan(scope)
    if not live:
        return {"status": "DRY_RUN", **plan}
    output = confined(root, f"data/raw/g03/osm/{plan['query_sha256']}")
    output.mkdir(parents=True, exist_ok=False)
    (output / "plan.json").write_bytes(canonical(plan))
    records = []
    total = 0
    with requests.Session() as session:
        session.headers["User-Agent"] = USER_AGENT.replace("G02", "G03")
        for index, job in enumerate(plan["jobs"]):
            file = f"{index:02d}-{job['group']}.json"
            record = {"file": file, "captured_utc": datetime.now(UTC).isoformat()}
            try:
                raw, count, vintage = download(
                    session, job["query"], min(25 * MB, 220 * MB - total)
                )
                (output / file).write_bytes(raw)
                total += len(raw)
                record.update(
                    status="OK", sha256=digest(raw), count=count, source_utc=vintage
                )
            except (OSError, ValueError) as error:
                record.update(status="FAILED", error=str(error))
            records.append(record)
            print(f"{index + 1}/12 {file}: {record['status']}", flush=True)
            if index + 1 < len(plan["jobs"]):
                time.sleep(3)
    result = {
        "records": records,
        **plan,
        "bytes": total,
        "location": output.relative_to(root).as_posix(),
        "status": "CAPTURED"
        if all(row["status"] == "OK" for row in records)
        else "PARTIAL",
    }
    (output / "result.json").write_bytes(canonical(result))
    return result


def retry_failed(root, scope, previous_path, mirror=False):
    """New revision for failed slots only; the prior request and bytes remain intact."""
    current = query_plan(scope)
    path = confined(root, previous_path)
    previous = json.loads(path.read_bytes())
    if previous["query_sha256"] != current["query_sha256"]:
        raise ValueError("Retry must use the identical scope and query plan")
    endpoint = MIRROR_ENDPOINT if mirror else ENDPOINT
    target = path.parent.with_name(
        path.parent.name + ("-mirror" if mirror else "-retry")
    )
    target.mkdir(exist_ok=False)
    records = []
    remaining = 220 * MB - previous["bytes"]
    with requests.Session() as session:
        session.headers["User-Agent"] = USER_AGENT.replace("G02", "G03")
        for record, job in zip(previous["records"], current["jobs"], strict=True):
            if record["status"] == "OK":
                raw = confined(path.parent, record["file"]).read_bytes()
                if digest(raw) != record["sha256"]:
                    raise ValueError("Previous capture failed hash verification")
                (target / record["file"]).write_bytes(raw)
            else:
                original = record
                record = {
                    "file": original["file"],
                    "previous_error": original["error"],
                    "captured_utc": datetime.now(UTC).isoformat(),
                }
                try:
                    raw, count, vintage = download(
                        session, job["query"], min(25 * MB, remaining), endpoint
                    )
                    record["endpoint"] = endpoint
                    (target / record["file"]).write_bytes(raw)
                    remaining -= len(raw)
                    record.update(
                        status="OK", sha256=digest(raw), count=count, source_utc=vintage
                    )
                except (OSError, ValueError) as error:
                    record.update(status="FAILED", error=str(error))
                time.sleep(3)
            records.append(record)
    result = {
        **current,
        "records": records,
        "bytes": 220 * MB - remaining,
        "previous_result_sha256": digest(path.read_bytes()),
        "location": target.relative_to(root).as_posix(),
        "status": "CAPTURED"
        if all(row["status"] == "OK" for row in records)
        else "PARTIAL",
    }
    (target / "result.json").write_bytes(canonical(result))
    return result
