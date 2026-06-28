#!/usr/bin/env python3
"""Wave 5 contracts for tasks, calendar, scheduler, and GitHub PR reviewer."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cli.aikit.github_pr as github_pr
from cli.aikit.github_pr import run_gh
from cli.aikit.tasks import create_task, run_task, scheduler_run_once


AGENT = ROOT / "agent"
CLI_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_CLI_TIMEOUT_SECONDS", "60"))


class AgenticWave5ContractsTest(unittest.TestCase):
    def run_agent(self, *args: str, env: dict[str, str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(AGENT), *args],
            cwd=cwd,
            env=os.environ | env,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CLI_TIMEOUT_SECONDS,
        )

    def test_task_create_list_run_pause_resume_and_scheduler(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            create = self.run_agent("task", "create", "daily-check", "--title", "Daily check", "--prompt", "verificar status", "--every", "30m", "--json", env=env)
            listing = self.run_agent("task", "list", "--json", env=env)
            dry_run = self.run_agent("task", "run", "daily-check", "--dry-run", "--json", env=env)
            pause = self.run_agent("task", "pause", "daily-check", "--json", env=env)
            resume = self.run_agent("task", "resume", "daily-check", "--json", env=env)
            scheduler = self.run_agent("scheduler", "run-once", "--dry-run", "--json", env=env)
            history = self.run_agent("task", "history", "daily-check", "--json", env=env)

            self.assertEqual(create.returncode, 0, create.stderr)
            self.assertEqual(listing.returncode, 0, listing.stderr)
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertEqual(pause.returncode, 0, pause.stderr)
            self.assertEqual(resume.returncode, 0, resume.stderr)
            self.assertEqual(scheduler.returncode, 0, scheduler.stderr)
            self.assertEqual(history.returncode, 0, history.stderr)
            self.assertEqual(json.loads(create.stdout)["task"]["id"], "daily-check")
            self.assertEqual(len(json.loads(listing.stdout)["items"]), 1)
            self.assertTrue(json.loads(dry_run.stdout)["dry_run"])
            self.assertEqual(json.loads(scheduler.stdout)["kind"], "scheduler")
            self.assertIn("Created task", json.loads(history.stdout)["history"])

    def test_task_delete_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            create = self.run_agent("task", "create", "delete-me", "--title", "Delete me", "--json", env=env)
            blocked = self.run_agent("task", "delete", "delete-me", "--json", env=env)
            deleted = self.run_agent("task", "delete", "delete-me", "--yes", "--json", env=env)

            self.assertEqual(create.returncode, 0, create.stderr)
            self.assertEqual(blocked.returncode, 2)
            self.assertEqual(json.loads(blocked.stdout)["status"], "needs-confirmation")
            self.assertEqual(deleted.returncode, 0, deleted.stderr)
            self.assertEqual(json.loads(deleted.stdout)["status"], "deleted")

    def test_scheduler_run_once_skips_manual_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            old_home = os.environ.get("AI_DEVKIT_CONFIG_HOME")
            os.environ["AI_DEVKIT_CONFIG_HOME"] = tmpdir
            try:
                create_task(task_id="manual-only", title="Manual only", schedule={"type": "manual"})
                result = scheduler_run_once(dry_run=True)
            finally:
                if old_home is None:
                    os.environ.pop("AI_DEVKIT_CONFIG_HOME", None)
                else:
                    os.environ["AI_DEVKIT_CONFIG_HOME"] = old_home

            self.assertEqual(result["due_count"], 0)
            self.assertEqual(result["runs"], [])

    def test_calendar_ics_fixture_and_natural_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            today = __import__("datetime").date.today().strftime("%Y%m%d")
            ics = home / "agenda.ics"
            ics.write_text(
                "\n".join(
                    [
                        "BEGIN:VCALENDAR",
                        "BEGIN:VEVENT",
                        "UID:1",
                        f"DTSTART:{today}T090000",
                        f"DTEND:{today}T093000",
                        "SUMMARY:Daily sustentacao",
                        "END:VEVENT",
                        "END:VCALENDAR",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            configure = self.run_agent("calendar", "configure", "--ics", str(ics), "--json", env=env)
            today_result = self.run_agent("calendar", "today", "--json", env=env)
            natural = self.run_agent("--json", "qual", "minha", "agenda", "de", "hoje?", env=env)

            self.assertEqual(configure.returncode, 0, configure.stderr)
            self.assertEqual(today_result.returncode, 0, today_result.stderr)
            self.assertEqual(natural.returncode, 0, natural.stderr)
            self.assertEqual(json.loads(today_result.stdout)["count"], 1)
            self.assertIn("Daily sustentacao", json.loads(natural.stdout)["response"])
            self.assertFalse(json.loads(today_result.stdout)["llm_safe"])

    def test_calendar_without_provider_requests_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_agent("calendar", "today", "--json", env={"AI_DEVKIT_CONFIG_HOME": tmpdir})

            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "needs-input")
            self.assertTrue(payload["requires_provider"])

    def test_pr_reviewer_uses_fake_gh_report_only_and_blocks_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            fake_bin = home / "bin"
            fake_bin.mkdir()
            fake_gh = fake_bin / "gh"
            fake_gh.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env sh",
                        "set -eu",
                        "if [ \"$1 $2\" = \"pr list\" ]; then",
                        "  printf '%s\\n' '[{\"number\":7,\"title\":\"Fix bug\",\"url\":\"https://example/pr/7\",\"author\":{\"login\":\"dev\"}}]'",
                        "elif [ \"$1 $2\" = \"pr view\" ]; then",
                        "  printf '%s\\n' '{\"number\":7,\"title\":\"Fix bug\",\"url\":\"https://example/pr/7\"}'",
                        "elif [ \"$1 $2\" = \"pr diff\" ]; then",
                        "  printf '%s\\n' 'diff --git a/a b/a'",
                        "else",
                        "  printf '%s\\n' '{}'",
                        "fi",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            fake_gh.chmod(0o755)
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir, "PATH": f"{fake_bin}:{os.environ.get('PATH', '')}"}
            listing = self.run_agent("pr", "list-review-requests", "--json", env=env)
            natural = self.run_agent("--json", "quais", "PRs", "estao", "aguardando", "minha", "revisao?", env=env)
            review = self.run_agent("pr", "review", "7", "--json", env=env)
            blocked_write = self.run_agent("pr", "review", "7", "--approve", "--json", env=env)
            blocked_opt_in = self.run_agent("pr", "review", "7", "--approve", "--allow-write", "--json", env=env)

            self.assertEqual(listing.returncode, 0, listing.stderr)
            self.assertEqual(natural.returncode, 0, natural.stderr)
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertEqual(blocked_write.returncode, 2)
            self.assertEqual(blocked_opt_in.returncode, 2)
            self.assertEqual(json.loads(listing.stdout)["items"][0]["number"], 7)
            self.assertIn("#7 Fix bug", json.loads(natural.stdout)["response"])
            self.assertEqual(json.loads(review.stdout)["mode"], "report-only")
            self.assertTrue(json.loads(blocked_write.stdout)["requires_permission"])
            self.assertEqual(json.loads(blocked_opt_in.stdout)["mode"], "write-opt-in")
            self.assertTrue(json.loads(blocked_opt_in.stdout)["requires_permission"])

    def test_external_write_task_blocks_without_explicit_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            old_home = os.environ.get("AI_DEVKIT_CONFIG_HOME")
            os.environ["AI_DEVKIT_CONFIG_HOME"] = tmpdir
            try:
                task = create_task(
                    task_id="write-task",
                    title="Write task",
                    action={"type": "capability", "agent": "demo", "capability": "write", "external_writes": True},
                    permissions={"mode": "report-only"},
                )
                result = run_task(str(task["task"]["id"]))
            finally:
                if old_home is None:
                    os.environ.pop("AI_DEVKIT_CONFIG_HOME", None)
                else:
                    os.environ["AI_DEVKIT_CONFIG_HOME"] = old_home

            self.assertEqual(result["status"], "blocked")
            self.assertTrue(result["requires_permission"])
            self.assertEqual(result["task"]["run_count"], 0)

    def test_gh_failure_redacts_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            fake_bin = home / "bin"
            fake_bin.mkdir()
            fake_gh = fake_bin / "gh"
            token = "ghp_1234567890abcdefghijklmnop"
            fake_gh.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env sh",
                        f"printf '%s\\n' 'failed token={token}' >&2",
                        "exit 1",
                    ]
                ),
                encoding="utf-8",
            )
            fake_gh.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}:{old_path}"
            try:
                result = run_gh(["pr", "list"])
            finally:
                os.environ["PATH"] = old_path

            self.assertEqual(result["status"], "failed")
            self.assertNotIn(token, result["message"])
            self.assertIn("[REDACTED_SECRET]", result["message"])

    def test_gh_timeout_returns_failed_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            fake_bin = home / "bin"
            fake_bin.mkdir()
            fake_gh = fake_bin / "gh"
            fake_gh.write_text("#!/usr/bin/env sh\nsleep 2\n", encoding="utf-8")
            fake_gh.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            old_timeout = github_pr.GH_TIMEOUT_SECONDS
            os.environ["PATH"] = f"{fake_bin}:{old_path}"
            github_pr.GH_TIMEOUT_SECONDS = 1
            try:
                result = run_gh(["pr", "list"])
            finally:
                os.environ["PATH"] = old_path
                github_pr.GH_TIMEOUT_SECONDS = old_timeout

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["exit_code"], 124)

    def test_pr_automation_natural_prompt_creates_report_only_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            result = self.run_agent("--json", "revise", "todas", "as", "prs", "que", "recebo", "diariamente", env=env)

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "pr-automation-route")
            task = payload["result"]["task"]
            self.assertEqual(task["permissions"]["mode"], "report-only")
            self.assertFalse(task["permissions"]["approve"])


if __name__ == "__main__":
    unittest.main()
