"""Run the Gate 03 harvest or reproduce its derived ScenePackage."""

import argparse
import json
from pathlib import Path

from .osm import capture_osm, retry_failed
from .overture import capture_overture
from .package import enrich
from .scope import approved_scope


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--approval", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    osm = commands.add_parser("osm")
    mode = osm.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--retry")
    osm.add_argument("--mirror", action="store_true")
    overture = commands.add_parser("overture")
    overture.add_argument("--cli", required=True)
    build = commands.add_parser("build")
    build.add_argument("--base", required=True)
    build.add_argument("--osm", required=True)
    build.add_argument("--overture", required=True)
    build.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path.cwd()
    scope = approved_scope(root, args.capture, args.review, args.approval)
    if args.command == "osm":
        if args.mirror and not args.retry:
            parser.error("--mirror requires --retry")
        result = (
            retry_failed(root, scope, args.retry, args.mirror)
            if args.retry
            else capture_osm(root, scope, args.live)
        )
    elif args.command == "overture":
        result = capture_overture(root, scope, args.cli)
    else:
        result = enrich(root, scope, args.base, args.osm, args.overture, args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
