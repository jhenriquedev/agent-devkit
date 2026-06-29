"""Repository for deterministic Python automation generation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml


REQUIRED_SPEC_FIELDS = ("automation_name", "purpose", "inputs", "outputs", "systems", "side_effects")
IDEMPOTENCY_CLASSES = {"safe-repeat", "creates-artifact", "updates-local", "external-write", "destructive"}
OUT_OF_SCOPE_DEPENDENCIES = {
    "selenium": "problem 16",
    "pyautogui": "problem 17",
    "playwright": "problem 27",
}
FORBIDDEN_MARKER_PATTERN = re.compile(r"\b(?:SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY)\b\s*[:=]")
KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")
STANDARD_LIBRARY_HINTS = {
    "argparse",
    "csv",
    "datetime",
    "json",
    "logging",
    "os",
    "pathlib",
    "re",
    "shutil",
    "subprocess",
    "sys",
    "tempfile",
    "time",
    "urllib",
}


class PythonAutomationError(RuntimeError):
    """Raised when the builder cannot read or process an input spec."""


class PythonAutomationRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[5]

    def plan_python_automation(self, *, spec_path: Path) -> dict[str, Any]:
        spec = self.load_spec(spec_path)
        spec_result = self.validate_spec(spec)
        if spec_result["status"] != "ok":
            return spec_result

        normalized = self.normalize_spec(spec)
        blocked = self.detect_forbidden_content(normalized)
        if blocked:
            return blocked

        dependency_block = self.detect_out_of_scope_dependencies(normalized["dependencies"])
        if dependency_block:
            return dependency_block

        files = self.build_automation_files(normalized)
        return {
            "kind": "python-automation-plan",
            "status": "ok",
            "automation": self.automation_summary(normalized),
            "idempotency": normalized["side_effects"],
            "risk": normalized["risk"],
            "write_policy": "read_only",
            "dependencies": self.dependency_plan(normalized["dependencies"]),
            "planned_artifacts": self.public_file_plan(files),
            "side_effect_guardrails": self.side_effect_guardrails(normalized["side_effects"]),
            "questions": self.open_questions(normalized),
        }

    def generate_python_automation(self, *, spec_path: Path) -> dict[str, Any]:
        plan = self.plan_python_automation(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        spec = self.normalize_spec(self.load_spec(spec_path))
        content = self.render_automation_py(spec)
        return {
            "kind": "python-automation-script",
            "status": "ok",
            "automation": self.automation_summary(spec),
            "artifact": "automation.py",
            "content": content,
            "bytes": len(content.encode("utf-8")),
            "write_policy": "output_only",
        }

    def generate_automation_project_files(
        self,
        *,
        spec_path: Path,
        execute: bool = False,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan_python_automation(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        spec = self.normalize_spec(self.load_spec(spec_path))
        target_project = spec.get("target_project")
        if not target_project:
            return {
                "kind": "python-automation-project-files",
                "status": "needs-input",
                "missing_fields": ["target_project"],
                "questions": ["Qual e o caminho do projeto destino?"],
            }

        target_root = Path(str(target_project)).expanduser().resolve()
        files = self.build_automation_files(spec, base_dir=spec["automation_slug"])
        return self.write_or_plan_files(
            kind="python-automation-project-files",
            files=files,
            target_root=target_root,
            execute=execute,
            allow_overwrite=allow_overwrite,
            extra={"automation": self.automation_summary(spec), "idempotency": spec["side_effects"]},
        )

    def review_python_automation(self, *, text: str, side_effects: str = "updates-local") -> dict[str, Any]:
        normalized_side_effects = str(side_effects or "updates-local").strip()
        findings: list[str] = []
        if not text.strip():
            findings.append("automation script is empty")
        lower_text = text.lower()
        if "--dry-run" not in text:
            findings.append("automation must expose --dry-run")
        if normalized_side_effects not in {"safe-repeat"} and "--execute" not in text:
            findings.append("automation with side effects must expose --execute")
        if normalized_side_effects not in {"safe-repeat"} and "--yes" not in text and "--confirm" not in text:
            findings.append("automation with side effects must require --yes or --confirm")
        if "logging" not in lower_text:
            findings.append("automation should use logging")
        if "return 0" not in text and "sys.exit(0)" not in text:
            findings.append("automation should return a predictable success exit code")
        if "redact" not in lower_text:
            findings.append("automation should include a redaction helper for public logs")
        if self.detect_text_forbidden_content(text):
            findings.append("automation contains a secret marker or URL")

        valid = not findings
        return {
            "kind": "python-automation-review",
            "status": "ok" if valid else "failed",
            "valid": valid,
            "side_effects": normalized_side_effects,
            "findings": findings,
            "write_policy": "read_only",
        }

    def wrap_automation_as_capability(
        self,
        *,
        spec_path: Path,
        agent_id: str,
        capability_id: str,
        execute: bool = False,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan_python_automation(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        if not KEBAB_CASE.match(agent_id):
            return {
                "kind": "python-automation-capability-wrapper",
                "status": "blocked",
                "reason": "invalid_agent_id",
                "risks": ["agent-id must be kebab-case."],
            }
        if not KEBAB_CASE.match(capability_id):
            return {
                "kind": "python-automation-capability-wrapper",
                "status": "blocked",
                "reason": "invalid_capability_id",
                "risks": ["capability-id must be kebab-case."],
            }

        spec = self.normalize_spec(self.load_spec(spec_path))
        target_project = spec.get("target_project")
        if not target_project:
            return {
                "kind": "python-automation-capability-wrapper",
                "status": "needs-input",
                "missing_fields": ["target_project"],
                "questions": ["Qual e o caminho do projeto destino?"],
            }

        target_root = Path(str(target_project)).expanduser().resolve()
        files = self.build_capability_wrapper_files(spec, agent_id=agent_id, capability_id=capability_id)
        return self.write_or_plan_files(
            kind="python-automation-capability-wrapper",
            files=files,
            target_root=target_root,
            execute=execute,
            allow_overwrite=allow_overwrite,
            extra={
                "agent_id": agent_id,
                "capability_id": capability_id,
                "capability_write_policy": self.capability_write_policy(spec["side_effects"]),
            },
        )

    def load_spec(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise PythonAutomationError(f"spec not found: {path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            payload = json.loads(text)
        else:
            payload = yaml.safe_load(text) or {}
        if not isinstance(payload, dict):
            raise PythonAutomationError("spec must be a mapping")
        return payload

    def validate_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        missing = [field for field in REQUIRED_SPEC_FIELDS if not spec.get(field)]
        if missing:
            return {
                "kind": "python-automation-plan",
                "status": "needs-input",
                "missing_fields": missing,
                "questions": [self.question_for_missing_field(field) for field in missing],
            }
        for field in ("inputs", "outputs", "systems", "dependencies", "quality_gates"):
            if spec.get(field) is not None and not isinstance(spec[field], list):
                return {
                    "kind": "python-automation-plan",
                    "status": "blocked",
                    "reason": "invalid_list_field",
                    "field": field,
                    "risks": [f"{field} must be a list when provided."],
                }
        side_effects = str(spec.get("side_effects") or "").strip()
        if side_effects not in IDEMPOTENCY_CLASSES:
            return {
                "kind": "python-automation-plan",
                "status": "blocked",
                "reason": "invalid_side_effects",
                "supported_values": sorted(IDEMPOTENCY_CLASSES),
            }
        return {"status": "ok"}

    def normalize_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(spec)
        normalized["automation_name"] = " ".join(str(spec["automation_name"]).split())
        normalized["automation_slug"] = self.slugify(normalized["automation_name"])
        normalized["purpose"] = " ".join(str(spec["purpose"]).split())
        normalized["inputs"] = [str(item).strip() for item in spec.get("inputs") or []]
        normalized["outputs"] = [str(item).strip() for item in spec.get("outputs") or []]
        normalized["systems"] = [str(item).strip() for item in spec.get("systems") or []]
        normalized["frequency"] = " ".join(str(spec.get("frequency") or "manual").split())
        normalized["risk"] = " ".join(str(spec.get("risk") or "medium").split())
        normalized["target_environment"] = " ".join(str(spec.get("target_environment") or "local").split())
        normalized["side_effects"] = str(spec["side_effects"]).strip()
        normalized["dependencies"] = [str(item).strip() for item in spec.get("dependencies") or []]
        normalized["quality_gates"] = [str(item).strip() for item in spec.get("quality_gates") or []]
        if spec.get("target_project"):
            normalized["target_project"] = str(spec["target_project"]).strip()
        return normalized

    def detect_forbidden_content(self, spec: dict[str, Any]) -> dict[str, Any] | None:
        for value in self.iter_strings(spec):
            if self.detect_text_forbidden_content(value):
                return {
                    "kind": "python-automation-plan",
                    "status": "blocked",
                    "reason": "forbidden_sensitive_marker",
                    "risks": ["Spec contains a URL or text that looks like a secret or credential marker."],
                }
        return None

    def detect_text_forbidden_content(self, value: str) -> bool:
        return bool(FORBIDDEN_MARKER_PATTERN.search(value)) or "http://" in value or "https://" in value

    def detect_out_of_scope_dependencies(self, dependencies: list[str]) -> dict[str, Any] | None:
        for dependency in dependencies:
            normalized = dependency.strip().lower().replace("_", "-")
            for blocked, problem in OUT_OF_SCOPE_DEPENDENCIES.items():
                if blocked in normalized:
                    return {
                        "kind": "python-automation-plan",
                        "status": "blocked",
                        "reason": "out_of_scope_dependency",
                        "dependency": dependency,
                        "next_steps": [f"Use {problem} for {blocked}-specific automation."],
                    }
        return None

    def build_automation_files(self, spec: dict[str, Any], *, base_dir: str = "") -> list[tuple[str, str]]:
        prefix = f"{base_dir}/" if base_dir else ""
        files = [
            (f"{prefix}automation.py", self.render_automation_py(spec)),
            (f"{prefix}README.md", self.render_readme(spec)),
            (f"{prefix}tests/test_automation.py", self.render_automation_test(spec)),
        ]
        requirements = self.render_requirements(spec)
        if requirements:
            files.append((f"{prefix}requirements.txt", requirements))
        return files

    def build_capability_wrapper_files(
        self,
        spec: dict[str, Any],
        *,
        agent_id: str,
        capability_id: str,
    ) -> list[tuple[str, str]]:
        base = f"agents/{agent_id}/capabilities/{capability_id}"
        return [
            (f"{base}/capability.yaml", self.render_capability_yaml(spec, agent_id=agent_id, capability_id=capability_id)),
            (f"{base}/workflow.md", self.render_capability_workflow(spec, capability_id=capability_id)),
            (f"{base}/decision-rules.md", self.render_capability_decision_rules(spec)),
            (f"{base}/runner.py", self.render_capability_runner(spec)),
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
                    {
                        "path": relative_path,
                        "absolute_path": str(target),
                        "bytes": len(content.encode("utf-8")),
                    }
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

    def render_automation_py(self, spec: dict[str, Any]) -> str:
        needs_confirmation = spec["side_effects"] != "safe-repeat"
        confirmation_block = [
            "    if args.execute and not args.yes:",
            "        logger.error(\"real execution requires --yes after reviewing --dry-run output\")",
            "        return 2",
        ]
        if not needs_confirmation:
            confirmation_block = [
                "    if args.execute and not args.yes:",
                "        logger.info(\"--yes not required for safe-repeat automation, continuing\")",
            ]

        lines = [
            "#!/usr/bin/env python3",
            f'"""Automation: {spec["automation_name"]}."""',
            "",
            "from __future__ import annotations",
            "",
            "import argparse",
            "import json",
            "import logging",
            "import sys",
            "from pathlib import Path",
            "",
            "",
            "SENSITIVE_MARKERS = (\"SECRET\", \"TOKEN\", \"PASSWORD\", \"API_KEY\", \"PRIVATE_KEY\")",
            "",
            "",
            "def redact(value: str) -> str:",
            "    text = str(value)",
            "    for marker in SENSITIVE_MARKERS:",
            "        if marker in text.upper():",
            "            return \"<redacted>\"",
            "    return text",
            "",
            "",
            "def build_parser() -> argparse.ArgumentParser:",
            f"    parser = argparse.ArgumentParser(description={spec['purpose']!r})",
            "    parser.add_argument(\"--dry-run\", action=\"store_true\", help=\"show planned actions without writing\")",
            "    parser.add_argument(\"--execute\", action=\"store_true\", help=\"apply the planned actions\")",
            "    parser.add_argument(\"--yes\", action=\"store_true\", help=\"confirm real execution after dry-run review\")",
            "    parser.add_argument(\"--input\", help=\"optional input path or identifier\")",
            "    parser.add_argument(\"--summary-json\", help=\"optional path for a JSON execution summary\")",
            "    return parser",
            "",
            "",
            "def planned_actions(args: argparse.Namespace) -> list[dict[str, str]]:",
            "    target = args.input or \"<input-not-provided>\"",
            "    return [",
            "        {",
            "            \"action\": \"inspect\",",
            "            \"target\": redact(target),",
            f"            \"side_effects\": {spec['side_effects']!r},",
            "        }",
            "    ]",
            "",
            "",
            "def write_summary(path: str | None, payload: dict) -> None:",
            "    if not path:",
            "        return",
            "    target = Path(path)",
            "    target.parent.mkdir(parents=True, exist_ok=True)",
            "    target.write_text(json.dumps(payload, indent=2) + \"\\n\", encoding=\"utf-8\")",
            "",
            "",
            "def main(argv: list[str] | None = None) -> int:",
            "    parser = build_parser()",
            "    args = parser.parse_args(argv)",
            "    logging.basicConfig(level=logging.INFO, format=\"%(levelname)s %(message)s\")",
            "    logger = logging.getLogger(\"automation\")",
            "",
            "    if args.execute and args.dry_run:",
            "        logger.error(\"choose either --dry-run or --execute\")",
            "        return 2",
            "",
            *confirmation_block,
            "",
            "    actions = planned_actions(args)",
            "    dry_run = not args.execute",
            "    payload = {",
            f"        \"automation\": {spec['automation_slug']!r},",
            "        \"dry_run\": dry_run,",
            "        \"actions\": actions,",
            "    }",
            "    logger.info(\"dry_run=%s actions=%s\", dry_run, len(actions))",
            "",
            "    if dry_run:",
            "        print(json.dumps(payload, indent=2))",
            "        return 0",
            "",
            "    # Add the approved write behavior here after validating the dry-run output.",
            "    write_summary(args.summary_json, payload)",
            "    print(json.dumps(payload, indent=2))",
            "    return 0",
            "",
            "",
            "if __name__ == \"__main__\":",
            "    raise SystemExit(main())",
            "",
        ]
        return "\n".join(lines)

    def render_readme(self, spec: dict[str, Any]) -> str:
        dependency_lines = self.markdown_list(spec["dependencies"], fallback="No external dependencies.")
        quality_lines = self.markdown_list(spec["quality_gates"], fallback="Review dry-run output before execution.")
        return "\n".join(
            [
                f"# {spec['automation_name']}",
                "",
                spec["purpose"],
                "",
                "## Contract",
                "",
                f"- Inputs: {', '.join(spec['inputs'])}",
                f"- Outputs: {', '.join(spec['outputs'])}",
                f"- Systems: {', '.join(spec['systems'])}",
                f"- Frequency: {spec['frequency']}",
                f"- Target environment: {spec['target_environment']}",
                f"- Side effects: {spec['side_effects']}",
                f"- Risk: {spec['risk']}",
                "",
                "## Usage",
                "",
                "```bash",
                "python automation.py --dry-run --input ./data",
                "python automation.py --execute --yes --input ./data",
                "```",
                "",
                "## Dependencies",
                "",
                dependency_lines,
                "",
                "## Quality Gates",
                "",
                quality_lines,
                "",
                "## Guardrails",
                "",
                "- Do not hardcode secrets.",
                "- Review dry-run output before execution.",
                "- Use `--execute --yes` only after validating targets and blast radius.",
                "- Keep logs free of sensitive values.",
                "",
            ]
        )

    def render_automation_test(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                "import json",
                "import subprocess",
                "import sys",
                "from pathlib import Path",
                "",
                "",
                "def test_automation_dry_run_returns_json():",
                "    script = Path(__file__).resolve().parents[1] / \"automation.py\"",
                "    result = subprocess.run(",
                "        [sys.executable, str(script), \"--dry-run\", \"--input\", \"fixture\"],",
                "        text=True,",
                "        capture_output=True,",
                "        check=False,",
                "    )",
                "    assert result.returncode == 0, result.stderr",
                "    payload = json.loads(result.stdout)",
                "    assert payload[\"dry_run\"] is True",
                f"    assert payload[\"automation\"] == {spec['automation_slug']!r}",
                "",
            ]
        )

    def render_requirements(self, spec: dict[str, Any]) -> str:
        external = [
            dependency
            for dependency in spec["dependencies"]
            if dependency and dependency.strip().lower() not in STANDARD_LIBRARY_HINTS
        ]
        return "".join(f"{dependency}\n" for dependency in external)

    def render_capability_yaml(self, spec: dict[str, Any], *, agent_id: str, capability_id: str) -> str:
        payload = {
            "id": f"{agent_id}.{capability_id}",
            "kind": "capability",
            "name": self.title_from_id(capability_id),
            "version": "0.1.0",
            "status": "draft",
            "purpose": spec["purpose"],
            "entrypoint": {"runner": "runner.py", "workflow": "workflow.md"},
            "inputs": {"required": [], "optional": ["dry-run", "execute", "yes", "input", "summary-json"]},
            "outputs": {"artifacts": ["automation-result.json"]},
            "write_policy": self.capability_write_policy(spec["side_effects"]),
        }
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)

    def render_capability_workflow(self, spec: dict[str, Any], *, capability_id: str) -> str:
        return "\n".join(
            [
                "# Workflow",
                "",
                f"1. Executar `{capability_id}` em dry-run por padrao.",
                "2. Validar alvo, entrada e resumo planejado.",
                "3. Usar `--execute --yes --confirm-execute` apenas apos revisar o dry-run.",
                "4. Retornar JSON com status, dry-run e acoes.",
                "",
            ]
        )

    def render_capability_decision_rules(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                "# Decision Rules",
                "",
                f"- Side effects classificados como `{spec['side_effects']}`.",
                "- Nao persistir segredos.",
                "- Escrita real exige confirmacao do runtime e do script.",
                "- Falhas devem retornar exit code diferente de zero.",
                "",
            ]
        )

    def render_capability_runner(self, spec: dict[str, Any]) -> str:
        return self.render_automation_py(spec)

    def capability_write_policy(self, side_effects: str) -> str:
        mapping = {
            "safe-repeat": "read_only",
            "creates-artifact": "local_write",
            "updates-local": "local_write",
            "external-write": "confirm",
            "destructive": "blocked_by_default",
        }
        return mapping[side_effects]

    def dependency_plan(self, dependencies: list[str]) -> list[dict[str, Any]]:
        result = []
        for dependency in dependencies:
            normalized = dependency.strip().lower()
            result.append(
                {
                    "name": dependency,
                    "kind": "standard-library" if normalized in STANDARD_LIBRARY_HINTS else "external",
                    "decision": "allowed" if normalized in STANDARD_LIBRARY_HINTS else "review-required",
                }
            )
        return result

    def side_effect_guardrails(self, side_effects: str) -> list[str]:
        guardrails = {
            "safe-repeat": ["Dry-run still available for inspection."],
            "creates-artifact": ["Show target artifact path in dry-run.", "Use --execute --yes for creation."],
            "updates-local": ["Show affected local paths in dry-run.", "Use --execute --yes for writes."],
            "external-write": ["Require external approval and provider-specific confirmation."],
            "destructive": ["Blocked by default; require a separate risk decision before execution."],
        }
        return guardrails[side_effects]

    def automation_summary(self, spec: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": spec["automation_name"],
            "slug": spec["automation_slug"],
            "purpose": spec["purpose"],
            "systems": spec["systems"],
        }

    def public_file_plan(self, files: list[tuple[str, str]]) -> list[dict[str, Any]]:
        return [{"path": path, "bytes": len(content.encode("utf-8"))} for path, content in files]

    def open_questions(self, spec: dict[str, Any]) -> list[str]:
        questions: list[str] = []
        if not spec["quality_gates"]:
            questions.append("Quais criterios confirmam que a automacao executou corretamente?")
        if any(item["kind"] == "external" for item in self.dependency_plan(spec["dependencies"])):
            questions.append("A dependencia externa e realmente necessaria ou standard library resolve?")
        if spec["side_effects"] in {"external-write", "destructive"}:
            questions.append("Qual aprovacao humana e rollback sao exigidos antes da execucao real?")
        return questions

    def question_for_missing_field(self, field: str) -> str:
        questions = {
            "automation_name": "Qual sera o nome da automacao?",
            "purpose": "Qual tarefa repetitiva a automacao deve resolver?",
            "inputs": "Quais entradas a automacao recebe?",
            "outputs": "Quais saidas a automacao produz?",
            "systems": "Quais sistemas ou recursos a automacao toca?",
            "side_effects": "Qual classificacao de side effects se aplica?",
        }
        return questions.get(field, f"Informe o campo obrigatorio {field}.")

    def markdown_list(self, values: list[str], *, fallback: str) -> str:
        if not values:
            return f"- {fallback}"
        return "\n".join(f"- {value}" for value in values)

    def slugify(self, value: str) -> str:
        slug = SLUG_PATTERN.sub("-", value.strip().lower()).strip("-")
        return slug or "python-automation"

    def title_from_id(self, value: str) -> str:
        return " ".join(part.capitalize() for part in value.split("-"))

    def iter_strings(self, value: Any):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for item in value.values():
                yield from self.iter_strings(item)
        elif isinstance(value, list):
            for item in value:
                yield from self.iter_strings(item)

    def is_inside(self, root: Path, target: Path) -> bool:
        try:
            target.relative_to(root)
            return True
        except ValueError:
            return False
