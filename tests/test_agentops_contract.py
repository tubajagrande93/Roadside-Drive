"""UAOS-B1 T01–T24, isolated opt-in Git fixtures and fresh CLI processes."""

import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "tools/agentops.py"
CHECKPOINT = "_agent_state/CURRENT_TASK_CHECKPOINT.md"
HANDOFF = "output/agentops/handoff"
NEXT = "Read AGENTS.md and run python3 tools/agentops.py doctor --json."


class Contract(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "project"
        self.root.mkdir()

    def git(self, *args, ok=True):
        proc = subprocess.run(
            ["git", *args],
            check=False,
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=12,
        )
        if ok:
            self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc

    def init(self):
        self.git("init", "-q", "-b", "sandbox-main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")

    def copy_profile(self):
        for path in (
            "AGENTS.md",
            "GRAND_MASTER.md",
            ".agentops",
            ".agent_rules",
            "_agent_context",
            "_agent_modules",
            "_agent_templates",
        ):
            source, dest = ROOT / path, self.root / path
            if source.is_dir():
                shutil.copytree(source, dest)
            else:
                shutil.copyfile(source, dest)
        for name in (
            "_agent_state/.gitignore",
            "output/agentops/.gitignore",
            "tools/agentops.py",
            "tools/agentops_repo.py",
            "tools/agentops_route.py",
            "tools/agentops_state.py",
            "tests/test_agentops_contract.py",
        ):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        (self.root / ".gitignore").write_text("__pycache__/\n.env\n", encoding="utf-8")

    def commit(self, *paths):
        self.git("add", "--", *(paths or (".",)))
        self.git("commit", "-m", "Fixture source")
        return self.git("rev-parse", "HEAD").stdout.strip()

    def standard(self):
        self.init()
        self.copy_profile()
        return self.commit()

    def run_cli(self, *args, code=0, cwd=None, local_entry=False):
        entry = self.root / "tools/agentops.py" if local_entry else ENTRY
        parts = list(args)
        if "--" in parts:
            parts.insert(parts.index("--"), "--json")
        else:
            parts.append("--json")
        proc = subprocess.run(
            [sys.executable, str(entry), *parts],
            check=False,
            cwd=cwd or self.root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, code, proc.stdout + proc.stderr)
        return json.loads(proc.stdout)

    def checkpoint(self, *options, status="ACTIVE", code=0):
        return self.run_cli(
            "checkpoint",
            "--task-id",
            "FIXTURE",
            "--status",
            status,
            "--next",
            NEXT,
            *options,
            code=code,
        )

    def report(self, status="CHECKPOINT", code=0):
        return self.run_cli(
            "report",
            "--task-id",
            "FIXTURE",
            "--status",
            status,
            "--next",
            NEXT,
            code=code,
        )

    def put(self, path, text):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
        return destination

    def hashes(self, paths):
        return {
            p: hashlib.sha256((self.root / p).read_bytes()).hexdigest() for p in paths
        }

    def test_T01_actual_unknown_git_profile(self):
        self.init()
        self.put("src/tool.go", "package fixture\n")
        sha = self.commit()
        packet = self.run_cli("doctor")
        self.assertEqual(packet["fingerprint"]["sha"], sha)
        self.assertEqual(packet["fingerprint"]["branch"], "refs/heads/sandbox-main")
        self.assertIs(packet["fingerprint"]["dirty"], False)
        self.assertEqual(packet["schema"], "NOT_INSTALLED")
        self.assertNotIn("framework", packet)
        self.assertEqual(
            self.run_cli("route", "--task", "package fixture")["candidates"][0]["path"],
            "src/tool.go",
        )

    def test_T02_preserve_dirty_untracked_ignored(self):
        self.standard()
        dirty = ("tools/agentops.py", "untracked.txt", ".env")
        for name in dirty:
            self.put(name, "# sentinel " + name)
        before = self.hashes(dirty)
        self.run_cli("bootstrap", "--apply")
        self.checkpoint()
        self.report()
        self.assertEqual(self.hashes(dirty), before)
        self.assertEqual(self.git("diff", "--cached", "--name-only").stdout, "")

    def test_T03_existing_agents_byte_stable(self):
        self.standard()
        entry = self.root / "AGENTS.md"
        entry.write_bytes(b"# Policy\r\nRetain our rules.\r\n")
        before = entry.read_bytes()
        self.assertEqual(self.run_cli("bootstrap", "--apply")["status"], "APPLIED")
        entry.write_bytes(entry.read_bytes() + b"\nUser footer.\r\n")
        value = entry.read_bytes()
        self.assertTrue(value.startswith(before))
        self.assertTrue(value.endswith(b"User footer.\r\n"))
        self.assertEqual(value.count(b"<!-- AGENTOPS:BEGIN -->"), 1)
        self.run_cli("bootstrap", "--apply")
        self.assertEqual(entry.read_bytes(), value)

    def test_T04_manifest_existing_canonical_authority(self):
        self.standard()
        old = self.root / "GRAND_MASTER.md"
        custom = self.root / "SYSTEM_RECORD.md"
        old.rename(custom)
        manifest = self.root / ".agentops/manifest.json"
        cfg = json.loads(manifest.read_text())
        cfg["grand_master_path"] = cfg["canonical_master"] = custom.name
        manifest.write_text(json.dumps(cfg))
        content = custom.read_bytes()
        index = self.root / "_agent_context/GRAND_MASTER_INDEX.md"
        index.write_text(index.read_text().replace("GRAND_MASTER.md", custom.name))
        self.assertEqual(self.run_cli("bootstrap", "--apply")["status"], "NO_OP")
        self.assertFalse(old.exists())
        self.assertEqual(custom.read_bytes(), content)
        self.assertEqual(self.run_cli("verify")["status"], "PASS")

    def test_T05_nested_instructions_preserved(self):
        self.standard()
        child = self.put("apps/component/AGENTS.md", "Use the local runner.\n")
        before = child.read_bytes()
        self.run_cli("bootstrap", "--apply", cwd=child.parent)
        self.assertEqual(child.read_bytes(), before)
        self.assertEqual(
            self.run_cli("doctor", cwd=child.parent)["paths"]["agent_entry"],
            "AGENTS.md",
        )

    def test_T06_repeated_bootstrap_and_report(self):
        self.standard()
        self.assertEqual(self.run_cli("bootstrap", "--dry-run")["changes"], [])
        self.checkpoint()
        one = self.report()
        two = self.report()
        self.assertEqual(one["history"], two["history"])
        self.assertEqual(len(list((self.root / HANDOFF / "history").iterdir())), 1)
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_T07_targeted_cap_and_no_mutation(self):
        self.standard()
        for num in range(16):
            self.put(f"src/route_{num:02}.py", "def needle():\n    return 'needle'\n")
        self.put(".env", "needle=SECRET_CANARY")
        self.commit("src")
        before = self.git("status", "--porcelain", "--ignored").stdout
        result = self.run_cli("route", "--task", "needle src/route_07.py")
        self.assertEqual(result["candidates"][0]["path"], "src/route_07.py")
        self.assertEqual(len(result["candidates"]), 12)
        self.assertNotIn("SECRET_CANARY", json.dumps(result))
        self.assertEqual(self.git("status", "--porcelain", "--ignored").stdout, before)

    def test_T08_unknown_symbol_verify_first(self):
        self.standard()
        packet = self.run_cli("route", "--task", "unknown_" + uuid.uuid4().hex)
        self.assertEqual(packet["owner"], "VERIFY_FIRST")
        self.assertEqual(packet["caller"], "VERIFY_FIRST")
        self.assertEqual(packet["candidates"], [])

    def test_T09_verified_anchors_and_source_vs_doc_conflict(self):
        self.standard()
        packet = self.run_cli("route", "--task", "resume checkpoint")
        for role in ("owner", "caller", "consumer", "consumer_read_anchor"):
            item = packet[role]
            source = (self.root / item["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(source).hexdigest(), item["sha256"])
            self.assertIn(
                item["excerpt"], source.decode().splitlines()[item["line"] - 1]
            )
        source = self.root / "tools/agentops_state.py"
        source.write_text(
            source.read_text().replace("def write_checkpoint(", "def replaced(")
        )
        packet = self.run_cli("route", "--task", "resume checkpoint")
        self.assertEqual(packet["owner"], "VERIFY_FIRST")
        self.assertTrue(packet["context_references"])

    def test_T10_source_owner_plan(self):
        self.standard()
        out = "output/agentops/task.md"
        result = self.run_cli("powerbrain", "--task", "checkpoint resume", "--out", out)
        self.assertEqual(result["status"], "DRAFT_REQUIRES_SOURCE_REASONING")
        brief = (self.root / out).read_text()
        for item in (
            "def write_checkpoint(",
            "PB-07",
            "QA-04",
            "VERIFY_FIRST",
            "OPEN_INSUFFICIENT_EVIDENCE",
            "PENDING",
        ):
            self.assertIn(item, brief)
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_T11_active_interrupted_exact_resume(self):
        self.standard()
        self.checkpoint()
        self.assertEqual(self.run_cli("doctor")["checkpoint_status"], "ACTIVE")
        self.checkpoint(status="INTERRUPTED")
        self.report("INTERRUPTED")
        found = self.run_cli("doctor", local_entry=True)
        self.assertEqual(found["checkpoint_status"], "INTERRUPTED")
        self.assertEqual(found["task_id"], "FIXTURE")
        self.assertEqual(found["next_exact_action"], NEXT)

    def test_T12_stale_sha_refuses_silent_resume(self):
        self.standard()
        self.checkpoint()
        self.put("new.py", "# next commit")
        self.commit()
        self.assertEqual(
            self.run_cli("doctor")["checkpoint_status"], "STALE_VERIFY_FIRST"
        )
        self.assertEqual(self.run_cli("doctor")["next_exact_action"], None)
        before = self.hashes([CHECKPOINT])
        self.assertIn("STALE_VERIFY_FIRST", self.checkpoint(code=2)["error"])
        self.assertEqual(self.hashes([CHECKPOINT]), before)
        self.checkpoint("--refresh-source")
        self.assertEqual(self.run_cli("doctor")["checkpoint_status"], "ACTIVE")
        self.put("new.py", "# first dirty edit")
        self.checkpoint("--refresh-source")
        self.put("new.py", "# second dirty edit")
        self.assertEqual(
            self.run_cli("doctor")["checkpoint_status"], "STALE_VERIFY_FIRST"
        )

    def test_T13_non_git_truthful_local_fallback(self):
        self.copy_profile()
        result = self.run_cli("doctor")
        self.assertEqual(result["fingerprint"]["git"], "NON_GIT")
        self.assertEqual(result["fingerprint"]["sha"], "UNKNOWN")
        self.checkpoint()
        self.assertEqual(self.report()["publication"], "HANDOFF_NOT_PUBLISHED")
        self.assertEqual(
            self.run_cli("route", "--task", "scope")["source_proof"], "NON_GIT_BOUNDED"
        )

    def populate_collision(self):
        self.checkpoint()
        first = self.report()
        original = self.hashes([first["history"]])
        path = self.root / first["history"]
        name = re.sub(r"^[0-9]{8}T[0-9]{6}Z", "20000101T000000Z", path.name)
        marker = path.with_name(name)
        marker.write_bytes(
            re.sub(
                rb'(?m)^UTC: "[^"]+"',
                b'UTC: "2000-01-01T00:00:00Z"',
                path.read_bytes(),
            )
        )
        return first, marker, original

    def test_T14_exclusive_history_collision(self):
        self.standard()
        first, marker, original = self.populate_collision()
        # Freeze the timestamp in a fresh process to ensure collision independent of scheduler.
        self.checkpoint()
        script = (
            "import sys; sys.path.insert(0, sys.argv.pop(1)); import agentops, agentops_state; "
            "agentops_state.utc=lambda:'2000-01-01T00:00:00.123456Z'; "
            "raise SystemExit(agentops.main())"
        )
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                str(ROOT / "tools"),
                "report",
                "--task-id",
                "FIXTURE",
                "--status",
                "CHECKPOINT",
                "--next",
                NEXT,
                "--json",
            ],
            check=False,
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=12,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        second = json.loads(proc.stdout)
        self.assertRegex(
            second["history"], r"20000101T000000Z_FIXTURE-[a-f0-9]{32}\.md$"
        )
        self.assertTrue(marker.is_file())
        self.assertEqual(self.hashes([first["history"]]), original)
        self.assertIn(
            first["history"].split("/")[-1],
            (self.root / HANDOFF / "LATEST.md").read_text(),
        )

    def test_T15_concurrent_report_and_pointer_recovery(self):
        self.standard()
        self.checkpoint()
        first = self.report()
        self.checkpoint()
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda _: self.report(), range(7)))
        paths = {result["history"] for result in results}
        self.assertEqual(len(paths), 1)
        path = paths.pop()
        self.assertNotEqual(first["history"], path)
        index = self.root / HANDOFF / "INDEX.md"
        self.assertEqual(index.read_text().count("](history/"), 2)
        latest = self.root / HANDOFF / "LATEST.md"
        latest.write_text("interrupted pointer update")
        self.assertTrue(self.run_cli("doctor")["open_issues"])
        self.report()
        self.assertTrue(latest.read_text().endswith((self.root / path).read_text()))
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_T16_no_pass_without_exact_executed_proof(self):
        self.standard()
        self.checkpoint("--set", "WORKSTREAMS_NOT_STARTED=NONE", status="COMPLETE")
        self.assertIn("executed", self.report("COMPLETE_VERIFIED", code=2)["error"])
        failed = self.run_cli(
            "record-test",
            "--gate",
            "SMOKE",
            "--",
            "sh",
            "-c",
            "exit 7",
            code=7,
        )
        self.assertEqual(failed["record"]["exit"], 7)
        self.checkpoint("--evidence", failed["evidence"], status="COMPLETE")
        self.report("COMPLETE_VERIFIED", code=2)
        proof = self.run_cli(
            "record-test",
            "--gate",
            "SMOKE",
            "--",
            "true",
        )
        self.checkpoint("--evidence", proof["evidence"], status="COMPLETE")
        self.assertEqual(
            self.report("COMPLETE_VERIFIED")["status"], "COMPLETE_VERIFIED"
        )

    def test_T17_reopen_reproduced_regression(self):
        self.standard()
        proof = self.run_cli("record-test", "--gate", "WORLD", "--", "true")
        self.checkpoint(
            "--set",
            "WORKSTREAMS_NOT_STARTED=NONE",
            "--evidence",
            proof["evidence"],
            status="COMPLETE",
        )
        self.report("COMPLETE_VERIFIED")
        self.checkpoint("--reopen", "WORLD", status="PARTIAL")
        state = (self.root / CHECKPOINT).read_text()
        self.assertIn('OPEN_REOPENED_GATES: ["WORLD"]', state)
        self.assertIn("TESTS_EXECUTED: []", state)
        self.checkpoint("--evidence", proof["evidence"], code=2, status="PARTIAL")
        self.assertEqual(
            self.run_cli("route", "--task", "regression reopen WORLD")["mode"],
            "HIGH_RISK_ESCALATION",
        )

        self.checkpoint(
            "--close-gate",
            "WORLD=Observed writer boundary",
            "--evidence",
            proof["evidence"],
            code=2,
            status="PARTIAL",
        )
        rerun = self.run_cli("record-test", "--gate", "WORLD", "--", "true")
        self.checkpoint(
            "--close-gate",
            "WORLD=Observed writer boundary",
            "--evidence",
            rerun["evidence"],
            status="COMPLETE",
        )
        self.assertEqual(
            self.report("COMPLETE_VERIFIED")["status"], "COMPLETE_VERIFIED"
        )

    def test_T18_exclude_private_generated_binary(self):
        self.standard()
        client, generated, private, secret = (uuid.uuid4().hex for _ in range(4))
        self.put("data/raw/customer.py", f"def unicorn(): return '{client}'")
        self.put("Saved/auto.py", f"def unicorn(): return '{generated}'")
        self.put("src/secrets.py", f"unicorn = '{private}'")
        self.put("src/ordinary.py", f"unicorn = 42\npassword = '{secret}'\n")
        (self.root / "src/binary.py").write_bytes(b"unicorn\x00" + secret.encode())
        self.commit("data", "Saved", "src")
        result = json.dumps(self.run_cli("route", "--task", "unicorn password"))
        self.assertIn("ordinary.py", result)
        for value in (client, generated, private, secret):
            self.assertNotIn(value, result)

    def test_T19_reject_external_symlink_and_traversal(self):
        self.standard()
        outside = self.root.parent / "outside.md"
        outside.write_text("preserve external bytes")
        (self.root / "output/agentops/leak.md").symlink_to(outside)
        for dest in ("output/agentops/leak.md", "../outside.md", str(outside)):
            self.run_cli("powerbrain", "--task", "probe", "--out", dest, code=2)
        self.assertEqual(outside.read_text(), "preserve external bytes")
        (self.root / CHECKPOINT).symlink_to(outside)
        self.checkpoint(code=2)

    def test_T20_app_and_test_bytes_unchanged(self):
        self.standard()
        names = ("apps/demo/engine.py", "apps/demo/test_engine.py")
        self.put(names[0], "def value(): return 42\n")
        self.put(names[1], "from engine import value\nassert value() == 42\n")
        self.commit("apps")
        before = self.hashes(names)
        self.run_cli("verify")
        self.run_cli("bootstrap", "--dry-run")
        self.checkpoint()
        self.report()
        self.assertEqual(self.hashes(names), before)
        proc = subprocess.run(
            [sys.executable, "test_engine.py"],
            check=False,
            cwd=self.root / "apps/demo",
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.git("diff", "HEAD", "--name-only").stdout, "")

    def test_T21_monorepo_source_and_root(self):
        sha = self.standard()
        symbol = "endpoint_" + uuid.uuid4().hex
        path = self.put("apps/child/api.rs", f"pub fn {symbol}() {{}}\n")
        self.put("web/site.ts", f"export const {symbol} = 1;\n")
        self.commit("apps", "web")
        result = self.run_cli("route", "--task", symbol, cwd=path.parent)
        self.assertNotEqual(result["source"]["sha"], sha)
        self.assertEqual(
            {c["path"] for c in result["candidates"]},
            {"apps/child/api.rs", "web/site.ts"},
        )
        self.assertFalse((path.parent / ".agentops").exists())

    def test_T22_denied_or_missing_remote_preserves_queue(self):
        self.standard()
        self.git("remote", "add", "origin", "../missing-remote.git")
        self.checkpoint(status="PARTIAL")
        handoff = self.report("PARTIAL")
        paths = (handoff["history"], handoff["latest"])
        before = self.hashes(paths)
        attempted = self.git("push", "origin", "HEAD:refs/heads/agent-output", ok=False)
        self.assertNotEqual(attempted.returncode, 0)
        self.assertEqual(self.hashes(paths), before)
        self.assertEqual(handoff["publication"], "HANDOFF_NOT_PUBLISHED")
        self.assertIn("HANDOFF_RETRY", (self.root / handoff["history"]).read_text())
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_T23_context_pressure_required_fields(self):
        self.standard()
        self.checkpoint(
            "--set",
            "WORKSTREAMS_COMPLETE=PB-00,PB-01",
            "--set",
            "WORKSTREAMS_PARTIAL=PB-02",
            status="INTERRUPTED",
        )
        value = (self.root / CHECKPOINT).read_text()
        required = (
            "CHECKPOINT_SCHEMA",
            "TASK_ID",
            "TASK_TITLE",
            "STATUS",
            "OPERATOR_AUTHORIZATION",
            "BASELINE_BRANCH",
            "BASELINE_SHA",
            "CURRENT_BRANCH",
            "CURRENT_SHA",
            "WORKTREE",
            "DIRTY_AT_ENTRY",
            "FILES_CHANGED",
            "WORKSTREAMS_COMPLETE",
            "WORKSTREAMS_PARTIAL",
            "WORKSTREAMS_NOT_STARTED",
            "TESTS_EXECUTED",
            "TESTS_NOT_EXECUTED",
            "KNOWN_FAILURES",
            "LATEST_SOURCE_DELIVERY",
            "LATEST_HANDOFF_PUBLICATION",
            "NEXT_EXACT_ACTION",
            "UPDATED_UTC",
        )
        for field in required:
            self.assertRegex(value, rf"(?m)^{field}: ")
        self.assertEqual(self.run_cli("doctor")["next_exact_action"], NEXT)

    def test_T24_new_process_with_only_repo(self):
        sha = self.standard()
        self.checkpoint(status="INTERRUPTED")
        report = self.report("INTERRUPTED")
        script = (
            "import json, pathlib, subprocess, sys; "
            "entry=pathlib.Path('AGENTS.md').read_text(); "
            "assert 'tools/agentops.py doctor --json' in entry; "
            "print(subprocess.check_output([sys.executable,'tools/agentops.py','doctor','--json'],text=True))"
        )
        env = {"PATH": os.environ["PATH"], "LANG": "C.UTF-8"}
        output = subprocess.check_output(
            [sys.executable, "-I", "-c", script],
            cwd=self.root,
            env=env,
            text=True,
            timeout=15,
        )
        result = json.loads(output)
        self.assertEqual(result["fingerprint"]["sha"], sha)
        self.assertEqual(result["checkpoint_status"], "INTERRUPTED")
        self.assertEqual(result["latest_handoff"], report["latest"])
        self.assertIn("Open blockers", result["current_state"])
        self.assertEqual(result["next_exact_action"], NEXT)
        self.assertFalse((self.root / "tools/__pycache__").exists())
        self.assertTrue((self.root / report["history"]).is_file())


if __name__ == "__main__":
    unittest.main()
