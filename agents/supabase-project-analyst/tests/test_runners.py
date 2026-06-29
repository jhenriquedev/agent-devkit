#!/usr/bin/env python3
"""Tests for the Supabase Project Analyst runners."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "agent"
AGENT_DIR = ROOT / "agents" / "supabase-project-analyst"
REPOSITORY_PATH = (
    AGENT_DIR
    / "infra"
    / "integrations"
    / "supabase-project"
    / "supabase_project_repository.py"
)


def load_repository_module():
    spec = importlib.util.spec_from_file_location("supabase_project_repository", REPOSITORY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load repository from {REPOSITORY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SupabaseProjectAnalystRunnersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_module = load_repository_module()

    def write_project(self, root: Path) -> Path:
        supabase = root / "supabase"
        migrations = supabase / "migrations"
        functions = supabase / "functions" / "webhook"
        migrations.mkdir(parents=True)
        functions.mkdir(parents=True)
        (supabase / "config.toml").write_text(
            """
project_id = "local-project"
[api]
schemas = ["public", "storage"]
[auth]
site_url = "http://localhost:3000"
additional_redirect_urls = ["postgresql://user:pass@example.com/app"]
""".lstrip(),
            encoding="utf-8",
        )
        (root / ".env").write_text(
            "SUPABASE_SERVICE_ROLE_KEY=secret-value\nSUPABASE_DB_URL=postgresql://user:pass@localhost/db\nSUPABASE_ANON_KEY=anon-secret\n",
            encoding="utf-8",
        )
        (migrations / "20260101010101_init.sql").write_text(
            """
create table public.orders (
  id uuid primary key,
  user_id uuid not null,
  raw_user_meta_data jsonb
);

create table public.public_notes (
  id bigint generated always as identity primary key,
  body text
);
alter table public.orders enable row level security;

create policy "orders read" on public.orders
for select to authenticated
using (true);

create policy "orders update" on public.orders
for update to authenticated
using ((select auth.uid()) = user_id);

create policy "orders role" on public.orders
for select
using (auth.role() = 'authenticated');

create policy "public files" on storage.objects
for select to anon
using (true);

create view public.order_view as select * from public.orders;

create function public.admin_orders()
returns setof public.orders
language sql
security definer
as $$
  select * from public.orders;
$$;

grant select on public.orders to authenticated;
drop table public.legacy_orders;
""".lstrip(),
            encoding="utf-8",
        )
        (functions / "index.ts").write_text(
            """
const serviceRole = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
const userMetadata = event.user.user_metadata.role;
console.log(serviceRole, userMetadata);
""".lstrip(),
            encoding="utf-8",
        )
        return root

    def test_inspect_supabase_project_reads_local_context_without_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = self.write_project(Path(tmpdir))
            repository = self.repository_module.SupabaseProjectRepository()

            result = repository.inspect_supabase_project(project_path=project)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["write_policy"], "read_only")
            self.assertEqual(result["context"]["migrations_count"], 1)
            self.assertEqual(result["context"]["edge_functions"], ["webhook"])
            rendered = json.dumps(result)
            self.assertNotIn("secret-value", rendered)
            self.assertNotIn("anon-secret", rendered)
            self.assertNotIn("postgresql://user:pass@localhost/db", rendered)
            self.assertNotIn("postgresql://user:pass@example.com/app", rendered)

    def test_audit_rls_policies_detects_common_supabase_risks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = self.write_project(Path(tmpdir))
            repository = self.repository_module.SupabaseProjectRepository()

            result = repository.audit_rls_policies(project_path=project)

            codes = {finding["code"] for finding in result["findings"]}
            self.assertIn("exposed_table_without_rls", codes)
            self.assertIn("authenticated_without_ownership", codes)
            self.assertIn("deprecated_auth_role", codes)
            self.assertIn("update_policy_without_with_check", codes)

    def test_audit_auth_security_detects_metadata_and_service_role(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = self.write_project(Path(tmpdir))
            repository = self.repository_module.SupabaseProjectRepository()

            result = repository.audit_auth_security(project_path=project)

            codes = {finding["code"] for finding in result["findings"]}
            self.assertIn("user_metadata_authorization", codes)
            self.assertIn("service_role_reference", codes)
            self.assertIn("local_env_secret_present", codes)
            rendered = json.dumps(result)
            self.assertNotIn("secret-value", rendered)

    def test_audit_storage_policies_detects_public_storage_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = self.write_project(Path(tmpdir))
            repository = self.repository_module.SupabaseProjectRepository()

            result = repository.audit_storage_policies(project_path=project)

            codes = {finding["code"] for finding in result["findings"]}
            self.assertIn("storage_public_policy", codes)

    def test_review_migrations_detects_dangerous_constructs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = self.write_project(Path(tmpdir))
            repository = self.repository_module.SupabaseProjectRepository()

            result = repository.review_migrations(project_path=project)

            codes = {finding["code"] for finding in result["findings"]}
            self.assertIn("destructive_ddl", codes)
            self.assertIn("security_definer_function", codes)
            self.assertIn("view_without_security_invoker", codes)
            self.assertIn("broad_grant_to_public_roles", codes)

    def test_generate_supabase_report_consolidates_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = self.write_project(Path(tmpdir))
            repository = self.repository_module.SupabaseProjectRepository()

            result = repository.generate_supabase_report(project_path=project)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["write_policy"], "output_only")
            self.assertGreater(result["summary"]["findings"], 5)
            self.assertTrue(result["recommendations"])

    def test_plan_supabase_fix_is_dry_run_and_does_not_apply_sql(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = self.write_project(Path(tmpdir))
            repository = self.repository_module.SupabaseProjectRepository()

            result = repository.plan_supabase_fix(project_path=project)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["write_policy"], "dry_run")
            self.assertFalse(result["apply_real"])
            self.assertIn("execute_sql", result["blocked_actions"])
            self.assertTrue(all(action["apply_real"] is False for action in result["actions"]))

    def test_inspect_runner_is_executable_through_agent_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = self.write_project(Path(tmpdir))

            result = subprocess.run(
                [
                    sys.executable,
                    str(AGENT),
                    "--json",
                    "run",
                    "supabase-project-analyst",
                    "inspect-supabase-project",
                    "--project-path",
                    str(project),
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        runner_payload = json.loads(payload["stdout"])
        self.assertEqual(runner_payload["status"], "ok")
        self.assertEqual(runner_payload["context"]["migrations_count"], 1)


if __name__ == "__main__":
    unittest.main()
