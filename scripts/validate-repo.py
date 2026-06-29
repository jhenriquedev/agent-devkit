#!/usr/bin/env python3
"""Validate AI DevKit repository structure without calling external systems."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import yaml

from cli.aikit.write_policy import canonical_write_policies, legacy_write_policy_aliases


KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
AGENT_REQUIRED_KEYS = {
    "id",
    "kind",
    "name",
    "version",
    "status",
    "owner",
    "purpose",
    "default_context",
    "capabilities",
}
CAPABILITY_REQUIRED_KEYS = {
    "id",
    "kind",
    "name",
    "version",
    "status",
    "purpose",
    "entrypoint",
    "inputs",
    "outputs",
    "write_policy",
}
ALLOWED_STATUSES = {"draft", "mvp", "validated", "operational", "deprecated"}
PROVIDER_ALLOWED_STATUSES = {"draft", "active", "deprecated"}
PROVIDER_REQUIRED_KEYS = {
    "id",
    "name",
    "kind",
    "status",
    "description",
    "auth_methods",
    "config_fields",
    "capabilities",
    "health_check",
    "risk",
    "fallbacks",
}
PLUGIN_REQUIRED_KEYS = {
    "id",
    "name",
    "version",
    "description",
    "runtime",
    "scripts",
    "skills",
}
CAPABILITY_PROVIDER_MODES = {"required", "optional", "required_for_execute", "delegated"}
CAPABILITY_PROVIDER_FALLBACKS = {
    "plan_only",
    "dry_run",
    "manual_steps",
    "use_user_supplied_context",
    "skip_provider",
    "blocked",
}
CAPABILITY_EXECUTION_FIELDS = {"modes", "idempotency", "timeout_seconds"}
CAPABILITY_EXECUTION_MODES = {"run", "dry-run"}
CAPABILITY_IDEMPOTENCY_VALUES = {
    "safe-repeat",
    "creates-artifact",
    "external-read",
    "external-write",
}
CAPABILITY_ARTIFACT_KINDS = {"markdown", "json", "xlsx", "pptx", "drawio", "log", "other"}
RUNTIME_SOURCE_FIELDS = {"enabled", "args", "env"}
SOURCE_CONTRACT_FIELDS = {"enabled", "supported", "args", "env", "mappings", "apply"}
SOURCE_MAPPING_FIELDS = {"field", "name", "arg", "env"}
RUNTIME_ROLE_KINDS = {"coordinator", "reviewer", "provider-configurator", "local-worker", "none"}
AGENT_MODE_TYPES = {"reactive", "workflow", "planner", "reviewer"}
AGENT_MODE_LLM_VALUES = {False, "optional", "required"}
AGENT_MODE_FIELDS = {
    "type",
    "max_steps",
    "max_specialists",
    "max_llm_calls",
    "timeout_seconds",
    "can_call_capabilities",
    "can_call_llm",
    "can_request_user_input",
    "external_writes",
    "allowed_capabilities",
    "stop_conditions",
}
CANONICAL_WRITE_POLICIES = canonical_write_policies()
LEGACY_WRITE_POLICY_ALIASES = legacy_write_policy_aliases()
SECRET_MARKERS = ("SECRET", "TOKEN", "PASSWORD", "PAT", "API_KEY", "PRIVATE_KEY")
ROOT_ARTIFACT_NAMES = {"json", "markdown"}
ROOT_IGNORED_NAMES = {
    ".git",
    ".github",
    ".DS_Store",
    ".env",
    ".env.example",
    ".gitignore",
    ".playwright-mcp",
    "__pycache__",
    "AGENTS.md",
    "LICENSE",
    "README.md",
    "RELEASE_NOTES.md",
    "agent",
    "agents",
    "ai-devkit",
    "aikit",
    "cli",
    "docs",
    "package-lock.json",
    "package.json",
    "requirements.txt",
    "providers",
    "plugins",
    "scripts",
    "tests",
    "tooling",
    "vendor",
}


@dataclass
class ValidationState:
    root: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    agents: int = 0
    capabilities: int = 0
    declared_runners: int = 0
    missing_decision_rules: int = 0
    providers: int = 0
    plugins: int = 0
    provider_ids: set[str] = field(default_factory=set)
    plugin_stats: dict[str, dict[str, Any]] = field(default_factory=dict)
    agent_stats: dict[str, dict[str, int]] = field(default_factory=dict)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def payload(self) -> dict[str, Any]:
        return {
            "summary": {
                "agents": self.agents,
                "capabilities": self.capabilities,
                "declared_runners": self.declared_runners,
                "missing_decision_rules": self.missing_decision_rules,
                "providers": self.providers,
                "plugins": self.plugins,
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "agents": self.agent_stats,
            "providers": sorted(self.provider_ids),
            "plugins": self.plugin_stats,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AI DevKit repository structure.")
    parser.add_argument("--root", default=".", help="repository root to validate")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as failing conditions",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    state = validate_repo(root)
    failing = bool(state.errors or (args.strict and state.warnings))

    if args.json:
        print(json.dumps(state.payload(), ensure_ascii=False, indent=2))
    else:
        print_human(state, strict=args.strict)

    return 1 if failing else 0


def validate_repo(root: Path) -> ValidationState:
    state = ValidationState(root=root)
    if not root.exists():
        state.error(f"root does not exist: {root}")
        return state

    validate_root_hygiene(state)
    validate_providers(state)
    validate_plugins(state)
    agents = validate_agents(state)
    validate_docs_cover_agents(state, agents)
    return state


def validate_root_hygiene(state: ValidationState) -> None:
    for name in sorted(ROOT_ARTIFACT_NAMES):
        path = state.root / name
        if path.exists() and path.is_file():
            state.warn(f"root contains generated-looking artifact: {name}")

    for path in sorted(state.root.iterdir()):
        if path.name in ROOT_IGNORED_NAMES:
            continue
        if path.name in ROOT_ARTIFACT_NAMES:
            continue
        if path.name.startswith("."):
            continue
        if path.is_file():
            state.warn(f"root contains unexpected file: {path.name}")


def validate_agents(state: ValidationState) -> list[str]:
    agents_dir = state.root / "agents"
    if not agents_dir.exists():
        state.error("missing agents directory")
        return []
    if not agents_dir.is_dir():
        state.error("agents exists but is not a directory")
        return []

    agent_ids: list[str] = []
    for agent_dir in sorted(path for path in agents_dir.iterdir() if path.is_dir()):
        manifest_path = agent_dir / "agent.yaml"
        if not manifest_path.exists():
            continue
        state.agents += 1
        agent_ids.append(agent_dir.name)
        validate_agent(state, agent_dir, manifest_path)
    return agent_ids


def validate_providers(state: ValidationState) -> None:
    providers_dir = state.root / "providers"
    if not providers_dir.exists():
        state.warn("missing providers directory")
        return
    if not providers_dir.is_dir():
        state.error("providers exists but is not a directory")
        return

    for manifest_path in sorted(providers_dir.glob("*.yaml")):
        state.providers += 1
        relative_manifest = rel(state, manifest_path)
        if not KEBAB_CASE.match(manifest_path.stem):
            state.error(f"{relative_manifest} filename is not kebab-case")

        manifest = load_yaml(state, manifest_path)
        if not isinstance(manifest, dict):
            continue

        missing_keys = sorted(PROVIDER_REQUIRED_KEYS - set(manifest))
        for key in missing_keys:
            state.error(f"{relative_manifest} missing required key: {key}")

        if manifest.get("id") != manifest_path.stem:
            state.error(
                f"{relative_manifest} id {manifest.get('id')!r} does not match filename {manifest_path.name!r}"
            )
        elif manifest.get("id"):
            state.provider_ids.add(str(manifest["id"]))

        status = manifest.get("status")
        if status and str(status) not in PROVIDER_ALLOWED_STATUSES:
            state.error(f"{relative_manifest} has unsupported provider status: {status}")

        auth_methods = manifest.get("auth_methods", [])
        if not isinstance(auth_methods, list):
            state.error(f"{relative_manifest} auth_methods must be a list")
        else:
            for method in auth_methods:
                if not isinstance(method, dict):
                    state.error(f"{relative_manifest} auth_methods entries must be mappings")
                    continue
                secret_fields = method.get("secret_fields", [])
                if secret_fields is None:
                    continue
                if not isinstance(secret_fields, list):
                    state.error(f"{relative_manifest} auth method {method.get('id')} secret_fields must be a list")

        config_fields = manifest.get("config_fields", [])
        if not isinstance(config_fields, list):
            state.error(f"{relative_manifest} config_fields must be a list")
        else:
            validate_provider_config_fields(state, manifest_path, config_fields)

        fallbacks = manifest.get("fallbacks", [])
        if not isinstance(fallbacks, list) or not fallbacks:
            state.error(f"{relative_manifest} fallbacks must be a non-empty list")


def validate_provider_config_fields(state: ValidationState, manifest_path: Path, fields: list[Any]) -> None:
    relative_manifest = rel(state, manifest_path)
    for field in fields:
        if not isinstance(field, dict):
            state.error(f"{relative_manifest} config_fields entries must be mappings")
            continue
        name = field.get("name")
        if not name:
            state.error(f"{relative_manifest} config field missing name")
            continue
        if "secret" not in field:
            state.error(f"{relative_manifest} config field {name} missing secret marker")
        if looks_secret(str(name)) and field.get("secret") is not True:
            state.error(f"{relative_manifest} config field {name} looks secret but is not marked secret: true")


def validate_plugins(state: ValidationState) -> None:
    plugins_dir = state.root / "plugins"
    if not plugins_dir.exists():
        return
    if not plugins_dir.is_dir():
        state.error("plugins exists but is not a directory")
        return

    for plugin_dir in sorted(path for path in plugins_dir.iterdir() if path.is_dir()):
        state.plugins += 1
        manifest_path = plugin_manifest_path(plugin_dir)
        relative_dir = rel(state, plugin_dir)
        if not KEBAB_CASE.match(plugin_dir.name):
            state.error(f"{relative_dir} is not kebab-case")
        if not manifest_path.exists():
            state.error(f"{relative_dir} missing plugin manifest")
            continue

        manifest = load_json(state, manifest_path)
        if not isinstance(manifest, dict):
            continue

        relative_manifest = rel(state, manifest_path)
        missing_keys = sorted(PLUGIN_REQUIRED_KEYS - set(manifest))
        for key in missing_keys:
            state.error(f"{relative_manifest} missing required key: {key}")

        plugin_id = str(manifest.get("id") or "")
        if plugin_id and plugin_id != plugin_dir.name:
            state.error(f"{relative_manifest} id {plugin_id!r} does not match directory {plugin_dir.name!r}")

        runtime = manifest.get("runtime", {})
        if not isinstance(runtime, dict):
            state.error(f"{relative_manifest} runtime must be a mapping")
        elif runtime.get("command") not in {"agent", "aikit"}:
            state.error(f"{relative_manifest} runtime.command must be agent or aikit")

        skills = manifest.get("skills", [])
        if not isinstance(skills, list) or not skills:
            state.error(f"{relative_manifest} skills must be a non-empty list")
        else:
            validate_plugin_path_entries(state, plugin_dir, relative_manifest, skills, "skills")

        scripts = manifest.get("scripts", {})
        if scripts:
            if not isinstance(scripts, dict):
                state.error(f"{relative_manifest} scripts must be a mapping")
            else:
                validate_plugin_named_paths(state, plugin_dir, relative_manifest, scripts, "scripts")

        commands = manifest.get("commands", [])
        if commands:
            if not isinstance(commands, list):
                state.error(f"{relative_manifest} commands must be a list")
            else:
                validate_plugin_path_entries(state, plugin_dir, relative_manifest, commands, "commands")

        state.plugin_stats[plugin_dir.name] = {
            "manifest": rel(state, manifest_path),
            "skills": len(skills) if isinstance(skills, list) else 0,
            "commands": len(commands) if isinstance(commands, list) else 0,
            "scripts": len(scripts) if isinstance(scripts, dict) else 0,
        }


def plugin_manifest_path(plugin_dir: Path) -> Path:
    codex_manifest = plugin_dir / ".codex-plugin" / "plugin.json"
    if codex_manifest.exists():
        return codex_manifest
    return plugin_dir / "plugin.json"


def validate_plugin_path_entries(
    state: ValidationState,
    plugin_dir: Path,
    relative_manifest: str,
    entries: list[Any],
    field: str,
) -> None:
    for entry in entries:
        if not isinstance(entry, dict):
            state.error(f"{relative_manifest} {field} entries must be mappings")
            continue
        path = entry.get("path")
        if not isinstance(path, str) or not path:
            state.error(f"{relative_manifest} {field} entry missing path")
            continue
        validate_plugin_relative_path(state, plugin_dir, relative_manifest, path, field)


def validate_plugin_named_paths(
    state: ValidationState,
    plugin_dir: Path,
    relative_manifest: str,
    paths: dict[str, Any],
    field: str,
) -> None:
    for name, path in paths.items():
        if not isinstance(path, str) or not path:
            state.error(f"{relative_manifest} {field}.{name} must be a path string")
            continue
        validate_plugin_relative_path(state, plugin_dir, relative_manifest, path, f"{field}.{name}")


def validate_plugin_relative_path(
    state: ValidationState,
    plugin_dir: Path,
    relative_manifest: str,
    path: str,
    field: str,
) -> None:
    target = (plugin_dir / path).resolve()
    if not is_inside(plugin_dir.resolve(), target) or not target.exists():
        state.error(f"{relative_manifest} {field} missing ref: {path}")


def validate_agent(state: ValidationState, agent_dir: Path, manifest_path: Path) -> None:
    relative_dir = rel(state, agent_dir)
    if not KEBAB_CASE.match(agent_dir.name):
        state.error(f"{relative_dir} is not kebab-case")

    for filename in ("AGENTS.md", "README.md"):
        if not (agent_dir / filename).exists():
            state.error(f"{relative_dir} missing {filename}")

    for dirname in ("capabilities", "knowledge", "templates", "infra"):
        if not (agent_dir / dirname).is_dir():
            state.error(f"{relative_dir} missing {dirname}/")

    manifest = load_yaml(state, manifest_path)
    if not isinstance(manifest, dict):
        return

    missing_keys = sorted(AGENT_REQUIRED_KEYS - set(manifest))
    for key in missing_keys:
        state.error(f"{rel(state, manifest_path)} missing required key: {key}")

    if manifest.get("id") != agent_dir.name:
        state.error(
            f"{rel(state, manifest_path)} id {manifest.get('id')!r} does not match directory {agent_dir.name!r}"
        )
    state.agent_stats.setdefault(
        agent_dir.name,
        {"capabilities": 0, "declared_runners": 0, "missing_decision_rules": 0},
    )

    validate_status(state, manifest_path, manifest.get("status"))
    validate_relative_refs(state, agent_dir, manifest.get("default_context", []), "default_context")
    validate_agent_write_policy(state, manifest_path, manifest.get("write_policy"))
    validate_routing(state, manifest_path, manifest.get("routing"))
    validate_runtime_role(state, manifest_path, manifest.get("runtime_role"), agent_kind=manifest.get("kind"))
    validate_agent_mode(state, manifest_path, manifest.get("agent_mode"), write_policy=manifest.get("write_policy"))

    surface = manifest.get("agent_surface", {}) or {}
    if isinstance(surface, dict):
        for key in ("repositories", "methods", "policies", "skills_catalog"):
            validate_relative_refs(state, agent_dir, surface.get(key, []), f"agent_surface.{key}")

    declared_capabilities = manifest.get("capabilities", [])
    if isinstance(declared_capabilities, list):
        declared = sorted(str(item).split(".")[-1] for item in declared_capabilities)
    else:
        state.error(f"{rel(state, manifest_path)} capabilities must be a list")
        declared = []

    capabilities_dir = agent_dir / "capabilities"
    on_disk: list[str] = []
    if capabilities_dir.exists():
        for capability_manifest in sorted(capabilities_dir.glob("*/capability.yaml")):
            on_disk.append(capability_manifest.parent.name)
            validate_capability(state, agent_dir, capability_manifest)

    for capability in sorted(set(on_disk) - set(declared)):
        state.error(f"{relative_dir} capability exists on disk but is not declared: {capability}")
    for capability in sorted(set(declared) - set(on_disk)):
        state.error(f"{relative_dir} declares missing capability: {capability}")


def validate_capability(state: ValidationState, agent_dir: Path, manifest_path: Path) -> None:
    state.capabilities += 1
    agent_stats = state.agent_stats.setdefault(
        agent_dir.name,
        {"capabilities": 0, "declared_runners": 0, "missing_decision_rules": 0},
    )
    agent_stats["capabilities"] += 1
    capability_dir = manifest_path.parent
    relative_manifest = rel(state, manifest_path)

    if not KEBAB_CASE.match(capability_dir.name):
        state.error(f"{rel(state, capability_dir)} is not kebab-case")
    if not (capability_dir / "workflow.md").exists():
        state.error(f"{rel(state, capability_dir)} missing workflow.md")
    if not (capability_dir / "decision-rules.md").exists():
        state.missing_decision_rules += 1
        agent_stats["missing_decision_rules"] += 1

    manifest = load_yaml(state, manifest_path)
    if not isinstance(manifest, dict):
        return

    missing_keys = sorted(CAPABILITY_REQUIRED_KEYS - set(manifest))
    for key in missing_keys:
        state.error(f"{relative_manifest} missing required key: {key}")

    manifest_id = str(manifest.get("id", ""))
    if manifest_id.split(".")[-1] != capability_dir.name:
        state.error(
            f"{relative_manifest} id {manifest.get('id')!r} does not match directory {capability_dir.name!r}"
        )

    validate_status(state, manifest_path, manifest.get("status"))
    validate_write_policy_value(state, manifest_path, manifest.get("write_policy"))
    validate_routing(state, manifest_path, manifest.get("routing"))
    validate_runtime_contract(state, manifest_path, manifest.get("runtime"))
    validate_source_contract(state, manifest_path, manifest.get("source"), field_prefix="source")
    validate_capability_execution(state, manifest_path, manifest.get("execution"))
    validate_capability_outputs(state, manifest_path, manifest.get("outputs"))

    entrypoint = manifest.get("entrypoint", {}) or {}
    if isinstance(entrypoint, dict):
        runner = entrypoint.get("runner")
        if runner:
            state.declared_runners += 1
            agent_stats["declared_runners"] += 1
            runner_path = (capability_dir / str(runner)).resolve()
            if not is_inside(state.root, runner_path) or not runner_path.exists():
                state.error(f"{relative_manifest} declares missing runner {runner}")
        for key, value in entrypoint.items():
            if key == "runner":
                continue
            if isinstance(value, str):
                validate_relative_refs(state, capability_dir, [value], f"entrypoint.{key}")

    integration = manifest.get("integration", {}) or {}
    if isinstance(integration, dict):
        repository = integration.get("repository")
        if repository:
            validate_relative_refs(state, capability_dir, [repository], "integration.repository")
        validate_relative_refs(state, capability_dir, integration.get("methods", []), "integration.methods")

    validate_capability_provider_requirements(state, manifest_path, manifest.get("requires", {}))


def validate_capability_execution(state: ValidationState, manifest_path: Path, execution: Any) -> None:
    if execution is None:
        return
    relative_manifest = rel(state, manifest_path)
    if not isinstance(execution, dict):
        state.error(f"{relative_manifest} execution must be a mapping")
        return
    for key in execution:
        if key not in CAPABILITY_EXECUTION_FIELDS:
            state.error(f"{relative_manifest} execution has unsupported field: {key}")
    modes = execution.get("modes")
    if modes is not None:
        if not isinstance(modes, list):
            state.error(f"{relative_manifest} execution.modes must be a list")
        else:
            for mode in modes:
                if mode not in CAPABILITY_EXECUTION_MODES:
                    state.error(f"{relative_manifest} execution.modes has unsupported mode: {mode}")
    idempotency = execution.get("idempotency")
    if idempotency is not None and idempotency not in CAPABILITY_IDEMPOTENCY_VALUES:
        state.error(f"{relative_manifest} execution.idempotency has unsupported value: {idempotency}")
    timeout = execution.get("timeout_seconds")
    if timeout is not None and (not isinstance(timeout, int) or timeout <= 0):
        state.error(f"{relative_manifest} execution.timeout_seconds must be a positive integer")


def validate_capability_outputs(state: ValidationState, manifest_path: Path, outputs: Any) -> None:
    if outputs is None:
        return
    relative_manifest = rel(state, manifest_path)
    if not isinstance(outputs, dict):
        state.error(f"{relative_manifest} outputs must be a mapping")
        return
    artifacts = outputs.get("artifacts")
    if artifacts is None:
        return
    if not isinstance(artifacts, list):
        state.error(f"{relative_manifest} outputs.artifacts must be a list")
        return
    for item in artifacts:
        if isinstance(item, str):
            continue
        if not isinstance(item, dict):
            state.error(f"{relative_manifest} outputs.artifacts entries must be strings or mappings")
            continue
        path = item.get("path") or item.get("ref")
        if not isinstance(path, str) or not path.strip():
            state.error(f"{relative_manifest} outputs.artifacts entry missing path")
        kind = item.get("kind")
        if kind is not None and kind not in CAPABILITY_ARTIFACT_KINDS:
            state.error(f"{relative_manifest} outputs.artifacts has unsupported kind: {kind}")
        sensitive = item.get("sensitive")
        if sensitive is not None and not isinstance(sensitive, bool):
            state.error(f"{relative_manifest} outputs.artifacts sensitive must be boolean")


def validate_runtime_contract(state: ValidationState, manifest_path: Path, runtime: Any) -> None:
    if runtime is None:
        return
    relative_manifest = rel(state, manifest_path)
    if not isinstance(runtime, dict):
        state.error(f"{relative_manifest} runtime must be a mapping")
        return
    provider = runtime.get("provider")
    if provider is not None:
        provider_id = str(provider)
        if not provider_id:
            state.error(f"{relative_manifest} runtime.provider must be a non-empty string")
        elif provider_id not in state.provider_ids:
            state.error(f"{relative_manifest} runtime references unknown provider: {provider_id}")
    source = runtime.get("source")
    if source is None:
        return
    validate_source_contract(state, manifest_path, source, field_prefix="runtime.source", allowed_fields=RUNTIME_SOURCE_FIELDS)


def validate_source_contract(
    state: ValidationState,
    manifest_path: Path,
    source: Any,
    *,
    field_prefix: str,
    allowed_fields: set[str] = SOURCE_CONTRACT_FIELDS,
) -> None:
    if source is None:
        return
    if not isinstance(source, dict):
        state.error(f"{rel(state, manifest_path)} {field_prefix} must be a mapping")
        return
    relative_manifest = rel(state, manifest_path)
    for key in source:
        if key not in allowed_fields:
            state.error(f"{relative_manifest} {field_prefix} has unsupported field: {key}")
    for boolean_field in ("enabled", "supported"):
        if boolean_field in source and not isinstance(source.get(boolean_field), bool):
            state.error(f"{relative_manifest} {field_prefix}.{boolean_field} must be boolean")
    for field in ("args", "env"):
        mapping = source.get(field)
        if mapping is None:
            continue
        if not isinstance(mapping, dict):
            state.error(f"{relative_manifest} {field_prefix}.{field} must be a mapping")
            continue
        for name, value in mapping.items():
            if not isinstance(name, str) or not name.strip() or not isinstance(value, str) or not value.strip():
                state.error(f"{relative_manifest} {field_prefix}.{field} entries must be non-empty strings")
                continue
            if field == "args" and not value.startswith("--"):
                state.error(f"{relative_manifest} {field_prefix}.args.{name} must map to a CLI flag")
            if field == "env" and not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", value):
                state.error(f"{relative_manifest} {field_prefix}.env.{name} must map to an environment variable")
    for list_field in ("mappings", "apply"):
        mappings = source.get(list_field)
        if mappings is None:
            continue
        if not isinstance(mappings, list):
            state.error(f"{relative_manifest} {field_prefix}.{list_field} must be a list")
            continue
        for index, item in enumerate(mappings):
            item_prefix = f"{field_prefix}.{list_field}[{index}]"
            if not isinstance(item, dict):
                state.error(f"{relative_manifest} {item_prefix} entries must be mappings")
                continue
            for key in item:
                if key not in SOURCE_MAPPING_FIELDS:
                    state.error(f"{relative_manifest} {item_prefix} has unsupported field: {key}")
            field_name = item.get("field") or item.get("name")
            if not isinstance(field_name, str) or not field_name.strip():
                state.error(f"{relative_manifest} {item_prefix} missing field")
            arg = item.get("arg")
            if arg is not None and (not isinstance(arg, str) or not arg.startswith("--")):
                state.error(f"{relative_manifest} {item_prefix}.arg must map to a CLI flag")
            env = item.get("env")
            if env is not None and (not isinstance(env, str) or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", env)):
                state.error(f"{relative_manifest} {item_prefix}.env must map to an environment variable")


def validate_runtime_role(state: ValidationState, manifest_path: Path, runtime_role: Any, *, agent_kind: Any) -> None:
    relative_manifest = rel(state, manifest_path)
    if agent_kind == "runtime-agent" and runtime_role is None:
        state.error(f"{relative_manifest} runtime-agent must declare runtime_role")
        return
    if runtime_role is None:
        return
    if not isinstance(runtime_role, dict):
        state.error(f"{relative_manifest} runtime_role must be a mapping")
        return
    role_kind = str(runtime_role.get("kind") or "")
    if not role_kind:
        state.error(f"{relative_manifest} runtime_role.kind must be a non-empty string")
    elif role_kind not in RUNTIME_ROLE_KINDS:
        state.error(f"{relative_manifest} runtime_role.kind has unsupported value: {role_kind}")


def validate_agent_mode(state: ValidationState, manifest_path: Path, agent_mode: Any, *, write_policy: Any) -> None:
    if agent_mode is None:
        return
    relative_manifest = rel(state, manifest_path)
    if not isinstance(agent_mode, dict):
        state.error(f"{relative_manifest} agent_mode must be a mapping")
        return
    for key in agent_mode:
        if key not in AGENT_MODE_FIELDS:
            state.error(f"{relative_manifest} agent_mode has unsupported field: {key}")
    mode_type = str(agent_mode.get("type") or "")
    if not mode_type:
        state.error(f"{relative_manifest} agent_mode.type must be a non-empty string")
    elif mode_type not in AGENT_MODE_TYPES:
        state.error(f"{relative_manifest} agent_mode.type has unsupported value: {mode_type}")
    max_steps = agent_mode.get("max_steps")
    if not isinstance(max_steps, int) or max_steps <= 0 or max_steps > 20:
        state.error(f"{relative_manifest} agent_mode.max_steps must be an integer between 1 and 20")
    max_specialists = agent_mode.get("max_specialists")
    if max_specialists is not None and (not isinstance(max_specialists, int) or max_specialists <= 0 or max_specialists > 20):
        state.error(f"{relative_manifest} agent_mode.max_specialists must be an integer between 1 and 20")
    max_llm_calls = agent_mode.get("max_llm_calls")
    if max_llm_calls is not None and (not isinstance(max_llm_calls, int) or max_llm_calls < 0 or max_llm_calls > 20):
        state.error(f"{relative_manifest} agent_mode.max_llm_calls must be an integer between 0 and 20")
    timeout = agent_mode.get("timeout_seconds")
    if timeout is not None and (not isinstance(timeout, int) or timeout <= 0):
        state.error(f"{relative_manifest} agent_mode.timeout_seconds must be a positive integer")
    for boolean_field in ("can_call_capabilities", "can_request_user_input", "external_writes"):
        if boolean_field in agent_mode and not isinstance(agent_mode.get(boolean_field), bool):
            state.error(f"{relative_manifest} agent_mode.{boolean_field} must be boolean")
    llm_value = agent_mode.get("can_call_llm")
    if llm_value not in AGENT_MODE_LLM_VALUES:
        state.error(f"{relative_manifest} agent_mode.can_call_llm must be false, optional, or required")
    for list_field in ("allowed_capabilities", "stop_conditions"):
        values = agent_mode.get(list_field)
        if values is None:
            continue
        if not isinstance(values, list):
            state.error(f"{relative_manifest} agent_mode.{list_field} must be a list")
            continue
        for item in values:
            if not isinstance(item, str) or not item.strip():
                state.error(f"{relative_manifest} agent_mode.{list_field} entries must be non-empty strings")
    if agent_mode.get("external_writes") is True and not agent_write_policy_requires_confirmation(write_policy):
        state.error(f"{relative_manifest} agent_mode.external_writes=true requires confirm, delegated, or blocked_by_default write_policy")


def agent_write_policy_requires_confirmation(write_policy: Any) -> bool:
    if isinstance(write_policy, dict):
        values = [normalize_write_policy_value(policy) for policy in write_policy.values()]
    else:
        values = [normalize_write_policy_value(write_policy)]
    return any(value in {"confirm", "delegated", "blocked_by_default"} for value in values)


def normalize_write_policy_value(value: Any) -> str:
    raw = str(value or "").strip()
    return LEGACY_WRITE_POLICY_ALIASES.get(raw, raw)


def validate_capability_provider_requirements(state: ValidationState, manifest_path: Path, requires: Any) -> None:
    if not requires:
        return
    relative_manifest = rel(state, manifest_path)
    if not isinstance(requires, dict):
        state.error(f"{relative_manifest} requires must be a mapping")
        return
    providers = requires.get("providers", [])
    if not providers:
        return
    if not isinstance(providers, list):
        state.error(f"{relative_manifest} requires.providers must be a list")
        return
    for item in providers:
        if not isinstance(item, dict):
            state.error(f"{relative_manifest} requires.providers entries must be mappings")
            continue
        provider_id = str(item.get("id") or "")
        if not provider_id:
            state.error(f"{relative_manifest} requires provider entry missing id")
            continue
        if provider_id not in state.provider_ids:
            state.error(f"{relative_manifest} requires unknown provider: {provider_id}")

        mode = str(item.get("mode") or "")
        if mode and mode not in CAPABILITY_PROVIDER_MODES:
            state.error(f"{relative_manifest} provider {provider_id} has unsupported mode: {mode}")

        fallback = str(item.get("fallback") or "")
        if fallback and fallback not in CAPABILITY_PROVIDER_FALLBACKS:
            state.error(f"{relative_manifest} provider {provider_id} has unsupported fallback: {fallback}")


def validate_docs_cover_agents(state: ValidationState, agent_ids: list[str]) -> None:
    docs = [state.root / "README.md", state.root / "agents" / "README.md"]
    for doc in docs:
        if not doc.exists():
            state.error(f"missing documentation file: {rel(state, doc)}")
            continue
        text = doc.read_text(encoding="utf-8")
        for agent_id in agent_ids:
            if agent_id not in text:
                state.error(f"{rel(state, doc)} does not mention agent {agent_id}")


def validate_status(state: ValidationState, path: Path, status: Any) -> None:
    if status is None:
        return
    if str(status) not in ALLOWED_STATUSES:
        state.error(f"{rel(state, path)} has unsupported status: {status}")


def validate_agent_write_policy(state: ValidationState, path: Path, write_policy: Any) -> None:
    if write_policy is None:
        return
    if isinstance(write_policy, dict):
        for name, value in sorted(write_policy.items()):
            validate_write_policy_value(state, path, value, field=f"write_policy.{name}")
        return
    validate_write_policy_value(state, path, write_policy)


def validate_write_policy_value(
    state: ValidationState,
    path: Path,
    write_policy: Any,
    *,
    field: str = "write_policy",
) -> None:
    if write_policy is None:
        return
    policy = str(write_policy)
    if policy in CANONICAL_WRITE_POLICIES:
        return
    if policy in LEGACY_WRITE_POLICY_ALIASES:
        state.warn(
            f"{rel(state, path)} uses legacy {field}: {policy!r}; use {LEGACY_WRITE_POLICY_ALIASES[policy]!r}"
        )
        return
    state.error(f"{rel(state, path)} has unsupported {field}: {policy!r}")


def validate_routing(state: ValidationState, path: Path, routing: Any) -> None:
    if routing is None:
        return
    relative = rel(state, path)
    if not isinstance(routing, dict):
        state.error(f"{relative} routing must be a mapping")
        return
    for field in ("aliases", "anchors", "domains", "entities", "intents", "keywords", "examples"):
        value = routing.get(field)
        if value is None:
            continue
        if not isinstance(value, list):
            state.error(f"{relative} routing.{field} must be a list")
            continue
        for item in value:
            if not isinstance(item, str) or not item.strip():
                state.error(f"{relative} routing.{field} entries must be non-empty strings")
    if "priority" in routing and not isinstance(routing.get("priority"), int):
        state.error(f"{relative} routing.priority must be an integer")


def validate_relative_refs(state: ValidationState, base: Path, refs: Any, field: str) -> None:
    if refs is None:
        return
    if isinstance(refs, str):
        refs = [refs]
    if not isinstance(refs, list):
        state.error(f"{rel(state, base)} {field} must be a list or string")
        return
    for ref in refs:
        if not isinstance(ref, str):
            state.error(f"{rel(state, base)} {field} contains non-string ref: {ref!r}")
            continue
        ref_path = (base / ref).resolve()
        if not is_inside(state.root, ref_path) or not ref_path.exists():
            state.error(f"{rel(state, base)} {field} missing ref: {ref}")


def load_yaml(state: ValidationState, path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001 - validator should report malformed files.
        state.error(f"{rel(state, path)} is not valid YAML: {exc}")
        return None


def load_json(state: ValidationState, path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - validator should report malformed files.
        state.error(f"{rel(state, path)} is not valid JSON: {exc}")
        return None


def is_inside(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def looks_secret(name: str) -> bool:
    upper = name.upper()
    return any(marker in upper for marker in SECRET_MARKERS)


def rel(state: ValidationState, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(state.root))
    except ValueError:
        return str(path)


def print_human(state: ValidationState, strict: bool) -> None:
    print("AI DevKit repository validation")
    print(f"- Agents: {state.agents}")
    print(f"- Capabilities: {state.capabilities}")
    print(f"- Declared runners: {state.declared_runners}")
    print(f"- Missing decision-rules.md: {state.missing_decision_rules}")

    if state.errors:
        print("\nErrors:")
        for error in state.errors:
            print(f"- {error}")
    if state.warnings:
        print("\nWarnings:")
        for warning in state.warnings:
            print(f"- {warning}")
    if strict and state.warnings:
        print("\nStrict mode treats warnings as failures.")

    if not state.errors and not (strict and state.warnings):
        print("\nValidation passed.")


if __name__ == "__main__":
    raise SystemExit(main())
