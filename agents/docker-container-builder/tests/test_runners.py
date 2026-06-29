#!/usr/bin/env python3
"""Tests for the Docker Container Builder runners."""

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
AGENT_DIR = ROOT / "agents" / "docker-container-builder"
REPOSITORY_PATH = (
    AGENT_DIR
    / "infra"
    / "integrations"
    / "docker-container"
    / "docker_container_repository.py"
)


def load_repository_module():
    spec = importlib.util.spec_from_file_location("docker_container_repository", REPOSITORY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load repository from {REPOSITORY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DockerContainerBuilderRunnersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_module = load_repository_module()

    def write_project(self, root: Path) -> Path:
        (root / "requirements.txt").write_text("fastapi==0.115.0\nuvicorn==0.30.0\n", encoding="utf-8")
        (root / "app.py").write_text(
            """
import os

PORT = int(os.environ.get("PORT", "8000"))
""".lstrip(),
            encoding="utf-8",
        )
        (root / ".env").write_text("API_TOKEN=secret-value\n", encoding="utf-8")
        return root

    def write_spec(
        self,
        root: Path,
        *,
        target_project: Path | None = None,
        language: str = "python",
        target: str = "prod",
        entrypoint: str = "python app.py",
        image_tag: str = "1.0.0",
        include_secret_value: bool = False,
    ) -> Path:
        path = root / "container-spec.yaml"
        target_project_line = f"target_project: {target_project}\n" if target_project else ""
        secret_line = "  - name: API_TOKEN\n    value: plain-secret\n" if include_secret_value else "  - PORT\n"
        path.write_text(
            f"""
project_name: Orders API
{target_project_line}language: {language}
target: {target}
entrypoint: {entrypoint}
image_name: orders-api
image_tag: {image_tag}
ports:
  - 8000
environment:
{secret_line}services:
  - name: redis
    image: redis:7.2-alpine
    port: 6379
include_compose: true
""".lstrip(),
            encoding="utf-8",
        )
        return path

    def test_analyze_containerization_target_detects_python_project_and_risks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = self.write_project(Path(tmpdir))
            repository = self.repository_module.DockerContainerRepository(root=ROOT)

            result = repository.analyze_containerization_target(project_path=project)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["write_policy"], "read_only")
            self.assertEqual(result["facts"]["language"], "python")
            self.assertIn(".env", result["facts"]["sensitive_files"])
            codes = {risk["code"] for risk in result["risks"]}
            self.assertIn("sensitive_files_in_context", codes)

    def test_generate_dockerfile_returns_content_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.DockerContainerRepository(root=ROOT)

            result = repository.generate_dockerfile(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["write_policy"], "output_only")
            content = result["content"]
            self.assertIn("FROM python:3.12-slim", content)
            self.assertIn("USER appuser", content)
            self.assertIn("EXPOSE 8000", content)
            self.assertFalse((root / "Dockerfile").exists())

    def test_generate_compose_avoids_privileged_and_embedded_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.DockerContainerRepository(root=ROOT)

            result = repository.generate_compose(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            content = result["content"]
            self.assertIn("services:", content)
            self.assertIn('"8000:8000"', content)
            self.assertNotIn("privileged", content.lower())
            self.assertNotIn("plain-secret", content)

    def test_generate_project_files_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.DockerContainerRepository(root=ROOT)

            result = repository.generate_container_project_files(spec_path=spec_path)

            self.assertEqual(result["status"], "planned")
            self.assertTrue(result["dry_run"])
            planned = {item["path"] for item in result["planned_files"]}
            self.assertGreaterEqual(planned, {"Dockerfile", ".dockerignore", "README.docker.md", "docker-compose.yml"})
            self.assertFalse((target_project / "Dockerfile").exists())

    def test_generate_project_files_execute_writes_inside_target_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.DockerContainerRepository(root=ROOT)

            result = repository.generate_container_project_files(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "written")
            self.assertTrue((target_project / "Dockerfile").exists())
            self.assertTrue((target_project / ".dockerignore").exists())
            ignore = (target_project / ".dockerignore").read_text(encoding="utf-8")
            self.assertIn(".env", ignore)
            for item in result["written_files"]:
                self.assertTrue(Path(item["path"]).resolve().is_relative_to(target_project.resolve()))

    def test_generate_project_files_blocks_overwrite_without_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_project = root / "target"
            target_project.mkdir()
            spec_path = self.write_spec(root, target_project=target_project)
            repository = self.repository_module.DockerContainerRepository(root=ROOT)
            repository.generate_container_project_files(spec_path=spec_path, execute=True)

            result = repository.generate_container_project_files(spec_path=spec_path, execute=True)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "target_exists")

    def test_review_docker_security_detects_high_risk_patterns(self) -> None:
        repository = self.repository_module.DockerContainerRepository(root=ROOT)

        result = repository.review_docker_security(
            dockerfile_text="FROM python:latest\nCOPY . .\nENV API_KEY=abc\n",
            compose_text="services:\n  app:\n    image: app\n    privileged: true\n",
        )

        self.assertEqual(result["status"], "failed")
        codes = {finding["code"] for finding in result["findings"]}
        self.assertIn("missing_non_root_user", codes)
        self.assertIn("base_image_latest", codes)
        self.assertIn("secret_marker_in_dockerfile", codes)
        self.assertIn("compose_privileged", codes)
        rendered = json.dumps(result)
        self.assertNotIn("abc", rendered)

    def test_plan_image_build_is_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)
            repository = self.repository_module.DockerContainerRepository(root=ROOT)

            result = repository.plan_image_build(spec_path=spec_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["write_policy"], "dry_run")
            self.assertFalse(result["push_real"])
            self.assertIn("docker build", result["blocked_actions"])
            self.assertTrue(any(command.startswith("docker build") for command in result["commands_to_review"]))

    def test_plan_blocks_hardcoded_secret_environment_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root, include_secret_value=True)
            repository = self.repository_module.DockerContainerRepository(root=ROOT)

            result = repository.plan_container_artifacts(spec_path=spec_path)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "hardcoded_secret_env_value")

    def test_generate_dockerfile_runner_is_executable_through_agent_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            spec_path = self.write_spec(root)

            result = subprocess.run(
                [
                    sys.executable,
                    str(AGENT),
                    "--json",
                    "run",
                    "docker-container-builder",
                    "generate-dockerfile",
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
        self.assertIn("Dockerfile", runner_payload["artifact"])


if __name__ == "__main__":
    unittest.main()
