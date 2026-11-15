"""Bounded repository reads, Git fingerprinting and atomic local storage."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import selectors
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

SCHEMA = "UAOS-B1"
MANIFEST = ".agentops/manifest.json"
BEGIN = b"<!-- AGENTOPS:BEGIN -->"
END = b"<!-- AGENTOPS:END -->"
RULES = (
    "00-core",
    "10-preservation",
    "20-workflow",
    "30-evidence-and-publication",
    "40-quality-gates",
)
CONTEXT = (
    "README",
    "REPO_PROFILE",
    "CURRENT_STATE",
    "ARCHITECTURE_MAP",
    "GRAND_MASTER_INDEX",
    "RECENT_MILESTONES",
    "KNOWN_ISSUES",
)
MODULES = ("CONTEXT_SHARK", "MAX_POWERBRAIN")
TEMPLATES = ("POWERBRAIN_TASK", "HANDOFF", "CHECKPOINT", "QA_GATE_LEDGER")
SHA = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64}|UNKNOWN)\Z")
PRIVATE = re.compile(
    r"(?i)(?:^|[._-])(?:credentials?|secrets?|tokens?|passwords?|private[_-]?keys?)(?:[._-]|$)"
)
SECRET_TEXT = re.compile(
    r"(?i)(?:-----BEGIN .*PRIVATE KEY|(?:gh[pousr]_|github_pat_|sk-[a-z0-9])"
    r"[a-z0-9_-]{12,}|AKIA[A-Z0-9]{16}|https?://[^/\s]+@|"
    r"(?:password|secret|token|api[_-]?key)\s*['\"]?\s*[:=]\s*['\"][^'\"]+)"
)
HOST_PATH = re.compile(r"(?:/Users/|/home/|/private/|/Volumes/|[A-Za-z]:\\\\)")
EXCLUDED = {
    "node_modules",
    "vendor",
    "third_party",
    "third-party",
    "build",
    "dist",
    "target",
    "output",
    "agentoutput",
    "_agent_state",
    "binaries",
    "deriveddatacache",
    "intermediate",
    "saved",
    "__pycache__",
    "cache",
    "generated",
}
SOURCE_SUFFIX = {
    ".py",
    ".rs",
    ".go",
    ".java",
    ".kt",
    ".swift",
    ".m",
    ".mm",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cs",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".vue",
    ".svelte",
    ".sh",
    ".ps1",
    ".toml",
    ".ini",
    ".json",
    ".yaml",
    ".yml",
    ".uproject",
    ".sql",
    ".rb",
    ".lua",
    ".html",
    ".css",
}
CONFIG_KEYS = (
    "grand_master_path",
    "canonical_master",
    "agent_entry",
    "rules_dir",
    "context_dir",
    "modules_dir",
    "templates_dir",
    "checkpoint_path",
    "local_evidence_dir",
)
ACTIVE = {"ACTIVE", "INTERRUPTED", "PARTIAL"}


class AgentError(Exception):
    """Expected validation or system failure."""


def utc():
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bounded_run(argv, cwd, *, timeout=8, limit=2_000_000, include_stderr=False):
    """Capture at most limit bytes and terminate commands that overrun budget."""
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    deadline = time.monotonic() + timeout
    stderr = subprocess.STDOUT if include_stderr else subprocess.DEVNULL
    with (
        subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=stderr,
            start_new_session=True,
        ) as proc,
        selectors.DefaultSelector() as selector,
    ):
        selector.register(proc.stdout, selectors.EVENT_READ)
        output = bytearray()
        try:
            while selector.select(max(0, deadline - time.monotonic())):
                chunk = os.read(
                    proc.stdout.fileno(), min(65536, limit + 1 - len(output))
                )
                if not chunk:
                    return proc.wait(
                        timeout=max(0, deadline - time.monotonic())
                    ), bytes(output)
                output.extend(chunk)
                if len(output) > limit:
                    raise AgentError(f"{argv[0]} exceeded output budget")
            raise AgentError(f"{argv[0]} timed out")
        except (AgentError, subprocess.TimeoutExpired) as error:
            import signal

            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            raise AgentError(str(error)) from None


def pieces(data):
    return [
        part.decode("utf-8", errors="replace") for part in data.split(b"\0") if part
    ]


def validate_text(value, label, limit=10000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise AgentError(f"{label} requires 1–{limit} characters")
    if SECRET_TEXT.search(value) or HOST_PATH.search(value) or "\x00" in value:
        raise AgentError(f"{label} contains confidential or machine-specific data")
    return value


def relpath(value):
    if not isinstance(value, str):
        raise AgentError("Path must be text")
    path = PurePosixPath(value)
    if (
        not path.parts
        or path.is_absolute()
        or ".." in path.parts
        or str(path) != value
        or "\\" in value
        or any(ord(c) < 32 for c in value)
    ):
        raise AgentError("Expected a normalized repository-relative path")
    return path


def managed_entry(existing, block):
    """Replace precisely one managed region, preserving all surrounding bytes."""
    if block.count(BEGIN) != 1 or block.count(END) != 1 or not block.startswith(BEGIN):
        raise AgentError("Invalid managed entry block")
    begins, ends = existing.count(BEGIN), existing.count(END)
    if not begins and not ends:
        separator = (
            b""
            if not existing or existing.endswith(b"\n\n")
            else (b"\n" if existing.endswith(b"\n") else b"\n\n")
        )
        return existing + separator + block.rstrip(b"\n") + b"\n"
    if begins != 1 or ends != 1 or existing.index(BEGIN) >= existing.index(END):
        raise AgentError("Ambiguous managed entry markers")
    return (
        existing[: existing.index(BEGIN)]
        + block.rstrip(b"\n")
        + existing[existing.index(END) + len(END) :]
    )


def atomic_write(path, data, *, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=".agentops-", delete=False
    ) as f:
        temporary = Path(f.name)
        try:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
            if exclusive:
                os.link(temporary, path)
            else:
                os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


class Repository:
    def __init__(self, start):
        start = Path(start).resolve(strict=True)
        self.root = start
        self.has_git = bool(shutil.which("git"))
        result, top = self.git("rev-parse", "--show-toplevel")
        self.is_git = result == 0
        if self.is_git:
            self.root = Path(os.fsdecode(top.rstrip(b"\n"))).resolve(strict=True)
        else:
            self.root = next(
                (p for p in (start, *start.parents) if (p / MANIFEST).is_file()),
                start,
            )
        self.config = self.load_config() if self.path(MANIFEST).is_file() else {}

    def git(self, *argv, limit=2_000_000):
        if not self.has_git:
            return 127, b""
        # Override filesystem monitors so a read never starts a Git daemon/hook.
        return bounded_run(
            ["git", "-c", "core.fsmonitor=false", *argv], self.root, limit=limit
        )

    def path(self, value):
        here = self.root
        for part in relpath(value).parts:
            here = here / part
            if here.is_symlink():
                raise AgentError(f"Symlink path rejected: {value}")
        return here

    def read(self, value, *, limit=131072):
        path = self.path(value)
        if not path.is_file():
            raise AgentError(f"Expected readable regular file: {value}")
        with path.open("rb") as f:
            data = f.read(limit + 1)
        if len(data) > limit or b"\x00" in data:
            raise AgentError(f"Binary or oversized file: {value}")
        try:
            return data.decode("utf-8"), digest(data)
        except UnicodeDecodeError:
            raise AgentError(f"Non-UTF-8 file: {value}") from None

    def load_config(self):
        config = json.loads(self.read(MANIFEST)[0])
        if not isinstance(config, dict) or config.get("schema_version") != SCHEMA:
            raise AgentError(
                "Unsupported manifest schema; review and migrate explicitly"
            )
        for key in CONFIG_KEYS:
            self.path(config.get(key))
        if config["canonical_master"] != config["grand_master_path"]:
            raise AgentError("Conflicting manifest master paths")
        if config["checkpoint_path"] != "_agent_state/CURRENT_TASK_CHECKPOINT.md":
            raise AgentError("Checkpoint must remain in the scoped ignored directory")
        if config["local_evidence_dir"] != "output/agentops":
            raise AgentError("Evidence must remain in the scoped ignored directory")
        if config.get("network_side_effects_by_default") is not False:
            raise AgentError("Manifest must default to no network side effects")
        ignored = config.get("source_ignore", [])
        if not isinstance(ignored, list):
            raise AgentError("source_ignore must contain relative paths")
        for entry in ignored:
            relpath(entry)
        return config

    def require_config(self):
        if not self.config:
            raise AgentError(f"Missing {MANIFEST}; install the project profile first")

    def required_files(self):
        self.require_config()
        cfg = self.config
        files = [
            MANIFEST,
            cfg["agent_entry"],
            cfg["grand_master_path"],
            "_agent_state/.gitignore",
            "output/agentops/.gitignore",
            "tools/agentops.py",
            "tools/agentops_repo.py",
            "tools/agentops_state.py",
            "tools/agentops_route.py",
            "tests/test_agentops_contract.py",
        ]
        for key, names in (
            ("rules_dir", RULES),
            ("context_dir", CONTEXT),
            ("modules_dir", MODULES),
            ("templates_dir", TEMPLATES),
        ):
            files.extend(f"{cfg[key]}/{name}.md" for name in names)
        return files

    def safe_source(self, value):
        path = relpath(value)
        if any(
            part.lower() in EXCLUDED or part.startswith(".") or PRIVATE.search(part)
            for part in path.parts
        ):
            return False
        if any(
            path == relpath(prefix) or relpath(prefix) in path.parents
            for prefix in self.config.get("source_ignore", [])
        ):
            return False
        return path.suffix.lower() in SOURCE_SUFFIX

    def safe_metadata_path(self, value):
        path = PurePosixPath(value)
        if value in {"_agent_state/.gitignore", "output/agentops/.gitignore"}:
            return value
        if any(
            part.lower() in EXCLUDED
            or part.lower().startswith(".env")
            or PRIVATE.search(part)
            for part in path.parts
        ):
            return "[protected]"
        if SECRET_TEXT.search(value) or HOST_PATH.search(value):
            return "[protected]"
        return value

    def snapshot(self):
        result = {
            "root": ".",
            "git": "NON_GIT" if self.has_git else "GIT_UNAVAILABLE",
            "branch": "UNKNOWN",
            "sha": "UNKNOWN",
            "upstream": "UNKNOWN",
            "remotes": [],
            "dirty": None,
            "changed": [],
            "ignored_categories": [],
        }
        if not self.is_git:
            return result
        result["git"] = "GIT"
        for key, argv in (
            ("branch", ("symbolic-ref", "-q", "HEAD")),
            ("sha", ("rev-parse", "--verify", "HEAD")),
            ("upstream", ("rev-parse", "--symbolic-full-name", "@{upstream}")),
        ):
            rc, payload = self.git(*argv)
            if rc == 0:
                result[key] = payload.decode("utf-8", errors="replace").strip()
        if result["branch"] == "UNKNOWN" and result["sha"] != "UNKNOWN":
            result["branch"] = "DETACHED"
        rc, raw = self.git(
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--ignored=matching",
            "--no-renames",
        )
        if rc:
            raise AgentError("Could not verify Git status")
        entries = pieces(raw)
        visible = [entry for entry in entries if not entry.startswith("!! ")]
        result["dirty"] = bool(visible)
        result["changed"] = [
            entry[:3] + self.safe_metadata_path(entry[3:]) for entry in visible[:80]
        ]
        result["changed_count"] = len(visible)
        # Compare bytes of a bounded set of safe, changed source paths. Git status
        # letters alone cannot detect a second edit to an already modified file.
        dirty_source = []
        for path in sorted(
            {entry[3:] for entry in visible if self.safe_source(entry[3:])}
        )[:80]:
            try:
                _, checksum = self.read(path)
            except (AgentError, OSError):
                checksum = "UNREADABLE_OR_REMOVED"
            dirty_source.append((path, checksum))
        result["status_sha256"] = digest(json.dumps([visible, dirty_source]).encode())
        result["ignored_categories"] = sorted(
            {
                self.safe_metadata_path(entry[3:]).split("/")[0]
                for entry in entries
                if entry.startswith("!! ")
            }
        )[:40]
        rc, raw = self.git("remote")
        if rc:
            raise AgentError("Could not verify Git remote names")
        result["remotes"] = [
            self.safe_metadata_path(name) for name in raw.decode().splitlines()[:30]
        ]
        return result

    def tracked(self):
        if self.is_git:
            rc, data = self.git("ls-files", "-z", "--cached")
            if rc:
                raise AgentError("Cannot enumerate indexed source")
            return set(pieces(data))
        return None

    def ensure_local(self, value):
        path = self.path(value)
        if self.is_git:
            rc, data = self.git("ls-files", "-z", "--", value)
            if rc or data:
                raise AgentError(
                    f"Local destination is indexed or cannot be checked: {value}"
                )
            rc, _ = self.git("check-ignore", "-q", "--", value)
            if rc:
                raise AgentError(f"Local destination is not verified ignored: {value}")
        return path

    @contextmanager
    def lock(self):
        name = f"{self.config['local_evidence_dir']}/.agentops.lock"
        path = self.ensure_local(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(
            path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600
        )
        try:
            deadline = time.monotonic() + 15
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise AgentError(
                            "Timed out waiting for the local evidence writer"
                        )
                    time.sleep(0.05)
            yield
        finally:
            os.close(fd)

    def read_checkpoint(self):
        from agentops_state import parse_checkpoint

        if not self.config:
            return None
        name = self.config["checkpoint_path"]
        return (
            parse_checkpoint(self.read(name)[0]) if self.path(name).exists() else None
        )
