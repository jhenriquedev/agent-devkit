"""Repository for deterministic Docker artifact generation and review."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_LANGUAGES = {"python", "node", "go", "java", "unknown"}
SUPPORTED_TARGETS = {"dev", "prod", "ci"}
SECRET_NAME_PATTERN = re.compile(
    r"(SECRET|TOKEN|PASSWORD|PASS|API_KEY|PRIVATE_KEY|ACCESS_KEY|SERVICE_ROLE|CONNECTION_STRING)",
    re.IGNORECASE,
)
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"\b(?:SECRET|TOKEN|PASSWORD|PASS|API_KEY|PRIVATE_KEY|ACCESS_KEY|SERVICE_ROLE|CONNECTION_STRING)\b\s*[:=]",
    re.IGNORECASE,
)
PRIVATE_URL_PATTERN = re.compile(r"(postgres|mysql|mongodb|redis)://[^\s'\"<>]+", re.IGNORECASE)
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")
IMAGE_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._/-]*(?::[a-zA-Z0-9._-]+)?$")
SAFE_ENV_REF_PATTERN = re.compile(r"^(\$\{[^}]+\}|env:[A-Z_][A-Z0-9_]*|<[^>]+>)$")


class DockerContainerBuilderError(RuntimeError):
    """Raised when Docker artifacts cannot be generated or reviewed."""


class DockerContainerRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[5]

    def analyze_containerization_target(self, *, project_path: Path) -> dict[str, Any]:
        project_root = self.resolve_project(project_path)
        facts = self.detect_project_facts(project_root)
        risks = self.detect_project_risks(project_root)
        return {
            "kind": "containerization-analysis",
            "status": "ok",
            "project_path": str(project_root),
            "write_policy": "read_only",
            "facts": facts,
            "risks": risks,
            "questions": self.analysis_questions(facts),
            "next_steps": [
                "Review detected language and entrypoint before generating Docker artifacts.",
                "Provide an explicit spec for target, ports, environment refs and services.",
            ],
        }

    def generate_dockerfile(self, *, spec_path: Path) -> dict[str, Any]:
        plan = self.plan_container_artifacts(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan
        spec = self.normalize_spec(self.load_spec(spec_path))
        content = self.render_dockerfile(spec)
        findings = self.review_dockerfile_text(content)
        return {
            "kind": "dockerfile",
            "status": "ok",
            "artifact": "Dockerfile",
            "content": content,
            "bytes": len(content.encode("utf-8")),
            "write_policy": "output_only",
            "security_findings": findings,
        }

    def generate_compose(self, *, spec_path: Path) -> dict[str, Any]:
        plan = self.plan_container_artifacts(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan
        spec = self.normalize_spec(self.load_spec(spec_path))
        content = self.render_compose(spec)
        findings = self.review_compose_text(content)
        return {
            "kind": "docker-compose",
            "status": "ok",
            "artifact": "docker-compose.yml",
            "content": content,
            "bytes": len(content.encode("utf-8")),
            "write_policy": "output_only",
            "security_findings": findings,
        }

    def generate_container_project_files(
        self,
        *,
        spec_path: Path,
        execute: bool = False,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan_container_artifacts(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan
        spec = self.normalize_spec(self.load_spec(spec_path))
        target_project = spec.get("target_project")
        if not target_project:
            return {
                "kind": "container-project-files",
                "status": "needs-input",
                "missing_fields": ["target_project"],
                "questions": ["Qual e o caminho do projeto destino?"],
            }
        target_root = Path(str(target_project)).expanduser().resolve()
        files = self.build_container_files(spec)
        return self.write_or_plan_files(
            kind="container-project-files",
            files=files,
            target_root=target_root,
            execute=execute,
            allow_overwrite=allow_overwrite,
            extra={"container": self.container_summary(spec), "write_policy": "local_write"},
        )

    def review_docker_security(
        self,
        *,
        dockerfile_path: Path | None = None,
        compose_path: Path | None = None,
        dockerfile_text: str | None = None,
        compose_text: str | None = None,
    ) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []
        if dockerfile_path is not None:
            findings.extend(self.review_dockerfile_text(dockerfile_path.read_text(encoding="utf-8", errors="replace"), source=str(dockerfile_path)))
        if compose_path is not None:
            findings.extend(self.review_compose_text(compose_path.read_text(encoding="utf-8", errors="replace"), source=str(compose_path)))
        if dockerfile_text is not None:
            findings.extend(self.review_dockerfile_text(dockerfile_text, source="<dockerfile-text>"))
        if compose_text is not None:
            findings.extend(self.review_compose_text(compose_text, source="<compose-text>"))
        valid = not any(finding["severity"] in {"critical", "high"} for finding in findings)
        return {
            "kind": "docker-security-review",
            "status": "ok" if valid else "failed",
            "valid": valid,
            "write_policy": "read_only",
            "findings_count": len(findings),
            "findings": self.dedupe_findings(findings),
        }

    def plan_image_build(self, *, spec_path: Path) -> dict[str, Any]:
        plan = self.plan_container_artifacts(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan
        spec = self.normalize_spec(self.load_spec(spec_path))
        image = spec["image_name"] or spec["project_slug"]
        tag = spec["image_tag"] or ("dev" if spec["target"] == "dev" else "0.1.0")
        image_ref = f"{image}:{tag}"
        commands = [
            f"docker build --file Dockerfile --tag {image_ref} .",
        ]
        if spec["ports"]:
            port_args = " ".join(f"-p {port}:{port}" for port in spec["ports"])
            commands.append(f"docker run --rm {port_args} {image_ref}")
        else:
            commands.append(f"docker run --rm {image_ref}")
        if spec.get("registry"):
            commands.append(f"docker tag {image_ref} {spec['registry'].rstrip('/')}/{image_ref}")
            commands.append(f"docker push {spec['registry'].rstrip('/')}/{image_ref}")
        return {
            "kind": "image-build-plan",
            "status": "ok",
            "deploy_real": False,
            "push_real": False,
            "write_policy": "dry_run",
            "image": image,
            "tag": tag,
            "commands_to_review": commands,
            "blocked_actions": ["docker build", "docker run", "docker compose up", "docker push", "deploy container"],
            "pre_requisites": [
                "Docker installed locally.",
                "Dockerfile and .dockerignore reviewed.",
                "Secrets provided at runtime through env/secret manager, not copied into the image.",
            ],
        }

    def plan_container_artifacts(self, *, spec_path: Path) -> dict[str, Any]:
        spec = self.load_spec(spec_path)
        result = self.validate_spec(spec)
        if result["status"] != "ok":
            return result
        normalized = self.normalize_spec(spec)
        blocked = self.detect_forbidden_spec_content(normalized)
        if blocked:
            return blocked
        files = self.build_container_files(normalized)
        return {
            "kind": "container-artifact-plan",
            "status": "ok",
            "container": self.container_summary(normalized),
            "write_policy": "read_only",
            "planned_artifacts": self.public_file_plan(files),
            "security_findings": [
                *self.review_dockerfile_text(self.render_dockerfile(normalized)),
                *self.review_compose_text(self.render_compose(normalized)),
            ],
            "questions": self.open_questions(normalized),
        }

    def resolve_project(self, project_path: Path) -> Path:
        root = project_path.expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise DockerContainerBuilderError(f"project path not found: {root}")
        return root

    def load_spec(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise DockerContainerBuilderError(f"spec not found: {path}")
        text = path.read_text(encoding="utf-8")
        payload = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text) or {}
        if not isinstance(payload, dict):
            raise DockerContainerBuilderError("spec must be a mapping")
        return payload

    def validate_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        missing = [field for field in ("project_name", "language", "entrypoint", "target") if not spec.get(field)]
        if missing:
            return {
                "kind": "container-artifact-plan",
                "status": "needs-input",
                "missing_fields": missing,
                "questions": [self.question_for_missing_field(field) for field in missing],
            }
        language = str(spec.get("language") or "").strip().lower()
        if language not in SUPPORTED_LANGUAGES:
            return {
                "kind": "container-artifact-plan",
                "status": "blocked",
                "reason": "unsupported_language",
                "supported_languages": sorted(SUPPORTED_LANGUAGES),
            }
        target = str(spec.get("target") or "").strip().lower()
        if target not in SUPPORTED_TARGETS:
            return {
                "kind": "container-artifact-plan",
                "status": "blocked",
                "reason": "unsupported_target",
                "supported_targets": sorted(SUPPORTED_TARGETS),
            }
        for field in ("ports", "environment", "services", "tags"):
            if spec.get(field) is not None and not isinstance(spec[field], list):
                return {
                    "kind": "container-artifact-plan",
                    "status": "blocked",
                    "reason": "invalid_list_field",
                    "field": field,
                    "risks": [f"{field} must be a list when provided."],
                }
        return {"status": "ok"}

    def normalize_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(spec)
        normalized["project_name"] = " ".join(str(spec["project_name"]).split())
        normalized["project_slug"] = self.slugify(normalized["project_name"])
        normalized["language"] = str(spec["language"]).strip().lower()
        normalized["target"] = str(spec["target"]).strip().lower()
        normalized["entrypoint"] = " ".join(str(spec["entrypoint"]).split())
        normalized["ports"] = self.normalize_ports(spec.get("ports") or [])
        normalized["environment"] = self.normalize_environment(spec.get("environment") or [])
        normalized["services"] = [self.normalize_service(item) for item in spec.get("services") or []]
        normalized["base_image"] = str(spec.get("base_image") or self.default_base_image(normalized)).strip()
        normalized["package_manager"] = str(spec.get("package_manager") or self.default_package_manager(normalized)).strip()
        normalized["include_compose"] = bool(spec.get("include_compose", True))
        normalized["image_name"] = str(spec.get("image_name") or normalized["project_slug"]).strip()
        normalized["image_tag"] = str(spec.get("image_tag") or "").strip()
        normalized["registry"] = str(spec.get("registry") or "").strip()
        normalized["healthcheck_path"] = str(spec.get("healthcheck_path") or "/health").strip()
        return normalized

    def detect_project_facts(self, project_root: Path) -> dict[str, Any]:
        files = {path.name for path in project_root.iterdir() if path.is_file()}
        language = "unknown"
        package_manager = None
        if "pyproject.toml" in files or "requirements.txt" in files:
            language = "python"
            package_manager = "pip"
        elif "package.json" in files:
            language = "node"
            package_manager = "npm"
        elif "go.mod" in files:
            language = "go"
            package_manager = "go"
        elif "pom.xml" in files or "build.gradle" in files or "build.gradle.kts" in files:
            language = "java"
            package_manager = "maven" if "pom.xml" in files else "gradle"
        return {
            "language": language,
            "package_manager": package_manager,
            "has_dockerfile": "Dockerfile" in files,
            "has_dockerignore": ".dockerignore" in files,
            "has_compose": "docker-compose.yml" in files or "compose.yml" in files,
            "entrypoint_candidates": self.entrypoint_candidates(project_root, language),
            "ports": self.detect_ports(project_root),
            "sensitive_files": self.sensitive_files(project_root),
        }

    def detect_project_risks(self, project_root: Path) -> list[dict[str, Any]]:
        risks = []
        facts = self.detect_project_facts(project_root)
        if facts["has_dockerfile"] and not facts["has_dockerignore"]:
            risks.append(self.finding("medium", "missing_dockerignore", ".dockerignore is missing.", "Docker build context may include secrets or heavy caches.", "Add a .dockerignore file."))
        if facts["sensitive_files"]:
            risks.append(self.finding("high", "sensitive_files_in_context", "Sensitive file markers exist in the project root.", "Docker context can accidentally include secrets.", "Ensure .dockerignore excludes these files."))
        return risks

    def entrypoint_candidates(self, project_root: Path, language: str) -> list[str]:
        candidates = {
            "python": ["app.py", "main.py", "server.py"],
            "node": ["server.js", "app.js", "index.js"],
            "go": ["main.go", "cmd"],
            "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        }.get(language, [])
        return [candidate for candidate in candidates if (project_root / candidate).exists()]

    def detect_ports(self, project_root: Path) -> list[int]:
        ports: set[int] = set()
        for file_name in ("package.json", "pyproject.toml", "app.py", "main.py", "server.js", "index.js"):
            path = project_root / file_name
            if not path.exists() or path.stat().st_size > 512_000:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for match in re.finditer(r"\b(?:PORT|port|listen)\D{0,20}(3000|5000|8000|8080|9000)\b", text):
                ports.add(int(match.group(1)))
        return sorted(ports)

    def sensitive_files(self, project_root: Path) -> list[str]:
        names = []
        for path in project_root.iterdir():
            if path.name.startswith(".env") or path.name in {".npmrc", ".pypirc"} or path.name.endswith((".pem", ".key", ".p12")):
                names.append(path.name)
        return sorted(names)

    def build_container_files(self, spec: dict[str, Any]) -> list[tuple[str, str]]:
        files = [
            ("Dockerfile", self.render_dockerfile(spec)),
            (".dockerignore", self.render_dockerignore(spec)),
            ("README.docker.md", self.render_docker_readme(spec)),
        ]
        if spec.get("include_compose", True):
            files.append(("docker-compose.yml", self.render_compose(spec)))
        return files

    def render_dockerfile(self, spec: dict[str, Any]) -> str:
        language = spec["language"]
        if language == "python":
            lines = [
                f"FROM {spec['base_image']}",
                "",
                "ENV PYTHONDONTWRITEBYTECODE=1 \\",
                "    PYTHONUNBUFFERED=1",
                "",
                "WORKDIR /app",
                "RUN useradd --create-home --shell /usr/sbin/nologin appuser",
                "",
                "COPY requirements*.txt ./",
                "RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi",
                "",
                "COPY . .",
                "USER appuser",
                *self.expose_lines(spec),
                *self.healthcheck_lines(spec),
                f"CMD {self.json_command(spec['entrypoint'])}",
            ]
            return "\n".join(lines).rstrip() + "\n"
        if language == "node":
            lines = [
                f"FROM {spec['base_image']}",
                "",
                "ENV NODE_ENV=production",
                "WORKDIR /app",
                "RUN groupadd --system appuser && useradd --system --gid appuser appuser",
                "",
                "COPY package*.json ./",
                "RUN if [ -f package-lock.json ]; then npm ci --omit=dev; else npm install --omit=dev; fi",
                "",
                "COPY . .",
                "USER appuser",
                *self.expose_lines(spec),
                *self.healthcheck_lines(spec),
                f"CMD {self.json_command(spec['entrypoint'])}",
            ]
            return "\n".join(lines).rstrip() + "\n"
        if language == "go":
            lines = [
                f"FROM {spec['base_image']} AS build",
                "WORKDIR /src",
                "COPY go.mod go.sum* ./",
                "RUN go mod download",
                "COPY . .",
                f"RUN CGO_ENABLED=0 go build -o /out/app {spec['entrypoint']}",
                "",
                "FROM gcr.io/distroless/static-debian12:nonroot",
                "WORKDIR /app",
                "COPY --from=build /out/app /app/app",
                "USER nonroot:nonroot",
                *self.expose_lines(spec),
                'ENTRYPOINT ["/app/app"]',
            ]
            return "\n".join(lines).rstrip() + "\n"
        if language == "java":
            lines = [
                f"FROM {spec['base_image']} AS build",
                "WORKDIR /src",
                "COPY . .",
                "RUN if [ -f mvnw ]; then ./mvnw -DskipTests package; else mvn -DskipTests package; fi",
                "",
                "FROM eclipse-temurin:21-jre-jammy",
                "WORKDIR /app",
                "RUN useradd --create-home --shell /usr/sbin/nologin appuser",
                "COPY --from=build /src/target/*.jar /app/app.jar",
                "USER appuser",
                *self.expose_lines(spec),
                *self.healthcheck_lines(spec),
                'ENTRYPOINT ["java", "-jar", "/app/app.jar"]',
            ]
            return "\n".join(lines).rstrip() + "\n"
        return "\n".join([
            "FROM alpine:3.20",
            "WORKDIR /app",
            "RUN adduser -D -H appuser",
            "COPY . .",
            "USER appuser",
            *self.expose_lines(spec),
            f"CMD {self.json_command(spec['entrypoint'])}",
        ]).rstrip() + "\n"

    def render_dockerignore(self, _spec: dict[str, Any]) -> str:
        return "\n".join([
            ".git",
            ".gitignore",
            ".env",
            ".env.*",
            ".ssh",
            "*.pem",
            "*.key",
            "*.p12",
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".venv",
            "venv",
            "node_modules",
            "npm-debug.log",
            "dist",
            "build",
            "target",
            ".DS_Store",
            "",
        ])

    def render_compose(self, spec: dict[str, Any]) -> str:
        service_name = spec["project_slug"].replace("-", "_")
        named_volumes: list[str] = []
        lines = [
            "services:",
            f"  {service_name}:",
            "    build:",
            "      context: .",
            "      dockerfile: Dockerfile",
            f"    image: {spec['image_name']}:{spec['image_tag'] or 'dev'}",
        ]
        if spec["ports"]:
            lines.append("    ports:")
            for port in spec["ports"]:
                lines.append(f'      - "{port}:{port}"')
        if spec["environment"]:
            lines.append("    environment:")
            for item in spec["environment"]:
                lines.append(f"      {item['name']}: {item['value']}")
        lines.extend(self.compose_healthcheck_lines(spec))
        if spec["services"]:
            lines.append("    depends_on:")
            for service in spec["services"]:
                lines.append(f"      {service['name']}:")
                lines.append("        condition: service_healthy")
            for service in spec["services"]:
                service_lines, volume = self.render_compose_service(service)
                lines.extend(service_lines)
                if volume:
                    named_volumes.append(volume)
        if named_volumes:
            lines.append("volumes:")
            for volume in sorted(set(named_volumes)):
                lines.append(f"  {volume}:")
        return "\n".join(lines).rstrip() + "\n"

    def render_compose_service(self, service: dict[str, str]) -> tuple[list[str], str | None]:
        lines = [
            f"  {service['name']}:",
            f"    image: {service['image']}",
        ]
        if service.get("port"):
            lines.extend(["    expose:", f"      - \"{service['port']}\""])
        if service.get("volume"):
            lines.extend(["    volumes:", f"      - {service['volume']}:/data"])
        lines.extend([
            "    healthcheck:",
            "      test: [\"CMD\", \"true\"]",
            "      interval: 10s",
            "      timeout: 3s",
            "      retries: 5",
        ])
        return lines, service["volume"] or None

    def render_docker_readme(self, spec: dict[str, Any]) -> str:
        image_ref = f"{spec['image_name']}:{spec['image_tag'] or ('dev' if spec['target'] == 'dev' else '0.1.0')}"
        run_ports = " ".join(f"-p {port}:{port}" for port in spec["ports"])
        run_command = f"docker run --rm {run_ports} {image_ref}".replace("  ", " ").strip()
        return "\n".join([
            f"# Docker: {spec['project_name']}",
            "",
            "## Build",
            "",
            "```sh",
            f"docker build -t {image_ref} .",
            "```",
            "",
            "## Run",
            "",
            "```sh",
            run_command,
            "```",
            "",
            "## Notes",
            "",
            "- Review `.dockerignore` before build.",
            "- Provide secrets only at runtime through env or a secret manager.",
            "- Do not push images before reviewing tags and registry permissions.",
            "",
        ])

    def review_dockerfile_text(self, text: str, *, source: str = "Dockerfile") -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        lower = text.lower()
        if "user " not in lower:
            findings.append(self.finding("high", "missing_non_root_user", "Dockerfile does not set USER.", "Container may run as root.", "Create and use a non-root user.", source=source))
        if re.search(r"^FROM\s+\S+:latest\b", text, re.IGNORECASE | re.MULTILINE):
            findings.append(self.finding("medium", "base_image_latest", "Base image uses latest tag.", "Builds are not reproducible.", "Pin an explicit version tag.", source=source))
        if re.search(r"\bCOPY\s+\. ", text, re.IGNORECASE) and ".dockerignore" not in lower:
            findings.append(self.finding("medium", "broad_copy_requires_dockerignore", "Dockerfile copies full context.", "Secrets can enter image if .dockerignore is missing.", "Generate and review .dockerignore.", source=source))
        if re.search(r"\bADD\s+https?://", text, re.IGNORECASE):
            findings.append(self.finding("medium", "remote_add", "Dockerfile uses ADD from remote URL.", "Remote downloads reduce reproducibility.", "Download dependencies through package manager or verified checksums.", source=source))
        if SECRET_ASSIGNMENT_PATTERN.search(text) or PRIVATE_URL_PATTERN.search(text):
            findings.append(self.finding("critical", "secret_marker_in_dockerfile", "Secret marker or private URL appears in Dockerfile.", "Secrets can be baked into image layers.", "Move secrets to runtime env or secret manager.", source=source))
        return findings

    def review_compose_text(self, text: str, *, source: str = "docker-compose.yml") -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        lower = text.lower()
        if "privileged: true" in lower:
            findings.append(self.finding("critical", "compose_privileged", "Compose enables privileged mode.", "Privileged containers can escape intended isolation.", "Remove privileged mode.", source=source))
        if "network_mode: host" in lower:
            findings.append(self.finding("high", "compose_host_network", "Compose uses host network.", "Host network broadens exposure.", "Use explicit ports and bridge networks.", source=source))
        if re.search(r"[-:]\s*/:/", text):
            findings.append(self.finding("critical", "compose_mounts_host_root", "Compose appears to mount host root.", "Mounting / exposes the host filesystem.", "Use named volumes or scoped bind mounts.", source=source))
        if SECRET_ASSIGNMENT_PATTERN.search(text) or PRIVATE_URL_PATTERN.search(text):
            findings.append(self.finding("critical", "secret_marker_in_compose", "Secret marker or private URL appears in compose.", "Secrets can leak through committed compose files.", "Use env references or secret manager integration.", source=source))
        return findings

    def detect_forbidden_spec_content(self, spec: dict[str, Any]) -> dict[str, Any] | None:
        rendered = json.dumps(spec, ensure_ascii=False)
        if SECRET_ASSIGNMENT_PATTERN.search(rendered) or PRIVATE_URL_PATTERN.search(rendered):
            return {
                "kind": "container-artifact-plan",
                "status": "blocked",
                "reason": "forbidden_sensitive_marker",
                "write_policy": "read_only",
                "risks": ["Spec contains secret assignment marker or private connection URL."],
            }
        for env in spec["environment"]:
            if SECRET_NAME_PATTERN.search(env["name"]) and not SAFE_ENV_REF_PATTERN.match(env["value"]):
                return {
                    "kind": "container-artifact-plan",
                    "status": "blocked",
                    "reason": "hardcoded_secret_env_value",
                    "field": env["name"],
                    "risks": ["Secret-like environment variable must use env:, ${...} or <placeholder> reference."],
                }
        return None

    def write_or_plan_files(
        self,
        *,
        kind: str,
        files: list[tuple[str, str]],
        target_root: Path,
        execute: bool,
        allow_overwrite: bool,
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        if not target_root.exists() or not target_root.is_dir():
            return {
                "kind": kind,
                "status": "blocked",
                "reason": "target_project_missing",
                "target_project": str(target_root),
                "risks": ["target_project must exist before files can be written."],
            }
        checked_files = []
        for relative_path, content in files:
            target = (target_root / relative_path).resolve()
            if Path(relative_path).is_absolute() or not self.is_inside(target_root, target):
                return {
                    "kind": kind,
                    "status": "blocked",
                    "reason": "path_outside_target_project",
                    "path": relative_path,
                    "target_project": str(target_root),
                }
            checked_files.append((relative_path, target, content))
        if not execute:
            return {
                "kind": kind,
                "status": "planned",
                "dry_run": True,
                "target_project": str(target_root),
                "planned_files": [
                    {"path": relative_path, "absolute_path": str(target), "bytes": len(content.encode("utf-8"))}
                    for relative_path, target, content in checked_files
                ],
                **extra,
                "next_steps": ["Rerun with --execute after reviewing the planned files."],
            }
        existing = [target for _relative_path, target, _content in checked_files if target.exists()]
        if existing and not allow_overwrite:
            return {
                "kind": kind,
                "status": "blocked",
                "reason": "target_exists",
                "target_project": str(target_root),
                "existing_files": [str(path) for path in existing],
                **extra,
                "next_steps": ["Rerun with --allow-overwrite only after reviewing the existing files."],
            }
        written_files = []
        for _relative_path, target, content in checked_files:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written_files.append({"path": str(target), "bytes": len(content.encode("utf-8"))})
        return {
            "kind": kind,
            "status": "written",
            "dry_run": False,
            "target_project": str(target_root),
            "written_files": written_files,
            **extra,
        }

    def normalize_ports(self, ports: list[Any]) -> list[int]:
        normalized: list[int] = []
        for port in ports:
            try:
                value = int(port)
            except (TypeError, ValueError) as exc:
                raise DockerContainerBuilderError(f"invalid port: {port}") from exc
            if value < 1 or value > 65535:
                raise DockerContainerBuilderError(f"invalid port: {port}")
            normalized.append(value)
        return sorted(set(normalized))

    def normalize_environment(self, environment: list[Any]) -> list[dict[str, str]]:
        normalized = []
        for item in environment:
            if isinstance(item, str):
                name = item.strip()
                value = f"${{{name}}}"
            elif isinstance(item, dict):
                name = str(item.get("name") or item.get("key") or "").strip()
                value = str(item.get("value") or f"${{{name}}}").strip()
            else:
                raise DockerContainerBuilderError("environment entries must be strings or mappings")
            if not name:
                raise DockerContainerBuilderError("environment entry missing name")
            normalized.append({"name": name, "value": value})
        return normalized

    def normalize_service(self, item: Any) -> dict[str, str]:
        if isinstance(item, str):
            if not IMAGE_REF_PATTERN.match(item):
                raise DockerContainerBuilderError(f"invalid service image: {item}")
            name = self.slugify(item).replace("-", "_")
            return {"name": name, "image": item, "port": "", "volume": ""}
        if not isinstance(item, dict):
            raise DockerContainerBuilderError("services entries must be strings or mappings")
        name = self.slugify(str(item.get("name") or item.get("image") or "service")).replace("-", "_")
        image = str(item.get("image") or name).strip()
        if not IMAGE_REF_PATTERN.match(image):
            raise DockerContainerBuilderError(f"invalid service image: {image}")
        return {
            "name": name,
            "image": image,
            "port": str(item.get("port") or "").strip(),
            "volume": self.slugify(str(item.get("volume") or "")) if item.get("volume") else "",
        }

    def default_base_image(self, spec: dict[str, Any]) -> str:
        language = spec["language"]
        target = spec["target"]
        if language == "python":
            return "python:3.12-slim"
        if language == "node":
            return "node:20-bookworm-slim"
        if language == "go":
            return "golang:1.22-bookworm"
        if language == "java":
            return "maven:3.9-eclipse-temurin-21"
        return "alpine:3.20" if target != "prod" else "alpine:3.20"

    def default_package_manager(self, spec: dict[str, Any]) -> str:
        return {"python": "pip", "node": "npm", "go": "go", "java": "maven"}.get(spec["language"], "unknown")

    def expose_lines(self, spec: dict[str, Any]) -> list[str]:
        return [f"EXPOSE {port}" for port in spec["ports"]]

    def healthcheck_lines(self, spec: dict[str, Any]) -> list[str]:
        if not spec["ports"] or spec["language"] == "go":
            return []
        port = spec["ports"][0]
        if spec["language"] == "node":
            return [f'HEALTHCHECK CMD node -e "require(\'http\').get(\'http://127.0.0.1:{port}{spec["healthcheck_path"]}\', r => process.exit(r.statusCode < 500 ? 0 : 1)).on(\'error\', () => process.exit(1))"']
        return [f'HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen(\'http://127.0.0.1:{port}{spec["healthcheck_path"]}\', timeout=2)" || exit 1']

    def compose_healthcheck_lines(self, spec: dict[str, Any]) -> list[str]:
        if not spec["ports"]:
            return []
        port = spec["ports"][0]
        if spec["language"] == "python":
            test = f"python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:{port}{spec['healthcheck_path']}', timeout=2)\""
        elif spec["language"] == "node":
            test = f"node -e \"require('http').get('http://127.0.0.1:{port}{spec['healthcheck_path']}', r => process.exit(r.statusCode < 500 ? 0 : 1)).on('error', () => process.exit(1))\""
        else:
            test = "true"
        return [
            "    healthcheck:",
            f"      test: [\"CMD-SHELL\", {json.dumps(test)}]",
            "      interval: 10s",
            "      timeout: 3s",
            "      retries: 5",
        ]

    def json_command(self, command: str) -> str:
        parts = [part for part in command.split(" ") if part]
        return json.dumps(parts)

    def container_summary(self, spec: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": spec["project_name"],
            "slug": spec["project_slug"],
            "language": spec["language"],
            "target": spec["target"],
            "entrypoint": spec["entrypoint"],
            "ports": spec["ports"],
            "include_compose": spec["include_compose"],
        }

    def public_file_plan(self, files: list[tuple[str, str]]) -> list[dict[str, Any]]:
        return [{"path": path, "bytes": len(content.encode("utf-8"))} for path, content in files]

    def analysis_questions(self, facts: dict[str, Any]) -> list[str]:
        questions = []
        if facts["language"] == "unknown":
            questions.append("Qual linguagem/runtime deve ser usado no container?")
        if not facts["entrypoint_candidates"]:
            questions.append("Qual comando inicia a aplicacao dentro do container?")
        if not facts["ports"]:
            questions.append("A aplicacao expoe alguma porta HTTP/TCP?")
        return questions

    def open_questions(self, spec: dict[str, Any]) -> list[str]:
        questions = []
        if spec["language"] == "unknown":
            questions.append("A linguagem foi marcada como unknown; revise manualmente a imagem base e o entrypoint.")
        if not spec["ports"]:
            questions.append("Sem portas declaradas; confirme se o container e batch/worker.")
        if not spec["environment"]:
            questions.append("Sem environment refs; confirme se a aplicacao nao requer configuracao externa.")
        return questions

    def question_for_missing_field(self, field: str) -> str:
        return {
            "project_name": "Qual e o nome do projeto/container?",
            "language": "Qual linguagem deve ser usada? python, node, go, java ou unknown.",
            "entrypoint": "Qual comando inicia a aplicacao?",
            "target": "O alvo e dev, prod ou ci?",
        }.get(field, f"Informe o campo {field}.")

    def finding(
        self,
        severity: str,
        code: str,
        evidence: str,
        risk: str,
        recommendation: str,
        *,
        source: str | None = None,
    ) -> dict[str, Any]:
        return {
            "severity": severity,
            "code": code,
            "source": source,
            "evidence": self.redact_text(evidence),
            "risk": risk,
            "recommendation": recommendation,
        }

    def redact_text(self, text: str) -> str:
        redacted = PRIVATE_URL_PATTERN.sub("<redacted-private-url>", text)
        return re.sub(r"(?i)(SECRET|TOKEN|PASSWORD|PASS|API_KEY|PRIVATE_KEY|ACCESS_KEY)\s*[:=]\s*[^,\s]+", r"\1=<redacted>", redacted)

    def dedupe_findings(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[Any, ...]] = set()
        unique = []
        for finding in findings:
            key = (finding.get("code"), finding.get("source"), finding.get("evidence"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(finding)
        return unique

    def slugify(self, value: str) -> str:
        slug = SLUG_PATTERN.sub("-", value.lower()).strip("-")
        return slug or "container-app"

    def is_inside(self, root: Path, target: Path) -> bool:
        try:
            target.relative_to(root.resolve())
            return True
        except ValueError:
            return False
