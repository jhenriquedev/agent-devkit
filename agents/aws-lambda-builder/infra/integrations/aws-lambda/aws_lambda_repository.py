"""Repository for deterministic AWS Lambda project generation."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from typing import Any

import yaml


REQUIRED_SPEC_FIELDS = (
    "lambda_name",
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
)
RUNTIME_FAMILIES = {"python", "nodejs"}
PYTHON_RUNTIMES = {"python3.11", "python3.12", "python3.13"}
NODE_RUNTIMES = {"nodejs20.x", "nodejs22.x"}
TRIGGERS = {"api-gateway", "eventbridge-schedule", "sqs", "sns", "s3-event", "manual-test-event"}
DEPLOY_STRATEGIES = {"sam", "serverless", "manual"}
ASYNC_TRIGGERS = {"eventbridge-schedule", "sqs", "sns", "s3-event"}
SECRET_NAME_PATTERN = re.compile(r"(SECRET|TOKEN|PASSWORD|PASS|API_KEY|PRIVATE_KEY)", re.IGNORECASE)
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"\b(?:SECRET|TOKEN|PASSWORD|PASS|API_KEY|API_TOKEN|PRIVATE_KEY)\b\s*[:=]",
    re.IGNORECASE,
)
KMS_OR_DYNAMIC_REFERENCE = re.compile(r"^(env:|ssm:|secretsmanager:|resolve:|\$\{|<.+>)")
KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")
EXCLUDED_PACKAGE_PARTS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "dist"}
EXCLUDED_PACKAGE_NAMES = {".env", ".DS_Store"}


class AwsLambdaBuilderError(RuntimeError):
    """Raised when the builder cannot read or process an input spec."""


class AwsLambdaRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[5]

    def plan_lambda(self, *, spec_path: Path) -> dict[str, Any]:
        spec = self.load_spec(spec_path)
        spec_result = self.validate_spec(spec)
        if spec_result["status"] != "ok":
            return spec_result

        normalized = self.normalize_spec(spec)
        security = self.security_findings(normalized)
        blocking = [finding for finding in security if finding["severity"] == "error"]
        if blocking:
            return {
                "kind": "lambda-plan",
                "status": "blocked",
                "reason": "security_guardrail_failed",
                "findings": blocking,
                "write_policy": "read_only",
            }

        files = self.build_lambda_files(normalized)
        return {
            "kind": "lambda-plan",
            "status": "ok",
            "lambda": self.lambda_summary(normalized),
            "runtime": normalized["runtime"],
            "trigger": normalized["trigger"],
            "write_policy": "read_only",
            "planned_artifacts": self.public_file_plan(files),
            "security_findings": security,
            "questions": self.open_questions(normalized),
        }

    def generate_lambda_project(
        self,
        *,
        spec_path: Path,
        execute: bool = False,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan_lambda(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        spec = self.normalize_spec(self.load_spec(spec_path))
        target_project = spec.get("target_project")
        if not target_project:
            return {
                "kind": "lambda-project-files",
                "status": "needs-input",
                "missing_fields": ["target_project"],
                "questions": ["Qual e o caminho do projeto destino?"],
            }

        target_root = Path(str(target_project)).expanduser().resolve()
        files = self.build_lambda_files(spec, base_dir=spec["lambda_slug"])
        return self.write_or_plan_files(
            kind="lambda-project-files",
            files=files,
            target_root=target_root,
            execute=execute,
            allow_overwrite=allow_overwrite,
            extra={"lambda": self.lambda_summary(spec), "runtime_family": spec["runtime_family"]},
        )

    def review_lambda_security(self, *, spec_path: Path) -> dict[str, Any]:
        spec = self.load_spec(spec_path)
        spec_result = self.validate_spec(spec)
        if spec_result["status"] != "ok":
            return spec_result
        normalized = self.normalize_spec(spec)
        findings = self.security_findings(normalized)
        valid = not any(finding["severity"] == "error" for finding in findings)
        return {
            "kind": "lambda-security-review",
            "status": "ok" if valid else "failed",
            "valid": valid,
            "findings": findings,
            "write_policy": "read_only",
        }

    def package_lambda(
        self,
        *,
        project_path: Path,
        output_dir: Path | None = None,
        execute: bool = False,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        project_root = project_path.expanduser().resolve()
        if not project_root.exists() or not project_root.is_dir():
            return {
                "kind": "lambda-package",
                "status": "blocked",
                "reason": "project_path_missing",
                "project_path": str(project_root),
            }

        target_output_dir = (output_dir.expanduser().resolve() if output_dir else project_root / "dist")
        if not self.is_inside(project_root, target_output_dir):
            return {
                "kind": "lambda-package",
                "status": "blocked",
                "reason": "output_dir_outside_project",
                "project_path": str(project_root),
                "output_dir": str(target_output_dir),
            }

        archive = target_output_dir / f"{project_root.name}.zip"
        files = self.package_file_plan(project_root)
        if not execute:
            return {
                "kind": "lambda-package",
                "status": "planned",
                "dry_run": True,
                "project_path": str(project_root),
                "archive_path": str(archive),
                "file_count": len(files),
                "files": [str(path.relative_to(project_root)) for path in files],
                "write_policy": "local_write",
                "next_steps": ["Rerun with --execute after reviewing package contents."],
            }

        if archive.exists() and not allow_overwrite:
            return {
                "kind": "lambda-package",
                "status": "blocked",
                "reason": "target_exists",
                "archive_path": str(archive),
                "next_steps": ["Rerun with --allow-overwrite only after reviewing existing archive."],
            }

        target_output_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for path in files:
                package.write(path, path.relative_to(project_root))

        return {
            "kind": "lambda-package",
            "status": "written",
            "dry_run": False,
            "project_path": str(project_root),
            "archive_path": str(archive),
            "file_count": len(files),
            "bytes": archive.stat().st_size,
            "write_policy": "local_write",
        }

    def deploy_lambda_plan(self, *, spec_path: Path) -> dict[str, Any]:
        plan = self.plan_lambda(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        spec = self.normalize_spec(self.load_spec(spec_path))
        commands = self.deploy_commands(spec)
        return {
            "kind": "lambda-deploy-plan",
            "status": "ok",
            "deploy_real": False,
            "lambda": self.lambda_summary(spec),
            "deploy_strategy": spec["deploy_strategy"],
            "write_policy": "dry_run",
            "commands_to_review": commands,
            "pre_requisites": [
                "AWS credentials configured outside this agent.",
                "SAM/Serverless installed when that deploy strategy is selected.",
                "IAM reviewed and approved.",
                "Environment variables resolved through env/SSM/Secrets Manager references.",
            ],
            "rollback": [
                "Keep previous Lambda version or alias target before deployment.",
                "Use CloudFormation/SAM rollback or reset alias to previous version.",
                "Check CloudWatch logs and Lambda metrics after deployment.",
            ],
            "blocked_actions": ["aws cloudformation deploy", "sam deploy", "serverless deploy", "cdk deploy"],
        }

    def load_spec(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise AwsLambdaBuilderError(f"spec not found: {path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            payload = json.loads(text)
        else:
            payload = yaml.safe_load(text) or {}
        if not isinstance(payload, dict):
            raise AwsLambdaBuilderError("spec must be a mapping")
        return payload

    def validate_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        missing = [field for field in REQUIRED_SPEC_FIELDS if field not in spec or spec.get(field) in (None, "")]
        if missing:
            return {
                "kind": "lambda-plan",
                "status": "needs-input",
                "missing_fields": missing,
                "questions": [self.question_for_missing_field(field) for field in missing],
            }
        for field in ("environment_variables", "iam_permissions"):
            if not isinstance(spec.get(field), list):
                return {
                    "kind": "lambda-plan",
                    "status": "blocked",
                    "reason": "invalid_list_field",
                    "field": field,
                    "risks": [f"{field} must be a list."],
                }
        for field in ("input_schema", "output_schema", "observability"):
            if not isinstance(spec.get(field), dict):
                return {
                    "kind": "lambda-plan",
                    "status": "blocked",
                    "reason": "invalid_mapping_field",
                    "field": field,
                    "risks": [f"{field} must be a mapping."],
                }
        runtime_family = str(spec.get("runtime_family") or "").strip().lower()
        if runtime_family not in RUNTIME_FAMILIES:
            return {
                "kind": "lambda-plan",
                "status": "blocked",
                "reason": "unsupported_runtime_family",
                "supported_values": sorted(RUNTIME_FAMILIES),
            }
        runtime = str(spec.get("runtime") or "").strip()
        if runtime_family == "python" and runtime not in PYTHON_RUNTIMES:
            return {"kind": "lambda-plan", "status": "blocked", "reason": "unsupported_runtime", "supported_values": sorted(PYTHON_RUNTIMES)}
        if runtime_family == "nodejs" and runtime not in NODE_RUNTIMES:
            return {"kind": "lambda-plan", "status": "blocked", "reason": "unsupported_runtime", "supported_values": sorted(NODE_RUNTIMES)}
        trigger = str(spec.get("trigger") or "").strip()
        if trigger not in TRIGGERS:
            return {"kind": "lambda-plan", "status": "blocked", "reason": "unsupported_trigger", "supported_values": sorted(TRIGGERS)}
        deploy_strategy = str(spec.get("deploy_strategy") or "").strip()
        if deploy_strategy not in DEPLOY_STRATEGIES:
            return {
                "kind": "lambda-plan",
                "status": "blocked",
                "reason": "unsupported_deploy_strategy",
                "supported_values": sorted(DEPLOY_STRATEGIES),
            }
        timeout_seconds = self.as_int(spec.get("timeout_seconds"), "timeout_seconds")
        memory_mb = self.as_int(spec.get("memory_mb"), "memory_mb")
        if not 1 <= timeout_seconds <= 900:
            return {"kind": "lambda-plan", "status": "blocked", "reason": "invalid_timeout_seconds"}
        if not 128 <= memory_mb <= 10240:
            return {"kind": "lambda-plan", "status": "blocked", "reason": "invalid_memory_mb"}
        return {"status": "ok"}

    def normalize_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(spec)
        normalized["lambda_name"] = " ".join(str(spec["lambda_name"]).split())
        normalized["lambda_slug"] = self.slugify(normalized["lambda_name"])
        normalized["purpose"] = " ".join(str(spec["purpose"]).split())
        normalized["runtime_family"] = str(spec["runtime_family"]).strip().lower()
        normalized["runtime"] = str(spec["runtime"]).strip()
        normalized["handler"] = str(spec["handler"]).strip()
        normalized["trigger"] = str(spec["trigger"]).strip()
        normalized["input_schema"] = dict(spec["input_schema"])
        normalized["output_schema"] = dict(spec["output_schema"])
        normalized["environment_variables"] = [self.normalize_env_var(item) for item in spec["environment_variables"]]
        normalized["iam_permissions"] = [self.normalize_iam_permission(item) for item in spec["iam_permissions"]]
        normalized["observability"] = dict(spec["observability"])
        normalized["timeout_seconds"] = self.as_int(spec["timeout_seconds"], "timeout_seconds")
        normalized["memory_mb"] = self.as_int(spec["memory_mb"], "memory_mb")
        normalized["deploy_strategy"] = str(spec["deploy_strategy"]).strip()
        if spec.get("target_project"):
            normalized["target_project"] = str(spec["target_project"]).strip()
        return normalized

    def security_findings(self, spec: dict[str, Any]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for key, value in self.iter_key_values(spec):
            if isinstance(value, str) and SECRET_ASSIGNMENT_PATTERN.search(value):
                findings.append({"severity": "error", "code": "hardcoded_secret_marker", "field": key})

        for env_var in spec["environment_variables"]:
            name = env_var["name"]
            value = env_var["value"]
            if SECRET_NAME_PATTERN.search(name) and value and not KMS_OR_DYNAMIC_REFERENCE.search(value):
                findings.append({"severity": "error", "code": "hardcoded_secret_env_value", "env": name})

        for permission in spec["iam_permissions"]:
            action = permission["action"]
            resource = permission["resource"]
            justification = permission["justification"]
            if (action == "*" or action.endswith(":*")) and not justification:
                findings.append({"severity": "error", "code": "iam_action_wildcard_without_justification", "action": action})
            if resource == "*":
                findings.append({"severity": "warning", "code": "iam_resource_wildcard", "action": action})

        if spec["trigger"] in ASYNC_TRIGGERS and not spec["observability"].get("dlq_or_destination"):
            findings.append({"severity": "warning", "code": "missing_dlq_or_destination", "trigger": spec["trigger"]})
        if not spec["observability"].get("structured_logging"):
            findings.append({"severity": "warning", "code": "structured_logging_not_declared"})
        return findings

    def build_lambda_files(self, spec: dict[str, Any], *, base_dir: str = "") -> list[tuple[str, str]]:
        prefix = f"{base_dir}/" if base_dir else ""
        if spec["runtime_family"] == "python":
            runtime_files = [
                (f"{prefix}src/handler.py", self.render_python_handler(spec)),
                (f"{prefix}tests/test_handler.py", self.render_python_test(spec)),
                (f"{prefix}requirements.txt", "# Add runtime dependencies here.\n"),
            ]
        else:
            runtime_files = [
                (f"{prefix}src/handler.js", self.render_node_handler(spec)),
                (f"{prefix}tests/handler.test.js", self.render_node_test(spec)),
                (f"{prefix}package.json", self.render_package_json(spec)),
            ]
        return [
            *runtime_files,
            (f"{prefix}events/{spec['trigger']}.json", self.render_event_fixture(spec)),
            (f"{prefix}template.yaml", self.render_sam_template(spec)),
            (f"{prefix}README.md", self.render_readme(spec)),
        ]

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
            return {"kind": kind, "status": "blocked", "reason": "target_project_missing", "target_project": str(target_root)}

        checked_files = []
        for relative_path, content in files:
            target = (target_root / relative_path).resolve()
            if Path(relative_path).is_absolute() or not self.is_inside(target_root, target):
                return {"kind": kind, "status": "blocked", "reason": "path_outside_target_project", "path": relative_path}
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
                "existing_files": [str(path) for path in existing],
                **extra,
            }

        written_files = []
        for _relative_path, target, content in checked_files:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written_files.append({"path": str(target), "bytes": len(content.encode("utf-8"))})
        return {"kind": kind, "status": "written", "dry_run": False, "written_files": written_files, **extra}

    def render_python_handler(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                '"""AWS Lambda handler generated by aws-lambda-builder."""',
                "",
                "from __future__ import annotations",
                "",
                "import json",
                "import logging",
                "import os",
                "from typing import Any",
                "",
                "logger = logging.getLogger()",
                "logger.setLevel(logging.INFO)",
                "",
                "",
                "def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:",
                "    request_id = getattr(context, \"aws_request_id\", \"local\")",
                "    logger.info(json.dumps({\"message\": \"lambda_started\", \"request_id\": request_id}))",
                "    response = {",
                f"        \"lambda\": {spec['lambda_slug']!r},",
                "        \"request_id\": request_id,",
                "        \"received_keys\": sorted(event.keys()) if isinstance(event, dict) else [],",
                "        \"configured_env\": sorted(key for key in os.environ if key.startswith(\"APP_\")),",
                "    }",
                "    return {\"statusCode\": 200, \"body\": json.dumps(response)}",
                "",
            ]
        )

    def render_python_test(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                "import json",
                "import sys",
                "from pathlib import Path",
                "",
                "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / \"src\"))",
                "from handler import lambda_handler",
                "",
                "",
                "class Context:",
                "    aws_request_id = \"test-request\"",
                "",
                "",
                "def test_lambda_handler_returns_success():",
                f"    event = json.loads((Path(__file__).resolve().parents[1] / \"events\" / {spec['trigger']!r}).read_text())",
                "    result = lambda_handler(event, Context())",
                "    assert result[\"statusCode\"] == 200",
                "    body = json.loads(result[\"body\"])",
                f"    assert body[\"lambda\"] == {spec['lambda_slug']!r}",
                "",
            ]
        )

    def render_node_handler(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                "\"use strict\";",
                "",
                "exports.handler = async function handler(event, context) {",
                "  const requestId = context && context.awsRequestId ? context.awsRequestId : \"local\";",
                "  console.log(JSON.stringify({ message: \"lambda_started\", request_id: requestId }));",
                "  const body = {",
                f"    lambda: {json.dumps(spec['lambda_slug'])},",
                "    request_id: requestId,",
                "    received_keys: event && typeof event === \"object\" ? Object.keys(event).sort() : [],",
                "    configured_env: Object.keys(process.env).filter((key) => key.startsWith(\"APP_\")).sort()",
                "  };",
                "  return { statusCode: 200, body: JSON.stringify(body) };",
                "};",
                "",
            ]
        )

    def render_node_test(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                "\"use strict\";",
                "",
                "const assert = require(\"node:assert\");",
                "const fs = require(\"node:fs\");",
                "const path = require(\"node:path\");",
                "const { handler } = require(\"../src/handler\");",
                "",
                "(async () => {",
                f"  const event = JSON.parse(fs.readFileSync(path.join(__dirname, \"..\", \"events\", {json.dumps(spec['trigger'])})));",
                "  const result = await handler(event, { awsRequestId: \"test-request\" });",
                "  assert.equal(result.statusCode, 200);",
                "  const body = JSON.parse(result.body);",
                f"  assert.equal(body.lambda, {json.dumps(spec['lambda_slug'])});",
                "})();",
                "",
            ]
        )

    def render_package_json(self, spec: dict[str, Any]) -> str:
        return json.dumps(
            {
                "name": spec["lambda_slug"],
                "version": "0.1.0",
                "private": True,
                "type": "commonjs",
                "scripts": {"test": "node tests/handler.test.js"},
            },
            indent=2,
        ) + "\n"

    def render_event_fixture(self, spec: dict[str, Any]) -> str:
        fixtures = {
            "api-gateway": {"requestContext": {"requestId": "local-request"}, "body": "{\"message\":\"hello\"}", "httpMethod": "POST"},
            "eventbridge-schedule": {"source": "aws.events", "detail-type": "Scheduled Event", "detail": {}},
            "sqs": {"Records": [{"messageId": "local-message", "body": "{\"message\":\"hello\"}"}]},
            "sns": {"Records": [{"Sns": {"Message": "{\"message\":\"hello\"}"}}]},
            "s3-event": {"Records": [{"s3": {"bucket": {"name": "example-bucket"}, "object": {"key": "example.txt"}}}]},
            "manual-test-event": {"message": "hello"},
        }
        return json.dumps(fixtures[spec["trigger"]], indent=2) + "\n"

    def render_sam_template(self, spec: dict[str, Any]) -> str:
        env_vars = {item["name"]: item["value"] for item in spec["environment_variables"]}
        events = self.sam_event(spec)
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Transform": "AWS::Serverless-2016-10-31",
            "Description": spec["purpose"],
            "Resources": {
                "LambdaFunction": {
                    "Type": "AWS::Serverless::Function",
                    "Properties": {
                        "FunctionName": spec["lambda_slug"],
                        "Runtime": spec["runtime"],
                        "Handler": spec["handler"],
                        "CodeUri": "src/",
                        "Timeout": spec["timeout_seconds"],
                        "MemorySize": spec["memory_mb"],
                        "Environment": {"Variables": env_vars},
                        "Policies": [{"Statement": [self.iam_statement(permission) for permission in spec["iam_permissions"]]}],
                        "Events": events,
                    },
                }
            },
        }
        return yaml.safe_dump(template, sort_keys=False, allow_unicode=False)

    def render_readme(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                f"# {spec['lambda_name']}",
                "",
                spec["purpose"],
                "",
                "## Local Test",
                "",
                "```bash",
                "python -m pytest tests",
                "npm test",
                "```",
                "",
                "Run only the command that matches the generated runtime.",
                "",
                "## Deploy",
                "",
                "Deploy real is not performed by aws-lambda-builder. Use deploy-lambda-plan to review commands and checklist.",
                "",
                "## Security",
                "",
                "- Review IAM before deploy.",
                "- Resolve secrets through environment references, SSM or Secrets Manager.",
                "- Do not commit `.env` files.",
                "",
            ]
        )

    def sam_event(self, spec: dict[str, Any]) -> dict[str, Any]:
        trigger = spec["trigger"]
        if trigger == "api-gateway":
            return {"ApiEvent": {"Type": "Api", "Properties": {"Path": "/", "Method": "post"}}}
        if trigger == "eventbridge-schedule":
            return {"ScheduleEvent": {"Type": "Schedule", "Properties": {"Schedule": "rate(5 minutes)"}}}
        if trigger == "sqs":
            return {"SQSEvent": {"Type": "SQS", "Properties": {"Queue": "<queue-arn>"}}}
        if trigger == "sns":
            return {"SNSEvent": {"Type": "SNS", "Properties": {"Topic": "<topic-arn>"}}}
        if trigger == "s3-event":
            return {"S3Event": {"Type": "S3", "Properties": {"Bucket": "<bucket-name>", "Events": "s3:ObjectCreated:*"}}}
        return {"ManualTestEvent": {"Type": "Schedule", "Properties": {"Schedule": "rate(365 days)", "Enabled": False}}}

    def iam_statement(self, permission: dict[str, str]) -> dict[str, str]:
        return {"Effect": "Allow", "Action": permission["action"], "Resource": permission["resource"]}

    def deploy_commands(self, spec: dict[str, Any]) -> list[str]:
        if spec["deploy_strategy"] == "sam":
            return ["sam build", "sam deploy --guided"]
        if spec["deploy_strategy"] == "serverless":
            return ["serverless package", "serverless deploy"]
        return ["zip package locally", "review template.yaml", "deploy manually after separate approval"]

    def package_file_plan(self, project_root: Path) -> list[Path]:
        files: list[Path] = []
        for path in sorted(project_root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(project_root)
            if any(part in EXCLUDED_PACKAGE_PARTS for part in relative.parts):
                continue
            if path.name in EXCLUDED_PACKAGE_NAMES or path.suffix == ".pyc":
                continue
            files.append(path)
        return files

    def lambda_summary(self, spec: dict[str, Any]) -> dict[str, Any]:
        return {"name": spec["lambda_name"], "slug": spec["lambda_slug"], "purpose": spec["purpose"]}

    def public_file_plan(self, files: list[tuple[str, str]]) -> list[dict[str, Any]]:
        return [{"path": path, "bytes": len(content.encode("utf-8"))} for path, content in files]

    def open_questions(self, spec: dict[str, Any]) -> list[str]:
        questions: list[str] = []
        if spec["trigger"] in ASYNC_TRIGGERS and not spec["observability"].get("dlq_or_destination"):
            questions.append("Qual DLQ ou destination deve ser usada para falhas assíncronas?")
        if any(permission["resource"] == "*" for permission in spec["iam_permissions"]):
            questions.append("Quais ARNs concretos podem substituir resource `*` antes do deploy?")
        return questions

    def normalize_env_var(self, value: Any) -> dict[str, str]:
        if not isinstance(value, dict):
            return {"name": str(value), "value": ""}
        return {"name": str(value.get("name") or "").strip(), "value": str(value.get("value") or "").strip()}

    def normalize_iam_permission(self, value: Any) -> dict[str, str]:
        if not isinstance(value, dict):
            return {"action": str(value), "resource": "*", "justification": ""}
        return {
            "action": str(value.get("action") or "").strip(),
            "resource": str(value.get("resource") or "").strip(),
            "justification": str(value.get("justification") or "").strip(),
        }

    def question_for_missing_field(self, field: str) -> str:
        return f"Informe `{field}` para planejar a Lambda."

    def as_int(self, value: Any, field: str) -> int:
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise AwsLambdaBuilderError(f"{field} must be an integer") from exc

    def slugify(self, value: str) -> str:
        slug = SLUG_PATTERN.sub("-", value.lower()).strip("-")
        return slug or "lambda-function"

    def iter_key_values(self, value: Any):
        if isinstance(value, dict):
            for key, child in value.items():
                yield str(key), child
                yield from self.iter_key_values(child)
        elif isinstance(value, list):
            for child in value:
                yield from self.iter_key_values(child)

    def is_inside(self, root: Path, target: Path) -> bool:
        try:
            target.relative_to(root.resolve())
            return True
        except ValueError:
            return False
