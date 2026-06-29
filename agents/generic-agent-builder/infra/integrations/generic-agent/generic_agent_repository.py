"""Repository for deterministic generic agent generation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml


TARGET_HOSTS = {"codex", "claude", "cursor", "opencode", "generic"}
REQUIRED_SPEC_FIELDS = ("target_host", "agent_name", "purpose", "domain_context")
FORBIDDEN_MARKER_PATTERN = re.compile(r"\b(?:SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY)\b(?:\s*[:=])?")
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


class GenericAgentError(RuntimeError):
    """Raised when the builder cannot read or process an input spec."""


class GenericAgentRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[5]

    def plan_generic_agent(self, *, spec_path: Path) -> dict[str, Any]:
        spec = self.load_spec(spec_path)
        spec_result = self.validate_spec(spec)
        if spec_result["status"] != "ok":
            return spec_result

        normalized = self.normalize_spec(spec)
        blocked = self.detect_forbidden_content(normalized)
        if blocked:
            return blocked

        artifacts = self.build_project_files(normalized)
        return {
            "kind": "generic-agent-plan",
            "status": "ok",
            "target_host": normalized["target_host"],
            "agent": self.agent_summary(normalized),
            "planned_artifacts": self.public_file_plan(artifacts),
            "write_policy": "read_only",
            "notes": self.host_notes(normalized["target_host"]),
            "questions": self.open_questions(normalized),
        }

    def generate_agent_instructions(self, *, spec_path: Path) -> dict[str, Any]:
        plan = self.plan_generic_agent(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        spec = self.normalize_spec(self.load_spec(spec_path))
        content = self.render_instructions(spec)
        return {
            "kind": "generic-agent-instructions",
            "status": "ok",
            "target_host": spec["target_host"],
            "artifact": "generic-agent-instructions.md",
            "content": content,
            "bytes": len(content.encode("utf-8")),
            "write_policy": "output_only",
        }

    def generate_skill(self, *, spec_path: Path) -> dict[str, Any]:
        plan = self.plan_generic_agent(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        spec = self.normalize_spec(self.load_spec(spec_path))
        content = self.render_skill(spec)
        return {
            "kind": "generic-agent-skill",
            "status": "ok",
            "target_host": spec["target_host"],
            "artifact": "SKILL.md",
            "content": content,
            "bytes": len(content.encode("utf-8")),
            "write_policy": "output_only",
        }

    def generate_project_agent_files(
        self,
        *,
        spec_path: Path,
        execute: bool = False,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan_generic_agent(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        spec = self.normalize_spec(self.load_spec(spec_path))
        target_project = spec.get("target_project")
        if not target_project:
            return {
                "kind": "generic-agent-project-files",
                "status": "needs-input",
                "missing_fields": ["target_project"],
                "questions": ["Qual e o caminho do projeto destino?"],
            }

        target_root = Path(str(target_project)).expanduser().resolve()
        if not target_root.exists() or not target_root.is_dir():
            return {
                "kind": "generic-agent-project-files",
                "status": "blocked",
                "reason": "target_project_missing",
                "target_project": str(target_root),
                "risks": ["target_project must exist before files can be written."],
            }

        files = self.build_project_files(spec)
        checked_files = []
        for relative_path, content in files:
            target = (target_root / relative_path).resolve()
            if Path(relative_path).is_absolute() or not self.is_inside(target_root, target):
                return {
                    "kind": "generic-agent-project-files",
                    "status": "blocked",
                    "reason": "path_outside_target_project",
                    "path": relative_path,
                    "target_project": str(target_root),
                }
            checked_files.append((target, content))

        if not execute:
            return {
                "kind": "generic-agent-project-files",
                "status": "planned",
                "dry_run": True,
                "target_host": spec["target_host"],
                "target_project": str(target_root),
                "planned_files": [
                    {
                        "path": relative_path,
                        "absolute_path": str((target_root / relative_path).resolve()),
                        "bytes": len(content.encode("utf-8")),
                    }
                    for relative_path, content in files
                ],
                "next_steps": ["Rerun with --execute after reviewing the planned files."],
            }

        existing = [target for target, _content in checked_files if target.exists()]
        if existing and not allow_overwrite:
            return {
                "kind": "generic-agent-project-files",
                "status": "blocked",
                "reason": "target_exists",
                "target_project": str(target_root),
                "existing_files": [str(path) for path in existing],
                "next_steps": ["Rerun with --allow-overwrite only after reviewing the existing files."],
            }

        written_files = []
        for target, content in checked_files:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written_files.append({"path": str(target), "bytes": len(content.encode("utf-8"))})

        return {
            "kind": "generic-agent-project-files",
            "status": "written",
            "dry_run": False,
            "target_host": spec["target_host"],
            "target_project": str(target_root),
            "written_files": written_files,
        }

    def review_generic_agent(self, *, text: str, target_host: str = "generic") -> dict[str, Any]:
        normalized_host = str(target_host or "generic").strip().lower()
        findings: list[str] = []
        if normalized_host not in TARGET_HOSTS:
            findings.append(f"unsupported target_host: {target_host}")
        if not text.strip():
            findings.append("agent instructions are empty")
        lower_text = text.lower()
        if "guardrail" not in lower_text:
            findings.append("agent instructions must include explicit guardrails")
        if "ask a human" not in lower_text and "human" not in lower_text:
            findings.append("agent instructions should state when to ask a human")
        if self.detect_text_forbidden_content(text):
            findings.append("agent instructions contain a secret marker or URL")
        if normalized_host == "cursor" and "agents.md" in lower_text and ".cursor/rules" not in lower_text:
            findings.append("cursor agents should prefer .cursor/rules/*.mdc over AGENTS.md")

        valid = not findings
        return {
            "kind": "generic-agent-review",
            "status": "ok" if valid else "failed",
            "valid": valid,
            "target_host": normalized_host,
            "findings": findings,
            "write_policy": "read_only",
        }

    def load_spec(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise GenericAgentError(f"spec not found: {path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            payload = json.loads(text)
        else:
            payload = yaml.safe_load(text) or {}
        if not isinstance(payload, dict):
            raise GenericAgentError("spec must be a mapping")
        return payload

    def validate_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        missing = [field for field in REQUIRED_SPEC_FIELDS if not spec.get(field)]
        if missing:
            return {
                "kind": "generic-agent-plan",
                "status": "needs-input",
                "missing_fields": missing,
                "questions": [self.question_for_missing_field(field) for field in missing],
            }

        target_host = str(spec.get("target_host") or "").strip().lower()
        if target_host not in TARGET_HOSTS:
            return {
                "kind": "generic-agent-plan",
                "status": "blocked",
                "reason": "unsupported_target_host",
                "target_host": target_host,
                "supported_hosts": sorted(TARGET_HOSTS),
            }
        for field in ("allowed_tools", "forbidden_actions", "quality_gates"):
            if spec.get(field) is not None and not isinstance(spec[field], list):
                return {
                    "kind": "generic-agent-plan",
                    "status": "blocked",
                    "reason": "invalid_list_field",
                    "field": field,
                    "risks": [f"{field} must be a list when provided."],
                }
        return {"status": "ok"}

    def normalize_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(spec)
        normalized["target_host"] = str(spec["target_host"]).strip().lower()
        normalized["agent_name"] = " ".join(str(spec["agent_name"]).split())
        normalized["agent_slug"] = self.slugify(normalized["agent_name"])
        normalized["purpose"] = " ".join(str(spec["purpose"]).split())
        normalized["domain_context"] = " ".join(str(spec["domain_context"]).split())
        normalized["allowed_tools"] = [str(item).strip() for item in spec.get("allowed_tools") or []]
        normalized["forbidden_actions"] = [str(item).strip() for item in spec.get("forbidden_actions") or []]
        normalized["output_format"] = " ".join(str(spec.get("output_format") or "Markdown report.").split())
        normalized["quality_gates"] = [str(item).strip() for item in spec.get("quality_gates") or []]
        if spec.get("target_project"):
            normalized["target_project"] = str(spec["target_project"]).strip()
        return normalized

    def detect_forbidden_content(self, spec: dict[str, Any]) -> dict[str, Any] | None:
        for value in self.iter_strings(spec):
            if self.detect_text_forbidden_content(value):
                return {
                    "kind": "generic-agent-plan",
                    "status": "blocked",
                    "reason": "forbidden_sensitive_marker",
                    "risks": ["Spec contains a URL or text that looks like a secret or credential marker."],
                }
        return None

    def detect_text_forbidden_content(self, value: str) -> bool:
        return bool(FORBIDDEN_MARKER_PATTERN.search(value)) or "http://" in value or "https://" in value

    def build_project_files(self, spec: dict[str, Any]) -> list[tuple[str, str]]:
        target_host = spec["target_host"]
        instructions = self.render_instructions(spec)
        if target_host in {"codex", "opencode", "generic"}:
            return [("AGENTS.md", instructions)]
        if target_host == "claude":
            return [("CLAUDE.md", instructions), ("SKILL.md", self.render_skill(spec))]
        if target_host == "cursor":
            return [(f".cursor/rules/{spec['agent_slug']}.mdc", instructions)]
        raise GenericAgentError(f"unsupported target_host: {target_host}")

    def render_instructions(self, spec: dict[str, Any]) -> str:
        allowed_tools = self.markdown_list(spec["allowed_tools"], fallback="No host tools are assumed.")
        forbidden_actions = self.markdown_list(
            spec["forbidden_actions"],
            fallback="Do not bypass host permissions or operate outside the declared purpose.",
        )
        quality_gates = self.markdown_list(
            spec["quality_gates"],
            fallback="State assumptions, cite local evidence when available and expose unresolved questions.",
        )
        host_detail = self.host_detail(spec["target_host"])
        return "\n".join(
            [
                f"# {spec['agent_name']}",
                "",
                f"Target host: `{spec['target_host']}`.",
                "",
                "## Role",
                "",
                spec["purpose"],
                "",
                "## Domain Context",
                "",
                spec["domain_context"],
                "",
                "## Behavior",
                "",
                "- Stay inside the declared purpose and domain context.",
                "- Treat missing information as unknown, not as fact.",
                "- Use only declared tools and host capabilities.",
                f"- Host-specific note: {host_detail}",
                "",
                "## Workflow",
                "",
                "1. Restate the task in operational terms.",
                "2. Check scope, available tools and forbidden actions.",
                "3. Gather only the context needed for the task.",
                "4. Produce the requested artifact in the declared output format.",
                "5. List assumptions, risks and unresolved questions.",
                "",
                "## Allowed Tools",
                "",
                allowed_tools,
                "",
                "## Forbidden Actions",
                "",
                forbidden_actions,
                "",
                "## Guardrails",
                "",
                "- Do not ignore, bypass or weaken host permissions.",
                "- Do not request, store or print secrets, tokens or private credentials.",
                "- Do not claim access to tools that were not declared above.",
                "- Do not perform external writes unless the host and user explicitly permit it.",
                "",
                "## Output Format",
                "",
                spec["output_format"],
                "",
                "## Quality Gates",
                "",
                quality_gates,
                "",
                "## Human Escalation",
                "",
                "Ask a human before destructive actions, external writes, credential handling, "
                "ambiguous scope changes or decisions with unclear business impact.",
                "",
            ]
        )

    def render_skill(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                "---",
                f"name: {spec['agent_slug']}",
                f"description: {spec['purpose']}",
                "---",
                "",
                f"# {spec['agent_name']}",
                "",
                "Use this skill when the user needs this portable generic agent:",
                "",
                spec["purpose"],
                "",
                self.render_instructions(spec),
            ]
        )

    def public_file_plan(self, files: list[tuple[str, str]]) -> list[dict[str, Any]]:
        return [{"path": path, "bytes": len(content.encode("utf-8"))} for path, content in files]

    def markdown_list(self, values: list[str], *, fallback: str) -> str:
        if not values:
            return f"- {fallback}"
        return "\n".join(f"- {value}" for value in values)

    def host_detail(self, target_host: str) -> str:
        details = {
            "codex": "AGENTS.md is the preferred portable project instruction file.",
            "claude": "CLAUDE.md and SKILL.md can be exported, but installation stays manual.",
            "cursor": "Use .cursor/rules/*.mdc to avoid mixing host contracts.",
            "opencode": "AGENTS.md keeps the agent portable and can coexist with optional MCP setup.",
            "generic": "No host-specific runtime is assumed.",
        }
        return details[target_host]

    def host_notes(self, target_host: str) -> list[str]:
        notes = {
            "codex": ["Generate AGENTS.md for project-level instructions."],
            "claude": ["Generate CLAUDE.md and optional SKILL.md content."],
            "cursor": ["Generate .cursor/rules/<agent>.mdc."],
            "opencode": ["Generate AGENTS.md; MCP remains optional and external."],
            "generic": ["Generate AGENTS.md-compatible portable instructions."],
        }
        return notes[target_host]

    def open_questions(self, spec: dict[str, Any]) -> list[str]:
        questions: list[str] = []
        if not spec["allowed_tools"]:
            questions.append("Quais tools o host realmente disponibiliza para este agente?")
        if not spec["quality_gates"]:
            questions.append("Quais criterios de qualidade tornam a resposta aceitavel?")
        if spec["target_host"] == "generic":
            questions.append("Este agente sera usado em algum host especifico depois?")
        return questions

    def agent_summary(self, spec: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": spec["agent_name"],
            "slug": spec["agent_slug"],
            "purpose": spec["purpose"],
            "domain_context": spec["domain_context"],
        }

    def question_for_missing_field(self, field: str) -> str:
        questions = {
            "target_host": "Qual host alvo deve receber o agente?",
            "agent_name": "Qual sera o nome do agente generico?",
            "purpose": "Qual problema este agente deve resolver?",
            "domain_context": "Qual contexto de dominio o agente precisa conhecer?",
        }
        return questions.get(field, f"Informe o campo obrigatorio {field}.")

    def slugify(self, value: str) -> str:
        slug = SLUG_PATTERN.sub("-", value.strip().lower()).strip("-")
        return slug or "generic-agent"

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
