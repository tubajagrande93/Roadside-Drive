"""Clone a verified disposable G03 project and build/reopen G04A in UE 5.7."""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = "/Game/RoadsideDrive/Levels/L_RD_G03_Corridor"
LEVEL = "/Game/RoadsideDrive/Levels/L_RD_G04A_Visual200"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "engine",
        "source-project",
        "parent-scene",
        "orientation",
        "overlay",
        "textures",
        "output",
    ):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=420)
    args = parser.parse_args()
    source = args.source_project.resolve(strict=True)
    if not (source / ".roadside-g01-disposable").is_file():
        raise ValueError("Use the verified disposable G03 project as the parent")
    engine = args.engine.resolve(strict=True) / "Engine/Binaries/Mac"
    editor = engine / "UnrealEditor-Cmd"
    if not editor.is_file():
        editor = engine / "UnrealEditor.app/Contents/MacOS/UnrealEditor"
    output = args.output.resolve()
    if output.is_relative_to(source):
        raise ValueError("The output must be outside the G03 project")
    output.mkdir(parents=True, exist_ok=False)
    project = output / "project"
    project.mkdir()
    for name in ("Config", "Source", "Content", "Binaries"):
        shutil.copytree(source / name, project / name)
    shutil.copy2(source / "RoadsideDrive.uproject", project)
    (project / ".roadside-g04a-disposable").touch(exist_ok=False)
    native = {
        "PROJECT": project,
        "BUILD_EVIDENCE": output / "build.json",
        "PARENT_SCENE": args.parent_scene.resolve(strict=True),
        "G03_ORIENTATION": args.orientation.resolve(strict=True),
        "OVERLAY": args.overlay.resolve(strict=True),
        "TEXTURES": args.textures.resolve(strict=True),
    }
    env = {
        **os.environ,
        **{f"RD_G04A_{key}": str(value) for key, value in native.items()},
    }
    for phase, map_path, script, evidence in (
        ("build", PARENT, "g04a_preview.py", native["BUILD_EVIDENCE"]),
        (
            "reopen",
            LEVEL,
            "g04a_review.py",
            project / "Saved/RoadsideG04AReview/review.json",
        ),
    ):
        command = [
            str(editor),
            str(project / "RoadsideDrive.uproject"),
            map_path,
            f"-ExecutePythonScript={HERE / script}",
            "-unattended",
            "-ini:Engine:[ConsoleVariables]:Engine.Python.ForceWrapperGenerationOnSingleThread=1",
            "-nosound",
            "-nop4",
            "-NoSplash",
            "-NoAnalytics",
            "-notraceserver",
            "-NoCrashReporter",
            f"-abslog={output / f'{phase}.log'}",
            f"-UserDir={project}",
        ]
        (output / f"{phase}-invocation.json").write_text(json.dumps(command, indent=2))
        with (output / f"{phase}-process.log").open("wb") as log:
            run = subprocess.run(
                command,
                check=False,
                env=env,
                stdout=log,
                stderr=log,
                timeout=args.timeout,
            )
        if run.returncode or not evidence.is_file():
            raise RuntimeError(
                f"G04A {phase} failed. Inspect {output / f'{phase}.log'}"
            )
        result = json.loads(evidence.read_text())
        if phase == "reopen" and (
            result["status"] != "NATIVE_REOPEN_AND_RENDER_PASS"
            or result["runtime_spectator"] != "PASS"
        ):
            raise RuntimeError(f"G04A reopen or PIE failed. Inspect {evidence}")
        print(f"{phase}: {result['status']} ({evidence})", flush=True)


if __name__ == "__main__":
    main()
