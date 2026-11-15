"""Source-first task routing and MAX POWERBRAIN briefs."""

from __future__ import annotations

import json
import os
import re
import shlex

from agentops_repo import (
    ACTIVE,
    HOST_PATH,
    SECRET_TEXT,
    AgentError,
    atomic_write,
    validate_text,
)
from agentops_state import state_status

STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "how",
    "i",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "please",
    "that",
    "the",
    "to",
    "use",
    "verify",
    "inspect",
    "can",
    "with",
    "task",
    "check",
    "find",
}
SOURCE_BUDGET = 80
CANDIDATE_CAP = 12
RISK = re.compile(
    r"\b(migrat\w*|destruct\w*|reopen\w*|regress\w*|credential\w*|"
    r"privileg\w*|deploy\w*|schema|cross-system)\b",
    re.IGNORECASE,
)


def terms(task):
    return set(re.findall(r"[\w.]+", task.lower())) - STOP_WORDS


def visible_line(line):
    return not SECRET_TEXT.search(line) and not HOST_PATH.search(line)


def source_index(repo):
    indexed = repo.tracked()
    if indexed is not None:
        return sorted(p for p in indexed if repo.safe_source(p)), "INDEX"
    files = []
    visited = 0
    for directory, dirs, names in os.walk(repo.root, followlinks=False):
        dirs[:] = sorted(
            d
            for d in dirs
            if not d.startswith(".")
            and not (repo.root / directory / d).is_symlink()
            and repo.safe_source(
                (repo.root / directory / d / "file.py")
                .relative_to(repo.root)
                .as_posix()
            )
        )
        for name in sorted(names):
            visited += 1
            if visited > 800:
                return files, "NON_GIT_BOUNDED"
            path = (repo.root / directory / name).relative_to(repo.root).as_posix()
            if repo.safe_source(path):
                files.append(path)
        visited += 1
        if visited > 800:
            break
    return files, "NON_GIT_BOUNDED"


def context_anchors(repo, task_terms):
    if not repo.config:
        return []
    context = repo.config["context_dir"]
    result = []
    for name in (
        "CURRENT_STATE",
        "ARCHITECTURE_MAP",
        "KNOWN_ISSUES",
        "GRAND_MASTER_INDEX",
    ):
        path = f"{context}/{name}.md"
        if not repo.path(path).is_file():
            continue
        content, checksum = repo.read(path, limit=32000)
        for i, line in enumerate(content.splitlines(), 1):
            if (
                line.startswith("|")
                and len(line) < 500
                and visible_line(line)
                and (terms(line) & task_terms)
            ):
                result.append(
                    {
                        "path": path,
                        "line": i,
                        "sha256": checksum,
                        "anchor": re.findall(r"#gm-[\w-]+", line)[:2],
                        "status": "REFERENCE_ONLY",
                    }
                )
                break
    return result


def verified_edges(repo, sources, task_terms, unreadable):
    candidates = {}
    edges = repo.config.get("source_edges", [])
    if not isinstance(edges, list) or len(edges) > 25:
        raise AgentError("Invalid or oversized source edge catalog")
    for edge in edges:
        if not isinstance(edge, dict) or not task_terms.intersection(
            edge.get("terms", [])
        ):
            continue
        proof = {}
        for role in ("owner", "caller", "consumer", "checks"):
            item = edge.get(role)
            if not isinstance(item, list) or len(item) != 2:
                raise AgentError("Invalid source edge definition")
            path, literal = item
            if path not in sources or not literal:
                break
            try:
                content, checksum = repo.read(path)
            except (AgentError, OSError):
                unreadable.add(repo.safe_metadata_path(path))
                break
            match = next(
                (
                    (i, line.strip()[:170])
                    for i, line in enumerate(content.splitlines(), 1)
                    if literal in line and visible_line(line)
                ),
                None,
            )
            if not match:
                break
            proof[role] = {
                "path": path,
                "line": match[0],
                "excerpt": match[1],
                "sha256": checksum,
                "status": "VERIFIED_SOURCE_ANCHOR",
            }
        if len(proof) == 4:
            return proof
        if proof:
            candidates = proof
    return candidates


def scan_candidates(repo, paths, query, task_terms, unreadable):
    name_score = {
        path: len(
            task_terms.intersection(
                re.findall(r"[\w]+", path.lower().replace("_", " "))
            )
        )
        + (4 if path.lower() in query else 0)
        for path in paths
    }
    ordered = sorted(paths, key=lambda p: (-name_score[p], p))
    matches = []
    bytes_read = 0
    attempted = 0
    for path in ordered[:SOURCE_BUDGET]:
        attempted += 1
        try:
            content, checksum = repo.read(path)
        except (AgentError, OSError):
            unreadable.add(repo.safe_metadata_path(path))
            continue
        bytes_read += len(content.encode())
        hits = []
        for line_no, line in enumerate(content.splitlines(), 1):
            if task_terms & terms(line) and visible_line(line):
                hits.append({"line": line_no, "excerpt": line.strip()[:140]})
                if len(hits) == 3:
                    break
        if hits or name_score[path] > 0:
            matches.append(
                {
                    "path": path,
                    "sha256": checksum,
                    "matches": hits,
                    "confidence": "CANDIDATE",
                    "score": name_score[path] + len(hits),
                }
            )
        if bytes_read >= 800000:
            break
    matches.sort(key=lambda candidate: (-candidate["score"], candidate["path"]))
    return matches[:CANDIDATE_CAP], attempted


def route(repo, task):
    task = validate_text(task, "task", 800)
    live = repo.snapshot()
    checkpoint = repo.read_checkpoint()
    status = state_status(checkpoint, live)
    query = task.lower()
    task_terms = terms(query)
    paths, scan_scope = source_index(repo)
    excluded = set()
    refs = context_anchors(repo, task_terms)
    edges = verified_edges(repo, set(paths), task_terms, excluded)
    candidates, attempted = scan_candidates(repo, paths, query, task_terms, excluded)
    safe_resume = (
        status in ACTIVE
        and checkpoint
        and not RISK.search(task)
        and query
        in {
            checkpoint["TASK_ID"].casefold(),
            checkpoint["TASK_TITLE"].casefold(),
            checkpoint["NEXT_EXACT_ACTION"].casefold(),
        }
    )
    if status == "STALE_VERIFY_FIRST":
        action = "Run python3 tools/agentops.py doctor --json and reconcile the stale checkpoint."
    elif safe_resume:
        action = checkpoint["NEXT_EXACT_ACTION"]
    elif edges.get("owner"):
        owner = edges["owner"]
        action = f"Run sed -n '{max(1, owner['line'] - 2)},{owner['line'] + 35}p' {shlex.quote(owner['path'])}."
    elif candidates:
        action = f"Inspect the source declaration in {candidates[0]['path']} and verify ownership."
    else:
        action = "Run git ls-files (or inspect the scoped non-Git tree) and confirm the target path."
    evidence_base = repo.config.get("local_evidence_dir", "output/agentops")
    latest_name = f"{evidence_base}/handoff/LATEST.md"
    latest = latest_name if repo.path(latest_name).is_file() else "NOT_PUBLISHED"
    return {
        "task": task,
        "mode": (
            "HIGH_RISK_ESCALATION"
            if RISK.search(task) or status == "STALE_VERIFY_FIRST"
            else "RESUME"
            if safe_resume
            else "NEW_TASK"
        ),
        "source": {
            key: live[key]
            for key in ("git", "branch", "sha", "dirty", "upstream", "remotes")
        },
        "checkpoint_status": status,
        "checkpoint_task": checkpoint["TASK_ID"] if checkpoint else None,
        "owner": edges.get("owner", "VERIFY_FIRST"),
        "caller": edges.get("caller", "VERIFY_FIRST"),
        "consumer": edges.get("consumer", "VERIFY_FIRST"),
        "consumer_read_anchor": edges.get("checks", "VERIFY_FIRST"),
        "context_references": refs,
        "latest_handoff": latest,
        "first_divergence": "HYPOTHESIS: reproduce expected vs observed at the first authoritative boundary.",
        "negative_control": (
            "Use an unknown target with identical surrounding inputs and require VERIFY_FIRST."
            if not edges
            else "Repeat the consumer path with stale or missing owner output; require a visible refusal."
        ),
        "source_proof": scan_scope,
        "candidates": candidates,
        "budget": {
            "attempted_paths": attempted,
            "candidate_cap": CANDIDATE_CAP,
            "indexed_source_count": len(paths),
            "skipped_unreadable_count": len(excluded),
        },
        "uncertainty": "Lexical evidence only. Verify edge semantics, task identity and live test behavior.",
        "next_exact_action": action,
    }


def proof_cell(proof):
    if proof == "VERIFY_FIRST":
        return proof
    excerpt = proof["excerpt"].replace("|", "&#124;").replace("`", "&#96;")
    return (
        f"{proof['path']}:{proof['line']} ({proof['status']}, SHA256 {proof['sha256']})"
        f" — {excerpt}"
    )


def powerbrain(repo, task, destination):
    repo.require_config()
    packet = route(repo, task)
    out = repo.ensure_local(destination)
    prefix = repo.config["local_evidence_dir"] + "/"
    if (
        not destination.startswith(prefix)
        or not destination.endswith(".md")
        or "/" in destination[len(prefix) :]
        or out.name.startswith(".")
    ):
        raise AgentError(
            "PowerBrain output must be a top-level .md file in output/agentops"
        )
    path = repo.config["templates_dir"] + "/POWERBRAIN_TASK.md"
    template, checksum = repo.read(path)
    source = packet["source"]
    rows = "\n".join(
        f"| {role} | {proof_cell(packet[role])} | VERIFY_FIRST: inspect behavior and smallest repair |"
        for role in ("owner", "caller", "consumer", "consumer_read_anchor")
    )
    owner = packet["owner"]
    target = owner["path"] if isinstance(owner, dict) else "VERIFY_FIRST"
    references = "\n".join(
        f"| {item['path']}:{item['line']} | REFERENCE_ONLY | Route via approved anchor | "
        f"Runtime behavior | {item['sha256']} |"
        for item in packet["context_references"]
    )
    substitutions = {
        "INTENT": f"Literal scope: {json.dumps(task, ensure_ascii=False)}\n"
        "Keep protected state and unrelated behavior stable. Additional functionality requires scope.",
        "BASELINE": (
            f"- Ref: {source['branch']}\n- SHA: {source['sha']}\n- Dirty: {source['dirty']}\n"
            f"- Local checkpoint: {packet['checkpoint_status']}\n"
            f"- Latest handoff: {packet['latest_handoff']}\n- Template SHA256: {checksum}\n\n"
            "| Reference | Meaning | Use | Cannot infer | Provenance |\n"
            "| --- | --- | --- | --- | --- |\n"
            f"| Git index/live worktree | Source candidates | Trace calls | Runtime PASS | {packet['source_proof']} |\n"
            f"{references}"
        ),
        "OWNERS": (
            "| Role | Proven file/symbol | Behavior and proposed edit |\n| --- | --- | --- |\n"
            f"{rows}\n\nRisk: {packet['mode']}. {packet['uncertainty']}"
        ),
        "DIVERGENCE": (
            f"{packet['first_divergence']} Alternatives: stale source, wrong caller or mismatched "
            f"configuration. Control: {packet['negative_control']}"
        ),
        "PHASES": (
            f"Architecture: {target}. VERIFY_FIRST actual inputs, data flow, persistence, compatibility, "
            "errors, rollback and competing causes before editing.\n\n"
            "| Gate | Precondition and action | Proof and STOP gate |\n| --- | --- | --- |\n"
            "| PB-00 | Run doctor and record protected before hashes | STOP on unresolved scope |\n"
            f"| PB-01 | Trace {target} through caller/consumer | STOP if any owner is unresolved |\n"
            "| PB-02 | Reproduce earliest divergence and falsifier | STOP without failing evidence |\n"
            "| PB-03 | Apply scoped semantic change to proven writer | Scoped diff, no product data loss |\n"
            "| PB-04 | Run targeted + regression + applicable native tests | Exact commands, exits and SHA |\n"
            "| PB-05 | Verify save/reopen and downstream consumer | STOP on parity or compatibility difference |\n"
            "| PB-06 | Update affected durable context | No contradiction with actual source |\n"
            "| PB-07 | Checkpoint and queue report | Verify remote only with actual authority |"
        ),
        "QA": (
            "| Gate | Input and expected outcome | Status |\n| --- | --- | --- |\n"
            "| QA-01 | Exact task sample VERIFY_FIRST; observe expected writer and consumer output | OPEN_INSUFFICIENT_EVIDENCE |\n"
            f"| QA-02 | {packet['negative_control']} | OPEN_INSUFFICIENT_EVIDENCE |\n"
            "| QA-03 | Original failing input and prior expected result VERIFY_FIRST | OPEN_INSUFFICIENT_EVIDENCE |\n"
            "| QA-04 | Native, performance, privacy and compatibility applicability VERIFY_FIRST | OPEN_INSUFFICIENT_EVIDENCE |\n\n"
            "Use PASS_VERIFIED only after observed results, FAIL_REQUIRES_REPAIR for observed failures, "
            "and BLOCKED_EXTERNAL_EVIDENCE for unavailable dependencies."
        ),
        "PRESERVATION": (
            "Run doctor and inspect preservation rules. Record protected paths/hashes and dry-run plan. "
            "Roll back only authorized scoped edits. Keep commits and public refs within explicit authority. "
            "Record local evidence, handoff visibility and OPERATOR_ACCEPTANCE: PENDING."
        ),
        "NEXT": packet["next_exact_action"],
    }
    keys = re.findall(r"\{\{([A-Z]+)\}\}", template)
    if sorted(keys) != sorted(substitutions):
        raise AgentError(
            "PowerBrain template contains missing, unknown or repeated fields"
        )
    filled = re.sub(
        r"\{\{([A-Z]+)\}\}", lambda match: substitutions[match[1]], template
    )
    with repo.lock():
        atomic_write(out, filled.encode())
    return {
        "path": destination,
        "status": "DRAFT_REQUIRES_SOURCE_REASONING",
        "next_exact_action": packet["next_exact_action"],
    }
