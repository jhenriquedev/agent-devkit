#!/usr/bin/env python3
"""Wave 6 contracts for permissions, dry-run, and audit."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cli.aikit.audit import redact_value
from cli.aikit.cli_dispatch import add_payload_warning
from cli.aikit.main import main
from cli.aikit.permissions import grant_permission, permission_check, permissions_json_path
from cli.aikit.tasks import create_task, run_task


AGENT = ROOT / "agent"
CLI_TIMEOUT_SECONDS = int(os.environ.get("AI_DEVKIT_TEST_CLI_TIMEOUT_SECONDS", "60"))


class AgenticWave6ContractsTest(unittest.TestCase):
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

    def test_permissions_default_grant_and_revoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            show = self.run_agent("permissions", "show", "--json", env=env)
            grant = self.run_agent("permissions", "grant", "github-pr-reviewer", "github", "comment-with-approval", "--json", env=env)
            revoke = self.run_agent("permissions", "revoke", "github-pr-reviewer", "github", "comment-with-approval", "--json", env=env)

            self.assertEqual(show.returncode, 0, show.stderr)
            self.assertEqual(grant.returncode, 0, grant.stderr)
            self.assertEqual(revoke.returncode, 0, revoke.stderr)
            self.assertEqual(json.loads(show.stdout)["default_level"], "read-only")
            self.assertEqual(json.loads(grant.stdout)["grant"]["level"], "comment-with-approval")
            self.assertEqual(json.loads(revoke.stdout)["status"], "revoked")

    def test_permission_check_treats_invalid_stored_level_as_default_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            old_home = os.environ.get("AI_DEVKIT_CONFIG_HOME")
            os.environ["AI_DEVKIT_CONFIG_HOME"] = tmpdir
            try:
                path = permissions_json_path()
                path.write_text(
                    json.dumps(
                        {
                            "version": 1,
                            "default_level": "invalid-default",
                            "grants": [
                                {
                                    "agent": "github-pr-reviewer",
                                    "provider": "github",
                                    "level": "invalid-grant",
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                read_check = permission_check(agent="github-pr-reviewer", provider="github", action="read")
                write_check = permission_check(agent="github-pr-reviewer", provider="github", action="write")
            finally:
                if old_home is None:
                    os.environ.pop("AI_DEVKIT_CONFIG_HOME", None)
                else:
                    os.environ["AI_DEVKIT_CONFIG_HOME"] = old_home

            self.assertTrue(read_check["ok"])
            self.assertEqual(read_check["granted_level"], "read-only")
            self.assertFalse(write_check["ok"])
            self.assertEqual(write_check["granted_level"], "read-only")

    def test_pr_write_requires_permission_and_executes_with_grant(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            fake_bin = home / "bin"
            fake_bin.mkdir()
            log = home / "gh.log"
            fake_gh = fake_bin / "gh"
            fake_gh.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env sh",
                        "set -eu",
                        f"printf '%s\\n' \"$*\" >> {log}",
                        "if [ \"$1 $2\" = \"pr review\" ]; then",
                        "  printf '%s\\n' '{\"submitted\":true}'",
                        "else",
                        "  printf '%s\\n' '[]'",
                        "fi",
                    ]
                ),
                encoding="utf-8",
            )
            fake_gh.chmod(0o755)
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir, "PATH": f"{fake_bin}:{os.environ.get('PATH', '')}"}

            blocked = self.run_agent("pr", "review", "7", "--approve", "--allow-write", "--json", env=env)
            grant = self.run_agent("permissions", "grant", "github-pr-reviewer", "github", "write-with-approval", "--json", env=env)
            submitted = self.run_agent("pr", "review", "7", "--approve", "--allow-write", "--json", env=env)

            self.assertEqual(blocked.returncode, 2)
            self.assertEqual(grant.returncode, 0, grant.stderr)
            self.assertEqual(submitted.returncode, 0, submitted.stderr)
            self.assertEqual(json.loads(blocked.stdout)["status"], "blocked")
            self.assertEqual(json.loads(submitted.stdout)["status"], "ok")
            self.assertIn("pr review 7 --approve", log.read_text(encoding="utf-8"))

    def test_external_write_task_respects_permission_grant(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            old_home = os.environ.get("AI_DEVKIT_CONFIG_HOME")
            os.environ["AI_DEVKIT_CONFIG_HOME"] = tmpdir
            try:
                task = create_task(
                    task_id="write-task",
                    title="Write task",
                    action={
                        "type": "capability",
                        "agent": "github-pr-reviewer",
                        "provider": "github",
                        "capability": "review-pr-diff",
                        "external_writes": True,
                        "required_action": "write",
                    },
                    permissions={"mode": "report-only"},
                )
                blocked = run_task(str(task["task"]["id"]))
                grant_permission("github-pr-reviewer", "github", "write-with-approval")
                allowed = run_task(str(task["task"]["id"]))
            finally:
                if old_home is None:
                    os.environ.pop("AI_DEVKIT_CONFIG_HOME", None)
                else:
                    os.environ["AI_DEVKIT_CONFIG_HOME"] = old_home

            self.assertEqual(blocked["status"], "blocked")
            self.assertEqual(allowed["status"], "ok")
            self.assertEqual(allowed["task"]["run_count"], 1)

    def test_global_dry_run_natural_pr_prompt_does_not_create_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            result = self.run_agent("--json", "--dry-run", "revise", "todas", "as", "prs", "que", "recebo", "diariamente", env=env)
            tasks = self.run_agent("task", "list", "--json", env=env)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(tasks.returncode, 0, tasks.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["mode"], "pr-dry-run")
            self.assertEqual(json.loads(tasks.stdout)["items"], [])

    def test_global_dry_run_direct_pr_automation_does_not_create_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            result = self.run_agent("--json", "--dry-run", "pr", "automation", "create", "--time", "08:30", env=env)
            tasks = self.run_agent("task", "list", "--json", env=env)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(tasks.returncode, 0, tasks.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "planned")
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["task"]["schedule"]["time"], "08:30")
            self.assertEqual(json.loads(tasks.stdout)["items"], [])

    def test_global_dry_run_reaches_setup_toolchain_and_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "consumer project"
            target.mkdir()
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            setup = self.run_agent("--json", "--dry-run", "setup", "plan", "--yes", env=env)
            toolchain = self.run_agent("--json", "--dry-run", "toolchain", "install", "gh-cli", "--yes", env=env)
            install = self.run_agent("--json", "--dry-run", "install", "project", "--target", str(target), env=env)

            self.assertEqual(setup.returncode, 0, setup.stderr)
            self.assertEqual(toolchain.returncode, 0, toolchain.stderr)
            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertTrue(json.loads(setup.stdout)["dry_run"])
            self.assertTrue(json.loads(toolchain.stdout)["dry_run"])
            self.assertTrue(json.loads(install.stdout)["dry_run"])
            self.assertFalse((target / "AGENTS.md").exists())

    def test_audit_generated_and_redacts_secret_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            token = "ghp_1234567890abcdefghijklmnop"
            env = {"AI_DEVKIT_CONFIG_HOME": tmpdir}
            result = self.run_agent("--json", "oi", "vc", "esta", "vivo?", f"token={token}", env=env)
            audits = self.run_agent("audit", "list", "--json", env=env)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(audits.returncode, 0, audits.stderr)
            items = json.loads(audits.stdout)["items"]
            self.assertGreaterEqual(len(items), 1)
            show = self.run_agent("audit", "show", str(items[0]["id"]), "--json", env=env)
            export = self.run_agent("audit", "export", str(items[0]["id"]), "--format", "md", "--json", env=env)

            self.assertEqual(show.returncode, 0, show.stderr)
            self.assertEqual(export.returncode, 0, export.stderr)
            self.assertEqual(json.loads(show.stdout)["entry"]["origin"], "cli")
            self.assertNotIn(token, show.stdout)
            self.assertNotIn(token, export.stdout)
            self.assertIn("[REDACTED_SECRET]", show.stdout)
            self.assertIn("- Origin: `cli`", json.loads(export.stdout)["content"])

    def test_audit_redacts_camel_case_secret_keys_without_redacting_token_metrics(self) -> None:
        payload = redact_value(
            {
                "accessToken": "plain-secret-value",
                "clientSecret": "another-secret-value",
                "apiKey": "api-secret-value",
                "token_estimate": 123,
                "usage": {"total_tokens": 456},
            }
        )

        self.assertEqual(payload["accessToken"], "[REDACTED_SECRET]")
        self.assertEqual(payload["clientSecret"], "[REDACTED_SECRET]")
        self.assertEqual(payload["apiKey"], "[REDACTED_SECRET]")
        self.assertEqual(payload["token_estimate"], 123)
        self.assertEqual(payload["usage"]["total_tokens"], 456)

    def test_audit_failure_is_reported_in_json_without_blocking_command(self) -> None:
        token = "ghp_1234567890abcdefghijklmnop"
        stdout = StringIO()
        stderr = StringIO()
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.dict(os.environ, {"AI_DEVKIT_CONFIG_HOME": tmpdir}), mock.patch(
            "cli.aikit.cli_dispatch.record_audit",
            side_effect=RuntimeError(f"audit failed token={token}"),
        ):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(["--json", "commands"], prog="agent")

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["kind"], "commands")
        self.assertIn("audit_warning", payload)
        self.assertIn("warnings", payload)
        warning = payload["audit_warning"]
        self.assertEqual(warning["kind"], "audit-warning")
        self.assertEqual(warning["code"], "audit_record_failed")
        self.assertEqual(warning["status"], "not-recorded")
        self.assertEqual(warning["reason"], "unknown-audit-error")
        self.assertEqual(warning["message"], "Audit trail could not be written.")
        self.assertFalse(warning["required"])
        self.assertNotIn("error", warning)
        self.assertNotIn(token, json.dumps(warning))
        self.assertEqual(payload["warnings"], [warning])
        self.assertEqual(stderr.getvalue(), "")

    def test_audit_failure_reason_is_classified_without_exception_detail(self) -> None:
        stdout = StringIO()
        stderr = StringIO()
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.dict(os.environ, {"AI_DEVKIT_CONFIG_HOME": tmpdir}), mock.patch(
            "cli.aikit.cli_dispatch.record_audit",
            side_effect=PermissionError("permission denied at /secret/path token=ghp_1234567890abcdefghijklmnop"),
        ):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(["--json", "commands"], prog="agent")

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        warning = payload["audit_warning"]
        self.assertEqual(warning["reason"], "permission-denied")
        self.assertEqual(warning["message"], "Audit trail could not be written.")
        self.assertNotIn("secret", json.dumps(warning).lower())
        self.assertNotIn("ghp_", json.dumps(warning))
        self.assertEqual(stderr.getvalue(), "")

    def test_audit_failure_is_reported_in_human_output_without_blocking_command(self) -> None:
        stdout = StringIO()
        stderr = StringIO()
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.dict(os.environ, {"AI_DEVKIT_CONFIG_HOME": tmpdir}), mock.patch(
            "cli.aikit.cli_dispatch.record_audit",
            side_effect=RuntimeError("audit path denied"),
        ):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(["commands"], prog="agent")

        self.assertEqual(exit_code, 0)
        self.assertIn("Warnings:", stdout.getvalue())
        self.assertIn("audit trail was not recorded", stdout.getvalue())
        self.assertIn("unknown-audit-error", stdout.getvalue())
        self.assertNotIn("audit path denied", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_audit_failure_during_command_error_is_reported_on_stderr(self) -> None:
        token = "ghp_1234567890abcdefghijklmnop"
        stdout = StringIO()
        stderr = StringIO()
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.dict(os.environ, {"AI_DEVKIT_CONFIG_HOME": tmpdir}), mock.patch(
            "cli.aikit.cli_dispatch.record_audit",
            side_effect=RuntimeError(f"audit failed token={token}"),
        ):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(["provider", "status", "missing-provider"], prog="agent")

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("warning: Audit trail could not be written.", stderr.getvalue())
        self.assertIn("unknown-audit-error", stderr.getvalue())
        self.assertIn("error: provider not found: missing-provider", stderr.getvalue())
        self.assertNotIn(token, stderr.getvalue())

    def test_audit_warning_preserves_existing_scalar_warning(self) -> None:
        result = {"kind": "example", "warnings": "legacy warning"}
        warning = {"kind": "audit-warning", "message": "Audit recording failed."}

        add_payload_warning(result, warning)

        self.assertEqual(result["warnings"], ["legacy warning", warning])


if __name__ == "__main__":
    unittest.main()
