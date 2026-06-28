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

import yaml


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
