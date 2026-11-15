#!/usr/bin/env python3
"""Repository-local UAOS-B1 operations. See AGENTS.md for startup instructions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime

# Keep read-only commands from writing caches into a fresh checkout.
sys.dont_write_bytecode = True

from agentops_repo import (
    ACTIVE,
    BEGIN,
    END,
    MANIFEST,
    SCHEMA,
    SHA,
    AgentError,
    Repository,
    atomic_write,
    managed_entry,
)
from agentops_route import powerbrain, route
from agentops_state import (
    CHECKPOINT_STATUSES,
    REPORT_STATUSES,
    history_entries,
    record_test,
    state_status,
    write_checkpoint,
    write_report,
)

AGENT_BLOCK = ".agentops/AGENTS.block.md"


def doctor(repo):
    live = repo.snapshot()
    checkpoint = repo.read_checkpoint()
    status = state_status(checkpoint, live)
    issues = []
    config = repo.config
    if config:
        base = config["local_evidence_dir"] + "/handoff"
        latest = f"{base}/LATEST.md"
        current_name = f"{config['context_dir']}/CURRENT_STATE.md"
        current = (
            repo.read(current_name)[0] if repo.path(current_name).is_file() else ""
        )
        evidence = history_entries(repo, base)[:1]
        report_body = evidence[0][2] if evidence else ""
        if evidence and (
            not repo.path(latest).is_file()
            or not repo.read(latest)[0].endswith(report_body)
        ):
            issues.append(
                "LATEST drift; retry the matching report to rebuild pointers from history"
            )
        mode = (
            status
            if status in ACTIVE | {"BLOCKED", "STALE_VERIFY_FIRST"}
            else "NEW_TASK"
        )
        action = (
            None
            if status == "STALE_VERIFY_FIRST"
            else checkpoint["NEXT_EXACT_ACTION"]
            if checkpoint and mode != "NEW_TASK"
            else current.split("# Next exact action\n", 1)[-1].strip()
            if "# Next exact action\n" in current
            else None
        )
    else:
        latest = None
        current = ""
        evidence = []
        mode = "NEW_TASK"
        action = None
    return {
        "fingerprint": live,
        "schema": config.get("schema_version", "NOT_INSTALLED"),
        "paths": {
            key: config.get(key)
            for key in (
                "agent_entry",
                "grand_master_path",
                "checkpoint_path",
                "context_dir",
            )
        },
        "missing": [
            p
            for p in repo.required_files() + [AGENT_BLOCK]
            if not repo.path(p).is_file()
        ]
        if config
        else [MANIFEST],
        "checkpoint_status": status,
        "mode": mode,
        "task_id": checkpoint["TASK_ID"] if checkpoint else None,
        "next_exact_action": action,
        "current_state": current,
        "open_issues": issues,
        "latest_handoff": latest
        if latest and repo.path(latest).is_file()
        else "NOT_PUBLISHED",
        "latest_history": evidence[0][1] if evidence else None,
        "publication": "HANDOFF_NOT_PUBLISHED",
    }


def canonical_files(repo, grand_master):
    result = {grand_master}
    # Scope to root and the indexed manifest. Nearest child docs are scoped to their own projects.
    for path in repo.root.iterdir():
        if (
            path.is_file()
            and re.search(r"grand[_ -]?master.*\.md\Z", path.name, re.IGNORECASE)
            and path.name != grand_master
        ):
            result.add(path.name)
    return sorted(result)


def check_datetime(value):
    try:
        return (
            value.endswith("Z")
            and datetime.fromisoformat(value).utcoffset().total_seconds() == 0
        )
    except (AttributeError, ValueError):
        return False


def verify(repo):
    status = doctor(repo)
    issues = [f"Missing {path}" for path in status["missing"]]
    if issues:
        return {"status": "FAIL", "issues": issues}
    config = repo.config
    entry = repo.path(config["agent_entry"]).read_bytes()
    block = repo.path(AGENT_BLOCK).read_bytes()
    if (
        entry.count(BEGIN) != 1
        or entry.count(END) != 1
        or managed_entry(entry, block) != entry
    ):
        issues.append("Expected one current managed AGENTS block")
    master = config["grand_master_path"]
    if canonical_files(repo, master) != [master]:
        issues.append("Competing root master candidates; identify a single authority")
    document, _ = repo.read(master)
    headings = re.findall(r"^## (GM-\d{3}) ", document, re.MULTILINE)
    if headings != [f"GM-{i:03d}" for i in range(1, 14)]:
        issues.append("Expected ordered GM-001 through GM-013 headings")
    current = status["current_state"]
    metadata = dict(
        re.findall(r"^([A-Z_]+): (.+)$", current.partition("\n\n")[0], re.MULTILINE)
    )
    if (
        metadata.get("CONTEXT_SCHEMA") != SCHEMA
        or not SHA.fullmatch(metadata.get("VERIFIED_SOURCE_SHA", ""))
        or not check_datetime(metadata.get("VERIFIED_UTC", ""))
        or not metadata.get("VERIFIED_SOURCE_REF")
        or metadata.get("VERIFIED_SOURCE_REF") != config.get("last_verified_ref")
        or metadata.get("VERIFIED_SOURCE_SHA") != config.get("last_verified_sha")
        or not metadata.get("CURRENT_TASK_ID")
        or not metadata.get("LATEST_HANDOFF")
        or metadata.get("CURRENT_TASK_STATUS") not in CHECKPOINT_STATUSES
        or metadata.get("OPERATOR_ACCEPTANCE")
        not in {"PENDING", "ACCEPTED", "NOT_APPLICABLE"}
    ):
        issues.append("CURRENT_STATE metadata clashes with the manifest or schema")
    for name in (
        config["checkpoint_path"],
        config["local_evidence_dir"] + "/handoff/LATEST.md",
    ):
        try:
            repo.ensure_local(name)
        except AgentError as error:
            issues.append(str(error))
    index = repo.read(config["context_dir"] + "/GRAND_MASTER_INDEX.md")[0]
    anchors = set(re.findall(r"#(gm-[\w-]+)\)", index))
    master_anchors = {
        re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-")
        for heading in re.findall(r"^## (.+)$", document, re.MULTILINE)
    }
    if not anchors or anchors - master_anchors:
        issues.append("Grand Master index references missing or invalid anchors")
    issues.extend(status["open_issues"])
    return {
        "status": "FAIL" if issues else "PASS",
        "issues": issues,
        "checkpoint_freshness": status["checkpoint_status"],
        "source": status["fingerprint"],
    }


def bootstrap(repo, apply):
    repo.require_config()
    config = repo.config
    entry_path = repo.path(config["agent_entry"])
    if len(canonical_files(repo, config["grand_master_path"])) != 1:
        raise AgentError("Resolve competing root masters before modifying the entry")
    # The project-aware files are supplied by installation/checkout. Only reconcile managed entry.
    other_files = [
        p
        for p in repo.required_files() + [AGENT_BLOCK]
        if p != config["agent_entry"] and not repo.path(p).is_file()
    ]
    if other_files:
        return {
            "status": "INSTALL_INPUT_REQUIRED",
            "missing": other_files,
            "changes": [],
        }
    original = entry_path.read_bytes() if entry_path.is_file() else b""
    block = repo.path(AGENT_BLOCK).read_bytes()
    modified = managed_entry(original, block)
    changes = [config["agent_entry"]] if original != modified else []
    if apply and changes:
        atomic_write(entry_path, modified)
    status = (
        "APPLIED" if apply and changes else "CHANGES_PLANNED" if changes else "NO_OP"
    )
    return {"status": status, "changes": changes}


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument(
        "--root", default=".", help="Starting directory (default current directory)"
    )
    commands = cli.add_subparsers(dest="operation", required=True)
    for name, description in (
        ("doctor", "show source, project wiring and local continuity"),
        ("route", "find bounded source candidates without mutation"),
        ("powerbrain", "write an evidence-backed task brief"),
        ("checkpoint", "save atomic local task state"),
        ("report", "queue and index an immutable factual handoff"),
        (
            "record-test",
            "execute a local test command and record exact source and exit",
        ),
        ("verify", "validate the installed infrastructure and local exclusions"),
        ("bootstrap", "check or reconcile the managed entry of a provisioned project"),
    ):
        sub = commands.add_parser(name, help=description, description=description)
        sub.add_argument(
            "--json", action="store_true", help="emit machine-readable JSON"
        )
        if name in {"route", "powerbrain"}:
            sub.add_argument("--task", required=True)
        if name == "powerbrain":
            sub.add_argument("--out", required=True)
        if name in {"checkpoint", "report"}:
            sub.add_argument("--task-id", required=True)
            statuses = CHECKPOINT_STATUSES if name == "checkpoint" else REPORT_STATUSES
            sub.add_argument("--status", choices=statuses, required=True)
            sub.add_argument(
                "--next", required=True, help="one exact continuation action"
            )
        if name == "checkpoint":
            sub.add_argument(
                "--set",
                action="append",
                default=[],
                metavar="FIELD=VALUE",
                help="set a supported detail field (scope, workstreams, gates, delivery)",
            )
            sub.add_argument(
                "--evidence", action="append", default=[], help="record-test JSON path"
            )
            sub.add_argument(
                "--refresh-source", action="store_true", help="acknowledge stale source"
            )
            sub.add_argument(
                "--replace-task", action="store_true", help="start a different task"
            )
            sub.add_argument(
                "--changed",
                action="append",
                default=[],
                metavar="REPO_PATH",
                help="record an exact changed path, including committed changes",
            )
            sub.add_argument(
                "--reopen", action="append", default=[], help="reopen an affected gate"
            )
            sub.add_argument(
                "--close-gate", action="append", default=[], metavar="ID=DIVERGENCE"
            )
        if name == "record-test":
            sub.add_argument("--gate", required=True)
            sub.add_argument(
                "--timeout",
                type=int,
                choices=range(1, 301),
                default=45,
                metavar="1..300",
            )
            sub.add_argument("command", nargs=argparse.REMAINDER)
        if name == "bootstrap":
            modes = sub.add_mutually_exclusive_group(required=True)
            modes.add_argument("--dry-run", action="store_true")
            modes.add_argument(
                "--apply", action="store_true", help="update managed entry only"
            )
    return cli


def run(args):
    repo = Repository(args.root)
    actions = {
        "doctor": lambda: doctor(repo),
        "route": lambda: route(repo, args.task),
        "powerbrain": lambda: powerbrain(repo, args.task, args.out),
        "checkpoint": lambda: write_checkpoint(repo, args),
        "report": lambda: write_report(repo, args),
        "verify": lambda: verify(repo),
        "bootstrap": lambda: bootstrap(repo, args.apply),
    }
    if args.operation == "record-test":
        return record_test(repo, args)
    result = actions[args.operation]()
    fail = result.get("status") in {"FAIL", "INSTALL_INPUT_REQUIRED"}
    return result, int(fail)


def main():
    args = parser().parse_args()
    try:
        result, code = run(args)
    except (AgentError, OSError, ValueError, TypeError) as error:
        if args.json:
            print(
                json.dumps({"status": "ERROR", "error": str(error)}, ensure_ascii=False)
            )
        else:
            print(f"agentops: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            rendered = (
                json.dumps(value, ensure_ascii=False)
                if not isinstance(value, str)
                else value
            )
            print(f"{key.upper()}: {rendered}")
    return code if code >= 0 else 128 - code


if __name__ == "__main__":
    sys.exit(main())
