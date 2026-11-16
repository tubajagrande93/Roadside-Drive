"""Compare actual metric footprints and retain unresolved matches for review."""

from collections import Counter
from math import ceil

from shapely.geometry import Polygon
from shapely.strtree import STRtree

from .features import Feature, height_evidence


def building(feature):
    return (
        "building" in feature.attributes
        and "building:part" not in feature.attributes
        and feature.geometry.geom_type in {"Polygon", "MultiPolygon"}
        and feature.geometry.area >= 8
    )


def associate(osm, overture):
    first = sorted(filter(building, osm), key=lambda feature: feature.identity)
    others = sorted(filter(building, overture), key=lambda feature: feature.identity)
    geometry = [item.geometry for item in first]
    tree = STRtree(geometry)
    links = {}
    supplement = []
    review = []
    for other in others:
        scores = []
        for index in tree.query(other.geometry, predicate="intersects"):
            item = first[index]
            union = item.geometry.union(other.geometry).area
            scores.append(
                (item.geometry.intersection(other.geometry).area / union, item.identity)
            )
        score, identity = max(scores, default=(0, ""))
        other_id = other.identity
        if score >= 0.65:
            if identity not in links or score > links[identity][1]:
                links[identity] = other, score
            else:
                review.append((identity, other_id, round(score, 3)))
        elif score >= 0.15:
            review.append((identity, other_id, round(score, 3)))
        else:
            supplement.append(other)
    return first, links, supplement, review


def station(scope, geometry):
    point = geometry.representative_point()
    along = scope.route.project(point)
    center = scope.route.interpolate(along)
    a = scope.route.interpolate(max(along - 1, 0))
    b = scope.route.interpolate(min(along + 1, scope.route.length))
    cross = (b.x - a.x) * (point.y - center.y) - (b.y - a.y) * (point.x - center.x)
    offset = point.distance(center)
    index = min(int(along // 100), ceil(scope.route.length / 100) - 1)
    return {
        "station": index,
        "side": "LEFT" if cross >= 0 else "RIGHT",
        "along_m": round(along, 3),
        "offset_m": round(offset, 3),
        "priority": "P0" if offset <= 125 else "P1",
    }


def baseline_osm(normal, project_sha):
    """Preserve pre-existing Gate 02 footprint identity even when a tile fails."""
    return [
        Feature(
            "osm:" + row["source_elements"][0],
            Polygon(row["footprint_m"]),
            {**row["raw_tags"], "building": row["raw_tags"].get("building", "yes")},
            "GATE02_OSM",
            project_sha,
            None,
        )
        for row in normal["buildings"]
    ]


def inventory(scope, osm, overture, baseline):
    combined = {item.identity: item for item in baseline}
    combined.update({item.identity: item for item in osm})
    first, links, supplemental, review = associate(combined.values(), overture)
    features = [*first, *supplemental]
    rows = []
    for feature in features:
        other, iou = links.get(feature.identity, (None, None))
        osm_tags = feature.attributes if feature.source != "OVERTURE" else {}
        ov_tags = (
            other.attributes
            if other
            else (feature.attributes if feature.source == "OVERTURE" else {})
        )
        value, basis, confidence = height_evidence(osm_tags, ov_tags)
        rows.append(
            {
                "source_id": feature.identity,
                "overture_id": other.identity if other else None,
                "iou": iou,
                "source_sha256": feature.sha,
                "source_vintage": feature.vintage,
                "geometry_source": feature.source,
                "geometry_crs": "EPSG:32633",
                "footprint_area_m2": round(feature.geometry.area, 3),
                "height_m": value,
                "height_basis": basis,
                "confidence": confidence,
                "height_osm_raw": osm_tags.get("height"),
                "height_overture_raw": ov_tags.get("height"),
                "levels_raw": osm_tags.get("building:levels")
                or ov_tags.get("num_floors"),
                "roof_shape": osm_tags.get("roof:shape") or ov_tags.get("roof_shape"),
                "roof_height_raw": osm_tags.get("roof:height"),
                "facade_status": "PENDING_MANUAL_REVIEW",
                "material_placeholder": True,
                "name": feature.attributes.get("name"),
                "license": "ODbL-1.0",
                "distribution": "LOCAL_DATA_ONLY",
                **station(scope, feature.geometry),
            }
        )
    counts = Counter((item["station"], item["side"]) for item in rows)
    cells = [
        {
            "station": index,
            "side": side,
            "buildings": counts[index, side],
            "status": "COVERED" if counts[index, side] else "NO_SOURCE_FEATURES",
        }
        for index in range(ceil(scope.route.length / 100))
        for side in ("LEFT", "RIGHT")
    ]
    return features, rows, cells, review
