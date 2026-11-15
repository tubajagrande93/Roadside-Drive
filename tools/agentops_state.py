"""Checkpoint state, executed evidence and serialized local handoffs."""

from __future__ import annotations

import json
import re
import shlex
import uuid
from datetime import datetime

from agentops_repo import (
    ACTIVE,
    SCHEMA,
    SHA,
    AgentError,
    atomic_write,
    bounded_run,
    utc,
    validate_text,
)

CHECKPOINT_STATUSES = (
    "IDLE",
    "ACTIVE",
    "INTERRUPTED",
    "PARTIAL",
    "COMPLETE",
    "BLOCKED",
)
REPORT_STATUSES = (
    "COMPLETE_VERIFIED",
    "PARTIAL",
    "INTERRUPTED",
    "BLOCKED",
    "CHECKPOINT",
)
TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
HISTORY = re.compile(r"[0-9]{8}T[0-9]{6}Z_[A-Za-z0-9_-]+\.md\Z")
PUBLICATION = "HANDOFF_NOT_PUBLISHED"
DEFAULTS = {
    "TASK_TITLE": None,
    "OPERATOR_AUTHORIZATION": "UNKNOWN",
    "WORKSTREAMS_COMPLETE": "NONE",
    "WORKSTREAMS_PARTIAL": "NONE",
    "WORKSTREAMS_NOT_STARTED": "UNKNOWN",
    "TESTS_NOT_EXECUTED": "UNKNOWN",
    "KNOWN_FAILURES": "NONE_RECORDED",
    "LATEST_SOURCE_DELIVERY": "NONE",
    "PRESERVATION": "Pending explicit comparison",
    "LOCAL_EVIDENCE": "NONE",
}
REQUIRED = {
    *DEFAULTS,
    "CHECKPOINT_SCHEMA",
    "TASK_ID",
    "STATUS",
    "BASELINE_BRANCH",
    "BASELINE_SHA",
    "CURRENT_BRANCH",
    "CURRENT_SHA",
    "WORKTREE",
    "DIRTY_AT_ENTRY",
    "FILES_CHANGED",
    "TESTS_EXECUTED",
    "LATEST_HANDOFF_PUBLICATION",
    "NEXT_EXACT_ACTION",
    "UPDATED_UTC",
    "CURRENT_STATUS_SHA256",
    "REOPENED_UTC",
    "OPEN_REOPENED_GATES",
    "CHECKPOINT_REVISION",
}


def checked_id(value):
    if not TASK_ID.fullmatch(value):
        raise AgentError(
            "Invalid ID; use at most 64 letters, digits, underscores or hyphens"
        )
    return value


def valid_utc(value):
    try:
        return (
            value.endswith("Z")
            and datetime.fromisoformat(value).utcoffset().total_seconds() == 0
        )
    except (AttributeError, ValueError):
        return False


def parse_checkpoint(text):
    front, fence, _ = text[4:].partition("\n---\n")
    if not text.startswith("---\n") or not fence:
        raise AgentError("Invalid checkpoint front matter")
    fields = {}
    for line in front.splitlines():
        key, sep, value = line.partition(": ")
        if not sep or key in fields:
            raise AgentError("Malformed or duplicate checkpoint field")
        fields[key] = json.loads(value)
    if (
        fields.keys() != REQUIRED
        or fields["CHECKPOINT_SCHEMA"] != SCHEMA
        or fields["STATUS"] not in CHECKPOINT_STATUSES
        or not all(
            isinstance(fields[key], str) and SHA.fullmatch(fields[key])
            for key in ("BASELINE_SHA", "CURRENT_SHA")
        )
        or not all(
            isinstance(fields[key], list)
            for key in ("FILES_CHANGED", "TESTS_EXECUTED", "OPEN_REOPENED_GATES")
        )
    ):
        raise AgentError("Incomplete or unsupported checkpoint")
    reopened = fields["REOPENED_UTC"]
    if (
        not isinstance(reopened, dict)
        or set(reopened) != set(fields["OPEN_REOPENED_GATES"])
        or not all(valid_utc(value) for value in reopened.values())
    ):
        raise AgentError("Invalid reopened-gate timestamps")
    for key, value in fields.items():
        validate_text(json.dumps(value, ensure_ascii=False), key, 80000)
    checked_id(fields["TASK_ID"])
    return fields


def state_status(state, live):
    if state is None:
        return "ABSENT"
    if (
        state["CURRENT_SHA"] != live["sha"]
        or state["CURRENT_BRANCH"] != live["branch"]
        or state["CURRENT_STATUS_SHA256"] != live.get("status_sha256", "UNKNOWN")
    ):
        return "STALE_VERIFY_FIRST"
    return state["STATUS"]


def checkpoint_metadata(previous, args, live):
    fields = dict(previous or DEFAULTS)
    for assignment in args.set:
        key, sep, value = assignment.partition("=")
        if not sep or key not in DEFAULTS:
            raise AgentError(f"Unsupported checkpoint detail: {key}")
        fields[key] = validate_text(value, key)
    if not previous:
        fields.update(
            BASELINE_BRANCH=live["branch"],
            BASELINE_SHA=live["sha"],
            DIRTY_AT_ENTRY=json.dumps(
                {"dirty": live["dirty"], "paths": live["changed"]},
                ensure_ascii=False,
            ),
        )
    fields["TASK_TITLE"] = fields["TASK_TITLE"] or args.task_id
    fields.update(
        CHECKPOINT_SCHEMA=SCHEMA,
        TASK_ID=args.task_id,
        STATUS=args.status,
        CURRENT_BRANCH=live["branch"],
        CURRENT_SHA=live["sha"],
        WORKTREE=".",
        CURRENT_STATUS_SHA256=live.get("status_sha256", "UNKNOWN"),
        FILES_CHANGED=args.changed or fields.get("FILES_CHANGED") or live["changed"],
        LATEST_HANDOFF_PUBLICATION=PUBLICATION,
        NEXT_EXACT_ACTION=validate_text(args.next, "NEXT_EXACT_ACTION", 1000),
        UPDATED_UTC=utc(),
        CHECKPOINT_REVISION=uuid.uuid4().hex,
    )
    return fields


def validate_record(record, live):
    if (
        not isinstance(record, dict)
        or record.get("schema") != SCHEMA
        or not isinstance(record.get("gate"), str)
        or not TASK_ID.fullmatch(record["gate"])
        or type(record.get("exit")) is not int
        or record.get("sha") != live["sha"]
        or record.get("branch") != live["branch"]
        or record.get("status_sha256") != live.get("status_sha256", "UNKNOWN")
        or record.get("source_stable") is not True
        or not valid_utc(record.get("utc"))
    ):
        raise AgentError(
            "Recorded test does not match current source or has invalid fields"
        )
    validate_text(record.get("command"), "recorded command")
    return record


def write_checkpoint(repo, args):
    checked_id(args.task_id)
    repo.require_config()
    with repo.lock():
        name = repo.config["checkpoint_path"]
        path = repo.ensure_local(name)
        live = repo.snapshot()
        previous = repo.read_checkpoint()
        if previous and previous["TASK_ID"] != args.task_id:
            if previous["STATUS"] in ACTIVE | {"BLOCKED"} and not args.replace_task:
                raise AgentError(
                    "Active task differs; preserve it or specify --replace-task"
                )
            previous = None
        freshness = state_status(previous, live)
        if freshness == "STALE_VERIFY_FIRST" and not args.refresh_source:
            raise AgentError(
                "STALE_VERIFY_FIRST: inspect live source before --refresh-source"
            )
        fields = checkpoint_metadata(previous, args, live)
        tests = (
            {}
            if freshness == "STALE_VERIFY_FIRST" or not previous
            else {
                record["gate"]: validate_record(record, live)
                for record in previous["TESTS_EXECUTED"]
            }
        )
        for name in args.changed:
            repo.path(name)
            if repo.safe_metadata_path(name) != name:
                raise AgentError(
                    "Changed paths must exclude private and generated data"
                )
        reopened = dict(previous["REOPENED_UTC"]) if previous else {}
        for gate in args.reopen:
            reopened[checked_id(gate)] = utc()
            tests.pop(gate, None)
        closing = {}
        for assignment in args.close_gate:
            gate, sep, reason = assignment.partition("=")
            if gate not in reopened or not sep:
                raise AgentError(
                    "Use --close-gate ID=FIRST-DIVERGENCE-EVIDENCE for a reopened gate"
                )
            closing[gate] = validate_text(reason, "first-divergence evidence")
        for name in args.evidence:
            prefix = repo.config["local_evidence_dir"] + "/tests/"
            if (
                not name.startswith(prefix)
                or "/" in name[len(prefix) :]
                or not name.endswith(".json")
            ):
                raise AgentError(
                    "Use a record-test evidence path from output/agentops/tests"
                )
            repo.ensure_local(name)
            record = validate_record(json.loads(repo.read(name)[0]), live)
            gate = record["gate"]
            if gate in reopened and (
                gate not in closing
                or record["exit"] != 0
                or record["utc"] <= reopened[gate]
            ):
                raise AgentError(
                    "Reopened gate needs first-divergence evidence and a fresh passing rerun"
                )
            tests[gate] = record
        for gate, reason in closing.items():
            if gate not in tests:
                raise AgentError(
                    "Reopened gate needs a passing --evidence rerun on current source"
                )
            del reopened[gate]
            fields["KNOWN_FAILURES"] += f" | {gate}: {reason}; verified rerun recorded"
        fields["REOPENED_UTC"] = reopened
        fields["OPEN_REOPENED_GATES"] = sorted(reopened)
        fields["TESTS_EXECUTED"] = list(tests.values())
        body = "\n".join(
            f"{key}: {json.dumps(value, ensure_ascii=False)}"
            for key, value in fields.items()
        )
        document = f"---\n{body}\n---\n\n# Active task checkpoint\n"
        parse_checkpoint(document)
        atomic_write(path, document.encode())
    return {
        "path": repo.config["checkpoint_path"],
        "status": args.status,
        "next_exact_action": fields["NEXT_EXACT_ACTION"],
    }


def record_test(repo, args):
    repo.require_config()
    gate = checked_id(args.gate)
    argv = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not argv:
        raise AgentError("Supply the exact test command after --")
    command = validate_text(shlex.join(argv), "test command")
    live = repo.snapshot()
    started = utc()
    exit_code, output = bounded_run(
        argv, repo.root, timeout=args.timeout, limit=1_000_000, include_stderr=True
    )
    after = repo.snapshot()
    record = {
        "schema": SCHEMA,
        "gate": gate,
        "command": command,
        "exit": exit_code,
        "sha": live["sha"],
        "branch": live["branch"],
        "dirty": live["dirty"],
        "status_sha256": live.get("status_sha256", "UNKNOWN"),
        "source_stable": all(
            live.get(key) == after.get(key)
            for key in ("sha", "branch", "status_sha256")
        ),
        "utc": started,
    }
    target = f"{repo.config['local_evidence_dir']}/tests/{gate}-{uuid.uuid4().hex}.json"
    atomic_write(
        repo.ensure_local(target),
        (json.dumps(record, indent=2) + "\n").encode(),
        exclusive=True,
    )
    return {
        "evidence": target,
        "record": record,
        "output": output.decode("utf-8", errors="replace"),
    }, exit_code


def format_report(state, live, status, next_action, timestamp):
    fields = [
        ("TASK_ID", state["TASK_ID"]),
        ("TASK_TITLE", state["TASK_TITLE"]),
        ("UTC", timestamp),
        ("STATUS", status),
        ("CHECKPOINT_REVISION", state["CHECKPOINT_REVISION"]),
        ("SOURCE_REF", live["branch"]),
        ("SOURCE_SHA", live["sha"]),
        ("DIRTY", live["dirty"]),
        ("BASELINE_BRANCH", state["BASELINE_BRANCH"]),
        ("BASELINE_SHA", state["BASELINE_SHA"]),
        ("DIRTY_AT_ENTRY", state["DIRTY_AT_ENTRY"]),
        ("HANDOFF_PUBLICATION", PUBLICATION),
        ("PUBLICATION_REASON", "LOCAL_REPORT_CREATED_WITHOUT_REMOTE_OPERATION"),
        (
            "HANDOFF_RETRY",
            "Follow the repository publication policy for the sanitized public summary.",
        ),
        ("OPERATOR_ACCEPTANCE", "PENDING"),
    ]
    fields.extend((key, state[key]) for key in DEFAULTS if key != "TASK_TITLE")
    fields.extend(
        (key, state[key])
        for key in (
            "FILES_CHANGED",
            "TESTS_EXECUTED",
            "OPEN_REOPENED_GATES",
        )
    )
    fields.append(("NEXT_EXACT_ACTION", next_action))
    return (
        "# UAOS-B1 handoff\n\n"
        + "\n".join(
            f"{key}: {json.dumps(value, ensure_ascii=False)}  " for key, value in fields
        )
        + "\n"
    )


def check_report_status(state, status):
    allowed = {
        "COMPLETE_VERIFIED": {"COMPLETE"},
        "PARTIAL": {"PARTIAL"},
        "INTERRUPTED": {"INTERRUPTED"},
        "BLOCKED": {"BLOCKED"},
        "CHECKPOINT": {"ACTIVE", "PARTIAL", "INTERRUPTED", "BLOCKED"},
    }
    if state["STATUS"] not in allowed[status]:
        raise AgentError("Report outcome contradicts the checkpoint")
    if status != "COMPLETE_VERIFIED":
        return
    tests = state["TESTS_EXECUTED"]
    if (
        state["CURRENT_SHA"] == "UNKNOWN"
        or not tests
        or any(record["exit"] != 0 for record in tests)
        or state["OPEN_REOPENED_GATES"]
        or state["WORKSTREAMS_PARTIAL"] != "NONE"
        or state["WORKSTREAMS_NOT_STARTED"] != "NONE"
    ):
        raise AgentError(
            "COMPLETE_VERIFIED requires matched executed passing proof and closed gates"
        )


def history_entries(repo, base):
    root = repo.path(f"{base}/history")
    if not root.exists():
        return []
    entries = []
    for path in root.iterdir():
        if not HISTORY.fullmatch(path.name):
            continue
        value, _ = repo.read(f"{base}/history/{path.name}")
        stamp = re.search(r'^UTC: ("[0-9T:.Z-]+")  $', value, re.MULTILINE)
        if not stamp:
            raise AgentError(f"Malformed history timestamp: {path.name}")
        entries.append((json.loads(stamp[1]), path.name, value))
    return sorted(entries, reverse=True)


def write_report(repo, args):
    repo.require_config()
    checked_id(args.task_id)
    with repo.lock():
        state = repo.read_checkpoint()
        live = repo.snapshot()
        if not state or state["TASK_ID"] != args.task_id:
            raise AgentError("Write the matching task checkpoint before reporting")
        if state_status(state, live) == "STALE_VERIFY_FIRST":
            raise AgentError("STALE_VERIFY_FIRST: update checkpoint before reporting")
        next_action = validate_text(args.next, "NEXT_EXACT_ACTION", 1000)
        if next_action != state["NEXT_EXACT_ACTION"]:
            raise AgentError("Next action must match checkpoint")
        for record in state["TESTS_EXECUTED"]:
            validate_record(record, live)
        check_report_status(state, args.status)
        base = f"{repo.config['local_evidence_dir']}/handoff"
        latest = repo.ensure_local(f"{base}/LATEST.md")
        index = repo.ensure_local(f"{base}/INDEX.md")
        entries = history_entries(repo, base)
        revision = f'CHECKPOINT_REVISION: "{state["CHECKPOINT_REVISION"]}"  '
        status_line = f'STATUS: "{args.status}"  '
        existing = next(
            (
                name
                for _, name, text in entries
                if revision in text.splitlines() and status_line in text.splitlines()
            ),
            None,
        )
        if existing:
            history_name = existing
        else:
            timestamp = utc()
            stamp = re.sub(r"[-:]", "", timestamp.split(".")[0]) + "Z"
            text = format_report(state, live, args.status, next_action, timestamp)
            history_name = f"{stamp}_{args.task_id}.md"
            target = repo.ensure_local(f"{base}/history/{history_name}")
            try:
                atomic_write(target, text.encode(), exclusive=True)
            except FileExistsError:
                history_name = f"{stamp}_{args.task_id}-{uuid.uuid4().hex}.md"
                target = repo.ensure_local(f"{base}/history/{history_name}")
                atomic_write(target, text.encode(), exclusive=True)
            entries.append((timestamp, history_name, text))
            entries.sort(reverse=True)
        _, newest_name, newest = entries[0]
        atomic_write(
            index,
            (
                "# Local handoff index\n\n"
                + "".join(f"- [{name}](history/{name})\n" for _, name, _ in entries)
            ).encode(),
        )
        atomic_write(
            latest,
            (
                f"Immutable copy: [history/{newest_name}](history/{newest_name})\n\n"
                + newest
            ).encode(),
        )
    return {
        "status": args.status,
        "publication": PUBLICATION,
        "history": f"{base}/history/{history_name}",
        "latest": f"{base}/LATEST.md",
    }
