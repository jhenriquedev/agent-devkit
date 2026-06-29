#!/usr/bin/env python3
"""Tests for the AWS Lambda Builder runners."""

from __future__ import annotations

import importlib.util
import json
import py_compile
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "agent"
AGENT_DIR = ROOT / "agents" / "aws-lambda-builder"
REPOSITORY_PATH = AGENT_DIR / "infra" / "integrations" / "aws-lambda" / "aws_lambda_repository.py"


def load_repository_module():
    spec = importlib.util.spec_from_file_location("aws_lambda_repository", REPOSITORY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load repository from {REPOSITORY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AwsLambdaBuilderRunnersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_module = load_repository_module()

    def write_spec(
        self,
        root: Path,
        *,
        lambda_name: str = "Orders Webhook",
        target_project: Path | None = None,
        runtime_family: str = "python",
        runtime: str = "python3.12",
        handler: str = "handler.lambda_handler",
        trigger: str = "api-gateway",
        deploy_strategy: str = "sam",
        env_value: str = "${APP_TABLE_NAME}",
        iam_action: str = "dynamodb:PutItem",
        iam_resource: str = "arn:aws:dynamodb:us-east-1:123456789012:table/orders",
        iam_justification: str = "",
        observability_extra: str = "  dlq_or_destination: arn:aws:sqs:us-east-1:123456789012:orders-dlq\n",
        purpose: str = "Receive order webhooks and enqueue normalized events.",
    ) -> Path:
        path = root / "lambda-spec.yaml"
        target_project_line = f"target_project: {target_project}\n" if target_project else ""
        path.write_text(
            f"""
lambda_name: {json.dumps(lambda_name)}
{target_project_line}purpose: {json.dumps(purpose)}
runtime_family: {json.dumps(runtime_family)}
runtime: {json.dumps(runtime)}
handler: {json.dumps(handler)}
trigger: {json.dumps(trigger)}
deploy_strategy: {json.dumps(deploy_strategy)}
timeout_seconds: 30
memory_mb: 256
input_schema:
  type: object
output_schema:
  type: object
environment_variables:
  - name: APP_TABLE_NAME
    value: {json.dumps(env_value)}
iam_permissions:
  - action: {json.dumps(iam_action)}
    resource: {json.dumps(iam_resource)}
    justification: {json.dumps(iam_justification)}
observability:
  structured_logging: true
{observability_extra}""".lstrip(),
            encoding="utf-8",
        )
        return path

    def test_plan_lambda_returns_plan_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.AwsLambdaRepository(root=root)

            result = repository.plan_lambda(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["lambda"]["slug"], "orders-webhook")
            self.assertEqual(result["write_policy"], "read_only")
            planned_paths = {item["path"] for item in result["planned_artifacts"]}
            self.assertGreaterEqual(planned_paths, {"src/handler.py", "tests/test_handler.py", "template.yaml"})
            self.assertFalse((root / "src").exists())

    def test_plan_lambda_reports_needs_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = root / "lambda-spec.yaml"
            spec_path.write_text("lambda_name: incomplete\n", encoding="utf-8")
            repository = self.repository_module.AwsLambdaRepository(root=root)

            result = repository.plan_lambda(spec_path=spec_path)

            self.assertEqual(result["status"], "needs-input")
            self.assertGreaterEqual(
                set(result["missing_fields"]),
                {
                    "purpose",
                    "runtime_family",
                    "runtime",
                    "handler",
                    "trigger",
                    "input_schema",
                    "output_schema",
                    "environment_variables",
                    "iam_permissions",
                    "observability",
                    "timeout_seconds",
                    "memory_mb",
                    "deploy_strategy",
                },
            )

    def test_plan_blocks_invalid_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, trigger="kinesis")
            repository = self.repository_module.AwsLambdaRepository(root=root)

            result = repository.plan_lambda(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "unsupported_trigger")

    def test_plan_blocks_invalid_runtime_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, runtime_family="ruby", runtime="ruby3.3")
            repository = self.repository_module.AwsLambdaRepository(root=root)

            result = repository.plan_lambda(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "unsupported_runtime_family")

    def test_plan_blocks_hardcoded_secret_env_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, env_value="plain-token", purpose="Uses API_TOKEN: plain-token")
            repository = self.repository_module.AwsLambdaRepository(root=root)

            result = repository.plan_lambda(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "security_guardrail_failed")
            codes = {finding["code"] for finding in result["findings"]}
            self.assertIn("hardcoded_secret_marker", codes)

    def test_plan_blocks_iam_wildcard_without_justification(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, iam_action="dynamodb:*", iam_resource="*")
            repository = self.repository_module.AwsLambdaRepository(root=root)

            result = repository.plan_lambda(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            codes = {finding["code"] for finding in result["findings"]}
            self.assertIn("iam_action_wildcard_without_justification", codes)

    def test_review_lambda_security_warns_resource_wildcard_when_justified(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(
                root,
                iam_action="dynamodb:*",
                iam_resource="*",
                iam_justification="temporary bootstrap until table ARNs are known",
            )
            repository = self.repository_module.AwsLambdaRepository(root=root)

            result = repository.review_lambda_security(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            self.assertTrue(result["valid"])
            codes = {finding["code"] for finding in result["findings"]}
            self.assertIn("iam_resource_wildcard", codes)

    def test_generate_lambda_project_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.AwsLambdaRepository(root=root)

            result = repository.generate_lambda_project(spec_path=spec_path)

            self.assertEqual(result["status"], "planned")
            self.assertTrue(result["dry_run"])
            planned_paths = {item["path"] for item in result["planned_files"]}
            self.assertGreaterEqual(
                planned_paths,
                {
                    "orders-webhook/src/handler.py",
                    "orders-webhook/tests/test_handler.py",
                    "orders-webhook/events/api-gateway.json",
                    "orders-webhook/template.yaml",
                },
            )
            self.assertFalse((target_project / "orders-webhook").exists())

    def test_generate_python_project_execute_writes_inside_target_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.AwsLambdaRepository(root=root)

            result = repository.generate_lambda_project(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "written")
            handler = target_project / "orders-webhook" / "src" / "handler.py"
            self.assertTrue(handler.exists())
            py_compile.compile(str(handler), doraise=True)
            for item in result["written_files"]:
                path = Path(item["path"]).resolve()
                self.assertTrue(path.is_relative_to(target_project.resolve()), item["path"])

    def test_generate_node_project_execute_writes_node_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(
                root,
                target_project=target_project,
                runtime_family="nodejs",
                runtime="nodejs20.x",
                handler="handler.handler",
                trigger="sqs",
            )
            repository = self.repository_module.AwsLambdaRepository(root=root)

            result = repository.generate_lambda_project(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "written")
            self.assertTrue((target_project / "orders-webhook" / "src" / "handler.js").exists())
            self.assertTrue((target_project / "orders-webhook" / "tests" / "handler.test.js").exists())
            self.assertTrue((target_project / "orders-webhook" / "package.json").exists())

    def test_generate_lambda_project_blocks_overwrite_without_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target-project"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.AwsLambdaRepository(root=root)
            repository.generate_lambda_project(spec_path=spec_path, execute=True)

            result = repository.generate_lambda_project(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "target_exists")

    def test_package_lambda_dry_run_does_not_create_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project = self.write_project(root)
            repository = self.repository_module.AwsLambdaRepository(root=root)

            result = repository.package_lambda(project_path=project)

            self.assertEqual(result["status"], "planned")
            self.assertTrue(result["dry_run"])
            self.assertFalse(Path(result["archive_path"]).exists())
            self.assertIn("src/handler.py", result["files"])

    def test_package_lambda_execute_creates_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project = self.write_project(root)
            repository = self.repository_module.AwsLambdaRepository(root=root)

            result = repository.package_lambda(project_path=project, execute=True)

            self.assertEqual(result["status"], "written")
            archive = Path(result["archive_path"])
            self.assertTrue(archive.exists())
            with zipfile.ZipFile(archive) as package:
                names = set(package.namelist())
            self.assertIn("src/handler.py", names)
            self.assertNotIn(".env", names)

    def test_deploy_lambda_plan_never_executes_real_deploy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.AwsLambdaRepository(root=root)

            result = repository.deploy_lambda_plan(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            self.assertFalse(result["deploy_real"])
            self.assertEqual(result["write_policy"], "dry_run")
            self.assertIn("sam deploy", " ".join(result["commands_to_review"]))
            self.assertIn("sam deploy", result["blocked_actions"])

    def test_plan_lambda_runner_is_executable_through_agent_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = self.write_spec(Path(tmpdir))

            result = subprocess.run(
                [
                    sys.executable,
                    str(AGENT),
                    "--json",
                    "run",
                    "aws-lambda-builder",
                    "plan-lambda",
                    "--spec",
                    str(spec_path),
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
        self.assertEqual(runner_payload["lambda"]["slug"], "orders-webhook")

    def write_project(self, root: Path) -> Path:
        project = root / "orders-webhook"
        (project / "src").mkdir(parents=True)
        (project / "events").mkdir()
        (project / "src" / "handler.py").write_text("def lambda_handler(event, context):\n    return {}\n", encoding="utf-8")
        (project / "events" / "api-gateway.json").write_text("{}", encoding="utf-8")
        (project / ".env").write_text("SECRET=value\n", encoding="utf-8")
        return project


if __name__ == "__main__":
    unittest.main()
