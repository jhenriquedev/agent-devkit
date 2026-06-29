"""Repository for deterministic Agent DevKit agent scaffolding."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml


KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_SPEC_FIELDS = ("agent_id", "name", "purpose", "domain", "capabilities")
CANONICAL_WRITE_POLICIES = {
    "read_only",
    "dry_run",
    "output_only",
    "local_write",
    "local_config_write",
    "confirm",
    "blocked_by_default",
    "delegated",
}
FORBIDDEN_TEXT_MARKERS = ("SECRET", "TOKEN", "PASSWORD", "API_KEY", "PRIVATE_KEY")


class AgentBuilderError(RuntimeError):
    """Raised when the builder cannot read or process an input spec."""


class AgentBuilderRepository:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[5]
        self.agents_dir = self.root / "agents"

    def plan_agent(self, *, spec_path: Path) -> dict[str, Any]:
        spec = self.load_spec(spec_path)
        spec_result = self.validate_spec(spec)
        if spec_result["status"] != "ok":
            return spec_result

        normalized = self.normalize_spec(spec)
        blocked = self.detect_forbidden_content(normalized)
        if blocked:
            return blocked

        files = self.build_files(normalized)
        return {
            "kind": "agent-builder-plan",
            "status": "ok",
            "agent": self.agent_summary(normalized),
            "capabilities": [self.capability_summary(item) for item in normalized["capabilities"]],
            "providers": normalized.get("providers", []),
            "risk_profile": normalized.get("risk_profile", "medium"),
            "planned_files": self.public_file_plan(files),
            "questions": self.open_questions(normalized),
            "write_policy": "read_only",
        }

    def scaffold_agent(
        self,
        *,
        spec_path: Path,
        execute: bool = False,
        allow_overwrite: bool = False,
    ) -> dict[str, Any]:
        plan = self.plan_agent(spec_path=spec_path)
        if plan["status"] != "ok":
            return plan

        agent_id = plan["agent"]["id"]
        agent_root = self.agents_dir / agent_id
        if agent_root.exists() and not allow_overwrite:
            return {
                "kind": "agent-builder-scaffold",
                "status": "blocked",
                "reason": "agent_exists",
                "agent": plan["agent"],
                "risks": ["Agent directory already exists and overwrite was not explicitly allowed."],
                "next_steps": ["Use a different agent_id or rerun with --allow-overwrite after reviewing the existing agent."],
            }

        files = self.build_files(self.normalize_spec(self.load_spec(spec_path)))
        if not execute:
            return {
                "kind": "agent-builder-scaffold",
                "status": "planned",
                "dry_run": True,
                "agent": plan["agent"],
                "planned_files": self.public_file_plan(files),
                "next_steps": ["Rerun with --execute --confirm-execute to write files locally."],
            }

        written_files = []
        for relative_path, content in files:
            target = (self.root / relative_path).resolve()
            if not self.is_inside(agent_root.resolve(), target):
                return {
                    "kind": "agent-builder-scaffold",
                    "status": "blocked",
                    "reason": "path_outside_agent",
                    "agent": plan["agent"],
                    "path": relative_path,
                }
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written_files.append({"path": relative_path, "bytes": len(content.encode("utf-8"))})

        return {
            "kind": "agent-builder-scaffold",
            "status": "written",
            "dry_run": False,
            "agent": plan["agent"],
            "written_files": written_files,
            "next_steps": [
                f"Run agent run agent-devkit-agent-builder validate-agent-contract --agent-id {agent_id}.",
                "Run scripts/validate-repo.py before considering the agent ready.",
            ],
        }

    def validate_agent_contract(self, *, agent_id: str) -> dict[str, Any]:
        if not KEBAB_CASE.match(agent_id):
            return {
                "kind": "agent-builder-validation",
                "status": "failed",
                "valid": False,
                "agent_id": agent_id,
                "errors": ["agent_id must be kebab-case"],
                "warnings": [],
            }

        agent_root = self.agents_dir / agent_id
        errors: list[str] = []
        warnings: list[str] = []
        for relative in ("AGENTS.md", "README.md", "agent.yaml"):
            if not (agent_root / relative).exists():
                errors.append(f"missing {relative}")
        for relative in ("capabilities", "knowledge", "templates", "infra"):
            if not (agent_root / relative).is_dir():
                errors.append(f"missing {relative}/")

        manifest = self.read_yaml(agent_root / "agent.yaml") if (agent_root / "agent.yaml").exists() else {}
        declared_capabilities = manifest.get("capabilities") if isinstance(manifest.get("capabilities"), list) else []
        if not declared_capabilities:
            errors.append("agent.yaml capabilities must declare at least one capability")
        if manifest.get("id") and manifest.get("id") != agent_id:
            errors.append("agent.yaml id does not match directory")

        for capability_id in declared_capabilities:
            capability_dir = agent_root / "capabilities" / str(capability_id).split(".")[-1]
            capability_manifest = capability_dir / "capability.yaml"
            if not capability_manifest.exists():
                errors.append(f"missing capability manifest: {capability_id}")
                continue
            for relative in ("workflow.md", "decision-rules.md"):
                if not (capability_dir / relative).exists():
                    errors.append(f"{capability_id} missing {relative}")
            capability = self.read_yaml(capability_manifest)
            if not capability.get("write_policy"):
                errors.append(f"{capability_id} missing write_policy")
            elif str(capability["write_policy"]) not in CANONICAL_WRITE_POLICIES:
                errors.append(f"{capability_id} has unsupported write_policy: {capability['write_policy']}")
            if not capability.get("entrypoint"):
                warnings.append(f"{capability_id} has no executable runner")

        valid = not errors
        return {
            "kind": "agent-builder-validation",
            "status": "ok" if valid else "failed",
            "valid": valid,
            "agent_id": agent_id,
            "errors": errors,
            "warnings": warnings,
        }

    def load_spec(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise AgentBuilderError(f"spec not found: {path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            payload = json.loads(text)
        else:
            payload = yaml.safe_load(text) or {}
        if not isinstance(payload, dict):
            raise AgentBuilderError("spec must be a mapping")
        return payload

    def validate_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        missing = [field for field in REQUIRED_SPEC_FIELDS if not spec.get(field)]
        if missing:
            return {
                "kind": "agent-builder-plan",
                "status": "needs-input",
                "missing_fields": missing,
                "questions": [self.question_for_missing_field(field) for field in missing],
            }
        agent_id = str(spec.get("agent_id") or "").strip()
        if not KEBAB_CASE.match(agent_id):
            return {
                "kind": "agent-builder-plan",
                "status": "blocked",
                "reason": "invalid_agent_id",
                "risks": ["agent_id must be kebab-case and cannot contain path separators."],
            }
        capabilities = spec.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities:
            return {
                "kind": "agent-builder-plan",
                "status": "needs-input",
                "missing_fields": ["capabilities"],
                "questions": [self.question_for_missing_field("capabilities")],
            }
        for item in capabilities:
            if not isinstance(item, dict):
                return {
                    "kind": "agent-builder-plan",
                    "status": "blocked",
                    "reason": "invalid_capability",
                    "risks": ["Each capability must be a mapping."],
                }
            capability_id = str(item.get("id") or "").strip()
            if not KEBAB_CASE.match(capability_id):
                return {
                    "kind": "agent-builder-plan",
                    "status": "blocked",
                    "reason": "invalid_capability_id",
                    "capability": capability_id,
                    "risks": ["Capability ids must be kebab-case."],
                }
            write_policy = str(item.get("write_policy") or "read_only")
            if write_policy not in CANONICAL_WRITE_POLICIES:
                return {
                    "kind": "agent-builder-plan",
                    "status": "blocked",
                    "reason": "invalid_write_policy",
                    "capability": capability_id,
                    "risks": [f"Unsupported write_policy: {write_policy}"],
                }
        return {"status": "ok"}

    def normalize_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(spec)
        normalized["agent_id"] = str(spec["agent_id"]).strip()
        normalized["name"] = str(spec["name"]).strip()
        normalized["purpose"] = " ".join(str(spec["purpose"]).split())
        normalized["domain"] = str(spec["domain"]).strip()
        normalized["providers"] = list(spec.get("providers") or [])
        normalized["risk_profile"] = str(spec.get("risk_profile") or "medium").strip()
        capabilities = []
        for item in spec["capabilities"]:
            capability = dict(item)
            capability["id"] = str(item["id"]).strip()
            capability["name"] = str(item.get("name") or self.title_from_id(capability["id"]))
            capability["purpose"] = " ".join(str(item.get("purpose") or "").split()) or "Executar a capability declarada."
            capability["write_policy"] = str(item.get("write_policy") or "read_only")
            capabilities.append(capability)
        normalized["capabilities"] = capabilities
        return normalized

    def detect_forbidden_content(self, spec: dict[str, Any]) -> dict[str, Any] | None:
        values = list(self.iter_strings(spec))
        for value in values:
            upper = value.upper()
            if any(marker in upper for marker in FORBIDDEN_TEXT_MARKERS):
                return {
                    "kind": "agent-builder-plan",
                    "status": "blocked",
                    "reason": "forbidden_sensitive_marker",
                    "risks": ["Spec contains text that looks like a secret or credential marker."],
                }
            if "http://" in value or "https://" in value:
                return {
                    "kind": "agent-builder-plan",
                    "status": "blocked",
                    "reason": "forbidden_url",
                    "risks": ["Spec contains a URL; move provider endpoints to configuration or a separate decision."],
                }
        return None

    def build_files(self, spec: dict[str, Any]) -> list[tuple[str, str]]:
        agent_id = spec["agent_id"]
        files: list[tuple[str, str]] = [
            (f"agents/{agent_id}/AGENTS.md", self.render_agents_md(spec)),
            (f"agents/{agent_id}/README.md", self.render_readme(spec)),
            (f"agents/{agent_id}/agent.yaml", self.render_agent_yaml(spec)),
            (f"agents/{agent_id}/knowledge/system.md", self.render_system_md(spec)),
            (f"agents/{agent_id}/knowledge/context.md", self.render_context_md(spec)),
            (f"agents/{agent_id}/knowledge/policies.yaml", self.render_policies_yaml(spec)),
            (f"agents/{agent_id}/templates/README.md", "# Templates\n\nModelos de saida das capabilities deste agente.\n"),
            (f"agents/{agent_id}/infra/README.md", "# Infra\n\nRepositories e integracoes externas deste agente.\n"),
        ]
        for capability in spec["capabilities"]:
            capability_id = capability["id"]
            files.extend(
                [
                    (
                        f"agents/{agent_id}/capabilities/{capability_id}/capability.yaml",
                        self.render_capability_yaml(spec, capability),
                    ),
                    (
                        f"agents/{agent_id}/capabilities/{capability_id}/workflow.md",
                        self.render_workflow_md(spec, capability),
                    ),
                    (
                        f"agents/{agent_id}/capabilities/{capability_id}/decision-rules.md",
                        self.render_decision_rules_md(spec, capability),
                    ),
                    (
                        f"agents/{agent_id}/templates/{capability_id}-output.md",
                        self.render_output_template(capability),
                    ),
                ]
            )
        return files

    def render_agent_yaml(self, spec: dict[str, Any]) -> str:
        payload = {
            "id": spec["agent_id"],
            "kind": "specialist-agent",
            "name": spec["name"],
            "version": "0.1.0",
            "status": "draft",
            "owner": "agent-devkit",
            "purpose": spec["purpose"],
            "default_context": [
                "knowledge/system.md",
                "knowledge/context.md",
                "knowledge/policies.yaml",
            ],
            "env": {"required": [], "optional": []},
            "capabilities": [item["id"] for item in spec["capabilities"]],
            "agent_surface": {"policies": ["knowledge/policies.yaml"]},
            "write_policy": {
                "read_operations": "read_only",
                "write_operations": "confirm",
                "external_side_effects": "blocked_by_default",
            },
            "routing": {
                "anchors": [spec["agent_id"], spec["domain"]],
                "intents": [f"{spec['agent_id']}.operate"],
                "priority": 40,
            },
        }
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)

    def render_capability_yaml(self, spec: dict[str, Any], capability: dict[str, Any]) -> str:
        payload = {
            "id": f"{spec['agent_id']}.{capability['id']}",
            "kind": "capability",
            "name": capability["name"],
            "version": "0.1.0",
            "status": "draft",
            "purpose": capability["purpose"],
            "entrypoint": {
                "workflow": "workflow.md",
                "output_template": f"../../templates/{capability['id']}-output.md",
            },
            "inputs": {"required": [], "optional": []},
            "outputs": {"artifacts": [f"{capability['id']}-output.md"]},
            "write_policy": capability["write_policy"],
        }
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)

    def render_agents_md(self, spec: dict[str, Any]) -> str:
        return "\n".join(
            [
                f"# {spec['name']}",
                "",
                f"Instrucoes locais para o agente `{spec['agent_id']}`.",
                "",
                "## Responsabilidade",
                "",
                spec["purpose"],
                "",
                "## Guardrails",
                "",
                "- Manter conhecimento detalhado sob demanda.",
                "- Nao persistir segredos ou contexto de cliente.",
                "- Respeitar write_policy das capabilities.",
                "",
            ]
        )

    def render_readme(self, spec: dict[str, Any]) -> str:
        lines = [
            f"# {spec['name']}",
            "",
            spec["purpose"],
            "",
            "## Capabilities",
            "",
        ]
        for capability in spec["capabilities"]:
            lines.append(f"- `{capability['id']}`: {capability['purpose']}")
        lines.extend(["", "## Dominio", "", spec["domain"], ""])
        return "\n".join(lines)

    def render_system_md(self, spec: dict[str, Any]) -> str:
        return f"# System\n\nVoce e o agente `{spec['agent_id']}`. Atue somente no dominio: {spec['domain']}.\n"

    def render_context_md(self, spec: dict[str, Any]) -> str:
        return f"# Context\n\nPurpose: {spec['purpose']}\n\nRisk profile: {spec.get('risk_profile', 'medium')}.\n"

    def render_policies_yaml(self, spec: dict[str, Any]) -> str:
        payload = {
            "policies": {
                "domain": spec["domain"],
                "risk_profile": spec.get("risk_profile", "medium"),
                "external_writes": "blocked_by_default",
                "secrets": "never_persist",
            }
        }
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)

    def render_workflow_md(self, spec: dict[str, Any], capability: dict[str, Any]) -> str:
        return "\n".join(
            [
                "# Workflow",
                "",
                f"1. Receber entrada para `{capability['id']}`.",
                "2. Validar escopo e write_policy.",
                "3. Executar somente o comportamento declarado.",
                "4. Retornar artefato ou diagnostico estruturado.",
                "",
            ]
        )

    def render_decision_rules_md(self, spec: dict[str, Any], capability: dict[str, Any]) -> str:
        return "\n".join(
            [
                "# Decision Rules",
                "",
                f"- Permanecer no dominio `{spec['domain']}`.",
                f"- Aplicar write_policy `{capability['write_policy']}`.",
                "- Nao inferir dados ausentes como fatos.",
                "- Registrar perguntas pendentes quando faltar contexto.",
                "",
            ]
        )

    def render_output_template(self, capability: dict[str, Any]) -> str:
        return "\n".join(
            [
                f"# {capability['name']} Output",
                "",
                "## Resultado",
                "",
                "-",
                "",
                "## Evidencias",
                "",
                "-",
                "",
                "## Riscos E Lacunas",
                "",
                "-",
                "",
            ]
        )

    def public_file_plan(self, files: list[tuple[str, str]]) -> list[dict[str, Any]]:
        return [
            {
                "path": path,
                "bytes": len(content.encode("utf-8")),
            }
            for path, content in files
        ]

    def agent_summary(self, spec: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": spec["agent_id"],
            "name": spec["name"],
            "domain": spec["domain"],
            "purpose": spec["purpose"],
        }

    def capability_summary(self, capability: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": capability["id"],
            "name": capability["name"],
            "purpose": capability["purpose"],
            "write_policy": capability["write_policy"],
        }

    def open_questions(self, spec: dict[str, Any]) -> list[str]:
        questions: list[str] = []
        if not spec.get("providers"):
            questions.append("Este agente precisa de algum provider ou deve permanecer local/read-only?")
        if spec.get("risk_profile", "medium") != "low":
            questions.append("Quais operacoes exigem confirmacao humana ou review gate?")
        return questions

    def question_for_missing_field(self, field: str) -> str:
        questions = {
            "agent_id": "Qual sera o id kebab-case do agente?",
            "name": "Qual sera o nome publico do agente?",
            "purpose": "Qual problema o agente resolve?",
            "domain": "Qual dominio tecnico ou operacional este agente possui?",
            "capabilities": "Quais capabilities iniciais o agente deve expor?",
        }
        return questions.get(field, f"Informe o campo obrigatorio {field}.")

    def read_yaml(self, path: Path) -> dict[str, Any]:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return payload if isinstance(payload, dict) else {}

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
