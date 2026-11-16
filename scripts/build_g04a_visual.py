"""Generate the bounded G04A overlay from a verified signed G03 package."""

import argparse
from pathlib import Path

from roadside_drive.world.visual.export import package

parser = argparse.ArgumentParser(description=__doc__)
for name in ("root", "base", "osm", "textures", "config", "output"):
    parser.add_argument(f"--{name}", required=True, type=Path)
args = parser.parse_args()
result = package(
    *(
        getattr(args, key).resolve()
        for key in (
            "base",
            "osm",
            "textures",
            "config",
            "output",
            "root",
        )
    )
)
print(result["content_sha256"])
