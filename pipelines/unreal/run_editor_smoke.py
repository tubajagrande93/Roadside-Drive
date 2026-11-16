#!/usr/bin/env python3
"""Run Unreal automation in an empty copy of the project and preserve native logs."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=150)
    parser.add_argument("--mode", choices=("probe", "import"), default="probe")
    args = parser.parse_args()
    source = ROOT / "apps/unreal/RoadsideDrive"
    engine = args.engine.resolve(strict=True) / "Engine"
    executable = engine / "Binaries/Mac/UnrealEditor-Cmd"
    scene = args.scene.resolve(strict=True)
    output = args.output.absolute()
    boundary = ROOT / "data/processed/world_builder"
    if (
        boundary not in output.parents
        or output.resolve() != output
        or ".." in args.output.parts
    ):
        parser.error(
            "output must be a new confined directory under the generated World Builder tree"
        )

    if not executable.is_file() or output.exists() or output.is_symlink():
        parser.error(
            "require an UnrealEditor-Cmd and a new disposable output directory"
        )
    if not 1 <= args.timeout <= 300:
        parser.error("timeout must be between 1 and 300 seconds")
    if output.parent.is_symlink():
        parser.error("output parent must be a real directory")
    output.mkdir(parents=True)
    project = output / "project"
    project.mkdir()
    shutil.copytree(source / "Config", project / "Config")
    template = json.loads((source / "RoadsideDrive.uproject").read_bytes())
    for name in ("PythonScriptPlugin", "EditorScriptingUtilities"):
        entries = [item for item in template["Plugins"] if item["Name"] == name]
        if not entries:
            template["Plugins"].append(
                {"Name": name, "Enabled": True, "TargetAllowList": ["Editor"]}
            )
        elif not entries[0]["Enabled"]:
            parser.error(f"Existing project has {name} disabled")
    descriptor = project / "RoadsideDrive.uproject"
    descriptor.write_text(json.dumps(template, indent=2), encoding="utf-8")
    (project / ".roadside-g01-disposable").touch()
    evidence = output / "native.json"
    env = {
        **os.environ,
        "RD_G01_MODE": args.mode,
        "RD_G01_DISPOSABLE_PROJECT": str(project),
        "RD_G01_SCENE": str(scene),
        "RD_G01_NATIVE_EVIDENCE": str(evidence),
        "UE-LocalDataCachePath": str(output / "DDC"),
        "UE-SharedDataCachePath": "None",
    }
    script = Path(__file__).with_name("import_world.py")
    argv = [
        str(executable),
        str(descriptor),
        *(
            [f"-ExecutePythonScript={script}"]
            if args.mode == "import"
            else ["-run=pythonscript", f"-script={script}"]
        ),
        "-unattended",
        "-nullrhi",
        "-nosound",
        "-nop4",
        "-NoSplash",
        "-NoAnalytics",
        "-notraceserver",
        "-NoCrashReporter",
        f"-abslog={output / 'unreal.log'}",
        f"-UserDir={output / 'user'}",
    ]
    (output / "invocation.json").write_text(json.dumps(argv), encoding="utf-8")
    timed_out = False
    with (
        (output / "process.log").open("wb") as log,
        subprocess.Popen(
            argv,
            cwd=project,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        ) as process,
    ):
        try:
            rc = process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            rc = process.wait()
    observed = json.loads(evidence.read_bytes()) if evidence.is_file() else None
    status = {
        "process_exit": rc,
        "timeout": timed_out,
        "native": observed,
        "result": "OBSERVED" if observed else "NOT_EXECUTED",
    }
    (output / "summary.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status))
    required = "NATIVE_API_PASS" if args.mode == "probe" else "NATIVE_IMPORT_PASS"
    if rc or not observed or observed["status"] != required:
        return 1
    if args.mode == "import" and (
        observed["collision_trace"] != "PASS" or not observed["level_file_present"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
