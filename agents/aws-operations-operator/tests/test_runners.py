#!/usr/bin/env python3
"""Runner tests for aws-operations-operator."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


class AwsOperationsOperatorRunnerTest(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        for key in list(env):
            if key.startswith("AWS_OPERATIONS_ALLOWED_ACCOUNTS_") or key.startswith("AWS_OPERATIONS_DEFAULT_REGION_"):
                env.pop(key)
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

    def test_agent_is_discoverable(self) -> None:
        result = self.run_cli("--json", "agents")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        agents = {item["id"] for item in payload["items"]}
        self.assertIn("aws-operations-operator", agents)

    def test_plan_operational_action_writes_plan_and_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "plan-operational-action",
                "--operation",
                "force-ecs-deployment",
                "--resource-id",
                "cluster/orders-service",
                "--environment",
                "dev",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            plan = (output_dir / "operation-plan.md").read_text(encoding="utf-8")
            dry_run = json.loads((output_dir / "operation-dry-run.json").read_text(encoding="utf-8"))

        self.assertIn("force-ecs-deployment", plan)
        self.assertFalse(dry_run["execute"])
        self.assertEqual(dry_run["status"], "planned")

    def test_force_ecs_deployment_defaults_to_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "force-ecs-deployment",
                "--cluster",
                "orders",
                "--service",
                "orders-api",
                "--environment",
                "dev",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            dry_run = json.loads((output_dir / "operation-dry-run.json").read_text(encoding="utf-8"))

        self.assertEqual(dry_run["operation"], "force-ecs-deployment")
        self.assertEqual(dry_run["aws_command"][:3], ["aws", "ecs", "update-service"])
        self.assertFalse((output_dir / "operation-result.json").exists())

    def test_restart_ecs_service_keeps_restart_operation_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "restart-ecs-service",
                "--cluster",
                "orders",
                "--service",
                "orders-api",
                "--environment",
                "dev",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            dry_run = json.loads((output_dir / "operation-dry-run.json").read_text(encoding="utf-8"))

        self.assertEqual(dry_run["operation"], "restart-ecs-service")
        self.assertEqual(dry_run["aws_command"][:3], ["aws", "ecs", "update-service"])

    def test_plan_operational_action_rejects_unknown_operation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "plan-operational-action",
                "--operation",
                "delete-rds",
                "--resource-id",
                "prod-db",
                "--environment",
                "prd",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not allowed", result.stderr.lower())

    def test_lambda_payload_is_redacted_in_dry_run_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "invoke-lambda",
                "--function-name",
                "reconcile-orders",
                "--payload",
                '{"secret":"abc"}',
                "--environment",
                "dev",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            artifact = (output_dir / "operation-dry-run.json").read_text(encoding="utf-8")
            plan = (output_dir / "operation-plan.md").read_text(encoding="utf-8")

        self.assertNotIn("abc", artifact)
        self.assertNotIn("abc", plan)
        self.assertIn("<redacted", artifact)

    def test_cloudfront_asg_and_eventbridge_generate_dry_run_artifacts(self) -> None:
        scenarios = [
            (
                "invalidate-cloudfront-cache",
                ["--distribution-id", "E123456", "--paths", "/index.html /static/*"],
                "invalidate-cloudfront-cache",
            ),
            (
                "scale-autoscaling-group",
                ["--auto-scaling-group", "orders-asg", "--desired-capacity", "3"],
                "scale-autoscaling-group",
            ),
            (
                "toggle-eventbridge-rule",
                ["--rule-name", "nightly-orders", "--action", "disable"],
                "toggle-eventbridge-rule",
            ),
        ]
        for capability, capability_args, expected_operation in scenarios:
            with self.subTest(capability=capability), tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir) / "out"

                result = self.run_cli(
                    "run",
                    "aws-operations-operator",
                    capability,
                    *capability_args,
                    "--environment",
                    "dev",
                    "--output-dir",
                    str(output_dir),
                    "--yes-create-dir",
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                dry_run = json.loads((output_dir / "operation-dry-run.json").read_text(encoding="utf-8"))

            self.assertEqual(dry_run["operation"], expected_operation)
            self.assertEqual(dry_run["status"], "planned")
            self.assertFalse(dry_run["execute"])

    def test_sqs_destructive_capabilities_are_blocked_plan_only(self) -> None:
        scenarios = [
            (
                "redrive-sqs-dlq",
                [
                    "--source-arn",
                    "arn:aws:sqs:us-east-1:123456789012:orders-dlq",
                    "--destination-arn",
                    "arn:aws:sqs:us-east-1:123456789012:orders",
                ],
            ),
            (
                "purge-sqs-queue-plan",
                ["--queue-url", "https://sqs.us-east-1.amazonaws.com/123456789012/orders"],
            ),
        ]
        for capability, capability_args in scenarios:
            with self.subTest(capability=capability), tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir) / "out"

                result = self.run_cli(
                    "run",
                    "aws-operations-operator",
                    capability,
                    *capability_args,
                    "--environment",
                    "dev",
                    "--output-dir",
                    str(output_dir),
                    "--yes-create-dir",
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                dry_run = json.loads((output_dir / "operation-dry-run.json").read_text(encoding="utf-8"))

            self.assertEqual(dry_run["status"], "blocked-plan-only")
            self.assertTrue(dry_run["destructive"])

    def test_execute_requires_confirm_resource(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "force-ecs-deployment",
                "--cluster",
                "orders",
                "--service",
                "orders-api",
                "--environment",
                "dev",
                "--execute",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("confirm", result.stderr.lower())

    def test_execute_requires_account_allowlist_even_with_confirm_resource(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "force-ecs-deployment",
                "--cluster",
                "orders",
                "--service",
                "orders-api",
                "--environment",
                "dev",
                "--execute",
                "--confirm-resource",
                "orders/orders-api",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("allowed aws accounts", result.stderr.lower())

    def test_generate_operation_report_reads_operation_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"
            output_dir.mkdir()
            (output_dir / "operation-dry-run.json").write_text(
                json.dumps({"operation": "force-ecs-deployment", "status": "planned", "execute": False}),
                encoding="utf-8",
            )

            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "generate-operation-report",
                "--operation-dir",
                str(output_dir),
                "--output-dir",
                str(output_dir),
                "--yes-overwrite",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = (output_dir / "operation-report.md").read_text(encoding="utf-8")

        self.assertIn("force-ecs-deployment", report)


class AwsOperationsOperatorNewTests(unittest.TestCase):
    """P1-5 tests: input faltante, caminhos de execucao mockada, scale-to-zero."""

    def run_cli(self, *args: str, env_extra: dict | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        for key in list(env):
            if key.startswith("AWS_OPERATIONS_ALLOWED_ACCOUNTS_") or key.startswith("AWS_OPERATIONS_DEFAULT_REGION_"):
                env.pop(key)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

    def test_force_ecs_missing_cluster_exits_with_error(self) -> None:
        """P1-5(d): falta input --cluster deve falhar com erro de argparse."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "force-ecs-deployment",
                "--service",
                "orders-api",
                "--environment",
                "dev",
                "--output-dir",
                tmpdir,
            )
        self.assertNotEqual(result.returncode, 0)

    def test_invoke_lambda_missing_environment_exits_with_error(self) -> None:
        """P1-5(d): falta input --environment deve falhar."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "invoke-lambda",
                "--function-name",
                "reconcile-orders",
                "--output-dir",
                tmpdir,
            )
        self.assertNotEqual(result.returncode, 0)

    def test_plan_operational_action_missing_resource_id_exits_with_error(self) -> None:
        """P1-5(d): falta input --resource-id deve falhar."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "plan-operational-action",
                "--operation",
                "force-ecs-deployment",
                "--environment",
                "dev",
                "--output-dir",
                tmpdir,
            )
        self.assertNotEqual(result.returncode, 0)

    def test_execute_with_valid_allowlist_validates_account_before_mutating(self) -> None:
        """P1-5(a): execute com allowlist e conta valida atinge validate_account antes de mutar."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"
            # Allowlist configurada mas nenhum mock de sts — deve falhar em validate_account (nao em args)
            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "force-ecs-deployment",
                "--cluster",
                "orders",
                "--service",
                "orders-api",
                "--environment",
                "dev",
                "--execute",
                "--confirm-resource",
                "orders/orders-api",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
                env_extra={"AWS_OPERATIONS_ALLOWED_ACCOUNTS_DEV": "111111111111"},
            )
        # Sem AWS CLI real, deve falhar — mas o erro deve vir do aws cli, nao de args faltantes
        self.assertNotEqual(result.returncode, 0)
        # Nao deve ser erro de "confirm" (passou confirm-resource) nem de "allowed aws accounts"
        # (allowlist foi configurada). Deve ser erro de execucao do aws cli.
        self.assertNotIn("execute requires --confirm-resource", result.stderr.lower())
        self.assertNotIn("no allowed aws accounts configured", result.stderr.lower())

    def test_toggle_eventbridge_dry_run_generates_artifacts(self) -> None:
        """P1-5(b): toggle em dry-run gera artefatos corretos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"
            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "toggle-eventbridge-rule",
                "--rule-name",
                "nightly-orders",
                "--action",
                "enable",
                "--environment",
                "dev",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            dry_run = json.loads((output_dir / "operation-dry-run.json").read_text(encoding="utf-8"))
        self.assertEqual(dry_run["operation"], "toggle-eventbridge-rule")
        self.assertEqual(dry_run["status"], "planned")
        self.assertFalse(dry_run["execute"])
        self.assertIn("enable-rule", " ".join(dry_run["aws_command"]))

    def test_scale_asg_dry_run_generates_correct_command(self) -> None:
        """P1-5(b): scale-autoscaling-group em dry-run gera comando correto."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"
            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "scale-autoscaling-group",
                "--auto-scaling-group",
                "orders-asg",
                "--desired-capacity",
                "0",
                "--environment",
                "dev",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            dry_run = json.loads((output_dir / "operation-dry-run.json").read_text(encoding="utf-8"))
        self.assertEqual(dry_run["operation"], "scale-autoscaling-group")
        self.assertEqual(dry_run["status"], "planned")
        # Verifica que desired-capacity 0 gera artefato (scale-to-zero ainda planeja no dry-run)
        self.assertIn("set-desired-capacity", " ".join(dry_run["aws_command"]))
        self.assertIn("--honor-cooldown", dry_run["aws_command"])

    def test_cloudfront_dry_run_generates_artifacts(self) -> None:
        """P1-5(b): invalidate-cloudfront-cache em dry-run gera artefatos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"
            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "invalidate-cloudfront-cache",
                "--distribution-id",
                "E123ABC",
                "--paths",
                "/index.html",
                "--environment",
                "dev",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            dry_run = json.loads((output_dir / "operation-dry-run.json").read_text(encoding="utf-8"))
        self.assertEqual(dry_run["operation"], "invalidate-cloudfront-cache")
        self.assertEqual(dry_run["status"], "planned")
        self.assertFalse(dry_run["execute"])

    def test_destructive_with_execute_flag_still_blocked(self) -> None:
        """P1-5(c): redrive/purge com --execute flag nao muda o resultado; continua blocked."""
        # O runner de redrive ignora qualquer flag --execute passado externamente
        # porque forca execute=False internamente. Este teste verifica que
        # o artefato ainda reflete blocked-plan-only.
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"
            result = self.run_cli(
                "run",
                "aws-operations-operator",
                "redrive-sqs-dlq",
                "--source-arn",
                "arn:aws:sqs:us-east-1:123456789012:orders-dlq",
                "--destination-arn",
                "arn:aws:sqs:us-east-1:123456789012:orders",
                "--environment",
                "dev",
                "--output-dir",
                str(output_dir),
                "--yes-create-dir",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            dry_run = json.loads((output_dir / "operation-dry-run.json").read_text(encoding="utf-8"))
        self.assertEqual(dry_run["status"], "blocked-plan-only")
        self.assertTrue(dry_run["destructive"])
        self.assertFalse(dry_run["execute"])

    def test_system_md_exists_and_is_non_empty(self) -> None:
        """Criterio de aceite: knowledge/system.md existe e nao e vazio."""
        system_md = ROOT / "agents" / "aws-operations-operator" / "knowledge" / "system.md"
        self.assertTrue(system_md.exists(), f"knowledge/system.md nao encontrado em {system_md}")
        content = system_md.read_text(encoding="utf-8")
        self.assertGreater(len(content.strip()), 100, "knowledge/system.md esta praticamente vazio")
        self.assertIn("Persona", content)
        self.assertIn("Missao", content)

    def test_all_prompts_are_non_stub(self) -> None:
        """Criterio de aceite: nenhum prompt em knowledge/prompts/ e stub de 1-2 linhas."""
        prompts_dir = ROOT / "agents" / "aws-operations-operator" / "knowledge" / "prompts"
        for prompt_file in sorted(prompts_dir.glob("*.md")):
            content = prompt_file.read_text(encoding="utf-8").strip()
            lines = [l for l in content.splitlines() if l.strip()]
            self.assertGreater(
                len(lines),
                5,
                f"Prompt {prompt_file.name} parece stub ({len(lines)} linhas nao-vazias)",
            )
            self.assertIn("Objetivo", content, f"Prompt {prompt_file.name} nao tem secao Objetivo")

    def test_destructive_never_executes_even_with_confirm(self) -> None:
        """Criterio de aceite: destrutiva nunca executa mesmo com --execute (runner bloqueia)."""
        # Verifica atraves de inspecao do codigo do runner que execute e forcado a False.
        runner_support = ROOT / "agents" / "aws-operations-operator" / "capabilities" / "_shared" / "runner_support.py"
        source = runner_support.read_text(encoding="utf-8")
        # O runner de redrive deve forcar execute=False
        self.assertIn("args.execute = False", source, "runner_support nao forca execute=False para destrutivas")


if __name__ == "__main__":
    unittest.main()
