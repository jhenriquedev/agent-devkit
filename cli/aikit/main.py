#!/usr/bin/env python3
"""AI DevKit public command line interface."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from cli.aikit import __version__
from cli.aikit.diagnostics import build_diagnostics
from cli.aikit.fallback import evaluate_provider_requirements
from cli.aikit.guardrails import evaluate_execution_guardrails
from cli.aikit.llm import (
    configure_backend,
    doctor_backends,
    invoke_agent_prompt,
    list_backends,
    resolve_backend,
    set_default_backend,
)
from cli.aikit.memory import record_usage, reset_memory, show_memory, napkin_context
from cli.aikit.install import InstallError, install_runtime
from cli.aikit.lock import lock_status, parse_profiles
from cli.aikit.output import run_payload
from cli.aikit.credentials import CredentialResolverError, credential_backends
from cli.aikit.providers import (
    ProviderRegistryError,
    configure_provider,
    credential_resolution,
    list_providers,
    provider_status_with_credentials,
    unset_provider_config,
)
from cli.aikit.router import route_prompt
from cli.aikit.sources import (
    SourceRegistryError,
    add_source,
    apply_source_to_args,
    extract_source_arg,
    list_sources,
    public_source,
    remove_source,
    resolve_source,
    source_env,
    source_status,
)


DEFAULT_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(os.environ.get("AI_DEVKIT_ROOT", DEFAULT_ROOT)).resolve()
AGENTS_DIR = ROOT / "agents"

DETERMINISTIC_COMMANDS = (
    "agents",
    "capabilities",
    "inspect",
    "run",
    "doctor",
    "commands",
    "llm",
    "providers",
    "provider",
    "credential",
    "source",
    "memory",
    "install",
)
LLM_COMMANDS = ("agent",)


class DevKitError(RuntimeError):
    """Raised for user-facing CLI errors."""


def main(argv: list[str] | None = None, *, prog: str | None = None) -> int:
    parser = build_parser(prog=prog)
    args = parser.parse_args(argv)
    args.prog_name = prog or "aikit"

    try:
        result = dispatch(args)
    except DevKitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if result is None:
        return 0

    if getattr(args, "json", False):
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
    if "exit_code" in result:
        return int(result["exit_code"])
    if result.get("kind") == "doctor" and result.get("errors"):
        return 1
    return 0


def build_parser(prog: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog or "aikit",
        description="AI DevKit CLI",
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("-v", "--version", action="store_true", help="print CLI version and exit")

    subparsers = parser.add_subparsers(dest="command")

    agent_parser = subparsers.add_parser(
        "agent",
        help="handle a natural-language task using an LLM backend",
    )
    agent_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    agent_parser.add_argument("--llm", help="LLM backend id to use")
    agent_parser.add_argument("prompt", nargs=argparse.REMAINDER)

    commands_parser = subparsers.add_parser("commands", help="list CLI command modes")
    commands_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    commands_parser.add_argument("action", nargs="?", default="list", choices=["list"])

    providers_parser = subparsers.add_parser("providers", help="list provider registry entries")
    providers_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    providers_parser.add_argument("action", nargs="?", default="list", choices=["list"])

    provider_parser = subparsers.add_parser("provider", help="inspect or configure one provider")
    provider_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    provider_parser.add_argument("--env-file", action="append", default=[], help="credential env/JSON/YAML file to inspect without printing values")
    provider_parser.add_argument("--env", action="append", default=[], help="persist an environment variable reference for provider configuration")
    provider_parser.add_argument("--from-env", action="store_true", help="persist references for provider fields found in the current environment")
    provider_parser.add_argument("--session-only", action="store_true", help="validate configuration for this invocation without writing config")
    provider_parser.add_argument("action", nargs="?", default="status", choices=["status", "doctor", "configure", "unset"])
    provider_parser.add_argument("provider", nargs="?")

    credential_parser = subparsers.add_parser("credential", help="resolve provider credentials without exposing values")
    credential_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    credential_parser.add_argument("--env-file", action="append", default=[], help="credential env/JSON/YAML file to inspect")
    credential_parser.add_argument("action", nargs="?", default="resolve", choices=["resolve", "backends"])
    credential_parser.add_argument("provider", nargs="?")

    source_parser = subparsers.add_parser("source", help="manage reusable provider/project sources")
    source_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    source_parser.add_argument("action", nargs="?", default="list", choices=["list", "add", "status", "remove"])
    source_parser.add_argument("source_id", nargs="?")
    source_parser.add_argument("--provider", help="provider id used by this source")
    source_parser.add_argument("--label", help="human-readable source label")
    source_parser.add_argument("--config", action="append", default=[], help="source config as KEY=VALUE")
    source_parser.add_argument("--env", action="append", default=[], help="environment reference as PROVIDER_ENV=LOCAL_ENV")
    source_parser.add_argument("--env-file", action="append", default=[], help="credential file reference")
    source_parser.add_argument("--default-for", action="append", default=[], help="intent that should use this source by default")
    source_parser.add_argument("--default-for-agent", action="append", default=[], help="agent id that should use this source by default")
    source_parser.add_argument("--set-default", action="store_true", help="set as default source for its provider")

    memory_parser = subparsers.add_parser("memory", help="inspect or reset local AI DevKit memory")
    memory_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    memory_parser.add_argument("action", nargs="?", default="show", choices=["show", "reset"])
    memory_parser.add_argument("--agent", dest="agent_id")
    memory_parser.add_argument("--source", dest="source_id")
    memory_parser.add_argument("--all", action="store_true", help="reset all local memory")

    llm_parser = subparsers.add_parser("llm", help="manage LLM backends")
    llm_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    llm_parser.add_argument(
        "action",
        nargs="?",
        default="list",
        choices=["list", "doctor", "configure", "set-default"],
    )
    llm_parser.add_argument("backend", nargs="?")
    llm_parser.add_argument("--api-key-env", help="environment variable that stores the API key")
    llm_parser.add_argument("--base-url", help="OpenAI-compatible base URL")
    llm_parser.add_argument("--model", help="default model id")
    llm_parser.add_argument("--command", dest="host_command", help="host CLI command name or path")
    llm_parser.add_argument("--set-default", action="store_true", help="set backend as the default LLM")

    install_parser = subparsers.add_parser("install", help="install AI DevKit host artifacts")
    install_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    install_parser.add_argument("scope", nargs="?", default="project", choices=["project", "global"])
    install_parser.add_argument("--target", help="project directory for project installs")
    install_parser.add_argument("--home", help="home directory override for global installs")
    install_parser.add_argument(
        "--host",
        default="all",
        choices=["all", "codex", "claude-code", "claude-desktop", "claude-ai"],
        help="host adapter to install",
    )
    install_parser.add_argument("--profiles", help="comma-separated project profiles to record in the lock")
    install_parser.add_argument("--dry-run", action="store_true", help="print planned writes without creating files")

    agents_parser = subparsers.add_parser("agents", aliases=["a"], help="list available agents")
    agents_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    agents_parser.add_argument("action", nargs="?", default="list", choices=["list"])

    capabilities_parser = subparsers.add_parser(
        "capabilities",
        aliases=["c"],
        help="list capabilities",
    )
    capabilities_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    capabilities_parser.add_argument("action_or_agent", nargs="?", default="list")
    capabilities_parser.add_argument("legacy_agent", nargs="?")
    capabilities_parser.add_argument("--agent", dest="agent")

    inspect_parser = subparsers.add_parser(
        "inspect",
        aliases=["i"],
        help="inspect an agent capability",
    )
    inspect_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    inspect_parser.add_argument("agent")
    inspect_parser.add_argument("capability")

    run_parser = subparsers.add_parser(
        "run",
        aliases=["r"],
        help="run an agent capability",
    )
    run_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    run_parser.add_argument("agent")
    run_parser.add_argument("capability")
    run_parser.add_argument("capability_args", nargs=argparse.REMAINDER)

    doctor_parser = subparsers.add_parser("doctor", help="run local diagnostics")
    doctor_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    doctor_parser.add_argument("--scope", default="auto", choices=["auto", "project", "global"], help="diagnostic scope")
    doctor_parser.add_argument("--project", help="project directory whose AI DevKit lock should be checked")
    doctor_parser.add_argument("--home", help="home directory override for global lock checks")
    return parser


def dispatch(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.version:
        return {"kind": "version", "program": getattr(args, "prog_name", "aikit"), "version": __version__}

    if not args.command:
        raise DevKitError("missing command. Use --help for usage.")

    command = canonical_command(args.command)
    if command == "agent":
        return agent_requires_llm(args)
    if command == "commands":
        return list_command_modes()
    if command == "providers":
        return dispatch_providers(args)
    if command == "provider":
        return dispatch_provider(args)
    if command == "credential":
        return dispatch_credential(args)
    if command == "source":
        return dispatch_source(args)
    if command == "memory":
        return dispatch_memory(args)
    if command == "llm":
        return dispatch_llm(args)
    if command == "install":
        return dispatch_install(args)
    if command == "agents":
        return {"kind": "agents", "items": list_agents()}
    if command == "capabilities":
        agent_id = resolve_capabilities_agent(args)
        if agent_id:
            agent = load_agent(agent_id)
            return {
                "kind": "capabilities",
                "agent": agent["id"],
                "items": list_capabilities(agent["path"]),
            }
        return {
            "kind": "capabilities",
            "agent": None,
            "items": list_all_capabilities(),
        }
    if command == "inspect":
        agent = load_agent(args.agent)
        capability = load_capability(agent["path"], args.capability)
        return {
            "kind": "capability",
            "agent": summarize_agent(agent),
            "capability": capability,
        }
    if command == "run":
        agent = load_agent(args.agent)
        return run_capability(
            agent,
            args.capability,
            args.capability_args,
            capture_output=args.json,
        )
    if command == "doctor":
        return doctor(args.project, args.home, args.scope)
    raise DevKitError(f"unsupported command: {args.command}")


def canonical_command(command: str) -> str:
    aliases = {
        "a": "agents",
        "c": "capabilities",
        "i": "inspect",
        "r": "run",
    }
    return aliases.get(command, command)


def list_command_modes() -> dict[str, Any]:
    return {
        "kind": "commands",
        "deterministic": [
            {
                "command": command,
                "requires_llm": False,
            }
            for command in DETERMINISTIC_COMMANDS
        ],
        "llm": [
            {
                "command": command,
                "requires_llm": True,
            }
            for command in LLM_COMMANDS
        ],
    }


def dispatch_llm(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action == "list":
            if args.backend:
                raise DevKitError("llm list does not accept a backend argument")
            return list_backends()
        if args.action == "doctor":
            return doctor_backends(args.backend)
        if args.action == "configure":
            if not args.backend:
                raise DevKitError("llm configure requires a backend")
            return configure_backend(
                args.backend,
                api_key_env=args.api_key_env,
                base_url=args.base_url,
                model=args.model,
                command=args.host_command,
                set_default=args.set_default,
            )
        if args.action == "set-default":
            if not args.backend:
                raise DevKitError("llm set-default requires a backend")
            return set_default_backend(args.backend)
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported llm action: {args.action}")


def dispatch_install(args: argparse.Namespace) -> dict[str, Any]:
    try:
        return install_runtime(
            ROOT,
            scope=args.scope,
            host=args.host,
            target=Path(args.target) if args.target else None,
            home=Path(args.home) if args.home else None,
            dry_run=args.dry_run,
            profiles=parse_profiles(args.profiles),
        )
    except InstallError as exc:
        raise DevKitError(str(exc)) from exc


def dispatch_providers(args: argparse.Namespace) -> dict[str, Any]:
    if args.action != "list":
        raise DevKitError(f"unsupported providers action: {args.action}")
    try:
        return list_providers(ROOT)
    except ProviderRegistryError as exc:
        raise DevKitError(str(exc)) from exc


def dispatch_provider(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action in {"status", "doctor"}:
            return provider_status_with_credentials(ROOT, args.provider, env_files=[Path(item) for item in args.env_file])
        if args.action == "configure":
            if not args.provider:
                raise DevKitError("provider configure requires a provider id")
            return configure_provider(
                ROOT,
                args.provider,
                env_refs=args.env,
                env_files=[Path(item) for item in args.env_file],
                from_env=args.from_env,
                session_only=args.session_only,
            )
        if args.action == "unset":
            if not args.provider:
                raise DevKitError("provider unset requires a provider id")
            return unset_provider_config(ROOT, args.provider)
    except ProviderRegistryError as exc:
        raise DevKitError(str(exc)) from exc
    except CredentialResolverError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported provider action: {args.action}")


def dispatch_credential(args: argparse.Namespace) -> dict[str, Any]:
    if args.action == "backends":
        if args.provider:
            raise DevKitError("credential backends does not accept a provider argument")
        return credential_backends()
    if args.action == "resolve":
        if not args.provider:
            raise DevKitError("credential resolve requires a provider id")
        try:
            return credential_resolution(ROOT, args.provider, env_files=[Path(item) for item in args.env_file])
        except (ProviderRegistryError, CredentialResolverError) as exc:
            raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported credential action: {args.action}")


def dispatch_source(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action == "list":
            return list_sources()
        if args.action == "add":
            if not args.source_id:
                raise DevKitError("source add requires a source id")
            return add_source(
                args.source_id,
                provider=args.provider,
                label=args.label,
                config_pairs=args.config,
                env_refs=args.env,
                env_files=args.env_file,
                default_for=args.default_for,
                default_for_agent=args.default_for_agent,
                set_default=args.set_default,
            )
        if args.action == "status":
            return source_status(args.source_id)
        if args.action == "remove":
            if not args.source_id:
                raise DevKitError("source remove requires a source id")
            return remove_source(args.source_id)
    except SourceRegistryError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported source action: {args.action}")


def dispatch_memory(args: argparse.Namespace) -> dict[str, Any]:
    if args.action == "show":
        return show_memory(ROOT, agent_id=args.agent_id, source_id=args.source_id)
    if args.action == "reset":
        return reset_memory(all_memory=args.all, agent_id=args.agent_id, source_id=args.source_id)
    raise DevKitError(f"unsupported memory action: {args.action}")


def agent_requires_llm(args: argparse.Namespace) -> dict[str, Any]:
    prompt = " ".join(args.prompt).strip()
    if not prompt:
        raise DevKitError("agent requires a natural-language prompt")
    route = route_prompt(prompt)
    if route:
        return invoke_deterministic_route(prompt, route)
    try:
        backend = resolve_backend(args.llm)
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    if backend and backend.get("status") == "ok":
        return invoke_agent_prompt(prompt, args.llm)
    return {
        "kind": "agent",
        "status": "blocked",
        "ok": False,
        "requires_llm": True,
        "llm_backend": args.llm,
        "prompt_received": True,
        "prompt_length": len(prompt),
        "message": "agent requires a configured LLM backend for natural-language tasks.",
        "next_steps": [
            "Use `agent run <agent> <capability>` for deterministic execution without LLM.",
            "Configure a backend with `agent llm configure <backend> --set-default`.",
            "Inspect available backends with `agent llm list` and their status with `agent llm doctor`.",
        ],
        "exit_code": 2,
    }


def invoke_deterministic_route(prompt: str, route: dict[str, Any]) -> dict[str, Any]:
    try:
        source = resolve_source(
            provider=route.get("provider"),
            intent=route.get("intent"),
            agent_id=route.get("agent_id"),
        )
    except SourceRegistryError as exc:
        raise DevKitError(str(exc)) from exc

    if not source:
        return {
            "kind": "agent",
            "status": "needs-input",
            "ok": False,
            "requires_source": True,
            "source_provider": route.get("provider"),
            "prompt_received": True,
            "prompt_length": len(prompt),
            "route": route,
            "napkin": napkin_context(ROOT, agent_id=route.get("agent_id")),
            "message": "agent identified the task, but no reusable source is configured for this provider.",
            "next_steps": [
                "Configure a source with `agent source add azure-sustentacao --provider azure-devops --config project=<project> --env AZURE_DEVOPS_PAT=AZURE_DEVOPS_PAT --default-for card`.",
                "Use `--config fixture=<path>` for local fixture-based tests or demos.",
                "Rerun the same prompt after configuring the source.",
            ],
            "exit_code": 2,
        }

    agent = load_agent(str(route["agent_id"]))
    capability_args = [*route.get("args", []), "--source", str(source["id"])]
    result = run_capability(agent, str(route["capability_id"]), capability_args, capture_output=True)
    response = result.get("stdout") or result.get("error") or ""
    record_usage(prompt, route=route, source_id=str(source["id"]))
    return {
        "kind": "agent",
        "status": result.get("status"),
        "ok": result.get("ok", False),
        "mode": "deterministic-route",
        "prompt_received": True,
        "prompt_length": len(prompt),
        "route": route,
        "source": public_source(source),
        "napkin": napkin_context(ROOT, agent_id=route.get("agent_id"), source_id=str(source["id"])),
        "response": response,
        "result": result,
        "exit_code": result.get("exit_code", 0 if result.get("ok") else 1),
    }


def resolve_capabilities_agent(args: argparse.Namespace) -> str | None:
    if args.agent:
        return args.agent

    action_or_agent = args.action_or_agent
    if action_or_agent == "list":
        return args.legacy_agent

    # Backward compatibility: `ai-devkit capabilities <agent>`.
    if args.legacy_agent:
        raise DevKitError("unexpected extra argument for capabilities")
    return action_or_agent


def runner_timeout_seconds() -> int:
    raw = os.environ.get("AI_DEVKIT_RUN_TIMEOUT", "300")
    return int(raw) if raw.isdigit() and int(raw) > 0 else 300


def list_agents() -> list[dict[str, Any]]:
    if not AGENTS_DIR.exists():
        return []

    agents = []
    for path in sorted(AGENTS_DIR.iterdir()):
        if not path.is_dir():
            continue
        manifest = path / "agent.yaml"
        if not manifest.exists():
            continue
        data = load_manifest(manifest)
        capabilities = list_capabilities(path)
        agents.append(
            {
                "id": data.get("id", path.name),
                "name": data.get("name", path.name),
                "status": data.get("status"),
                "version": data.get("version"),
                "path": str(path.relative_to(ROOT)),
                "purpose": compact_text(data.get("purpose")),
                "capabilities": len(capabilities),
            }
        )
    return agents


def load_agent(agent_id: str) -> dict[str, Any]:
    path = AGENTS_DIR / agent_id
    manifest = path / "agent.yaml"
    if not manifest.exists():
        available = ", ".join(item["id"] for item in list_agents()) or "none"
        raise DevKitError(f"agent not found: {agent_id}. available: {available}")

    data = load_manifest(manifest)
    data["path"] = path
    data["manifest_path"] = manifest
    return data


def summarize_agent(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": agent.get("id"),
        "name": agent.get("name"),
        "status": agent.get("status"),
        "version": agent.get("version"),
        "path": str(agent["path"].relative_to(ROOT)),
    }


def list_all_capabilities() -> list[dict[str, Any]]:
    capabilities: list[dict[str, Any]] = []
    for agent in list_agents():
        agent_path = AGENTS_DIR / agent["id"]
        for capability in list_capabilities(agent_path):
            item = dict(capability)
            item["agent"] = agent["id"]
            capabilities.append(item)
    return capabilities


def list_capabilities(agent_path: Path) -> list[dict[str, Any]]:
    capabilities_dir = agent_path / "capabilities"
    if not capabilities_dir.exists():
        return []

    capabilities = []
    for path in sorted(capabilities_dir.iterdir()):
        if not path.is_dir():
            continue
        manifest = path / "capability.yaml"
        if not manifest.exists():
            continue
        data = load_manifest(manifest)
        runner = ((data.get("entrypoint", {}) or {}).get("runner"))
        capabilities.append(
            {
                "id": data.get("id", path.name),
                "name": data.get("name", path.name),
                "status": data.get("status"),
                "version": data.get("version"),
                "path": str(path.relative_to(ROOT)),
                "purpose": compact_text(data.get("purpose")),
                "write_policy": data.get("write_policy"),
                "runner": runner,
                "has_runner": bool(runner),
                "has_workflow": (path / "workflow.md").exists(),
                "has_decision_rules": (path / "decision-rules.md").exists(),
            }
        )
    return capabilities


def load_capability(agent_path: Path, capability_id: str) -> dict[str, Any]:
    path = agent_path / "capabilities" / capability_id
    manifest = path / "capability.yaml"
    if not manifest.exists():
        available = ", ".join(item["id"].split(".")[-1] for item in list_capabilities(agent_path))
        raise DevKitError(
            f"capability not found: {capability_id}. available: {available or 'none'}"
        )

    data = load_manifest(manifest)
    return {
        "id": data.get("id", capability_id),
        "name": data.get("name", capability_id),
        "status": data.get("status"),
        "version": data.get("version"),
        "path": str(path.relative_to(ROOT)),
        "purpose": compact_text(data.get("purpose")),
        "inputs": data.get("inputs", {}),
        "outputs": data.get("outputs", {}),
        "entrypoint": resolve_refs(path, data.get("entrypoint", {})),
        "integration": resolve_integration_refs(path, data.get("integration", {})),
        "write_policy": data.get("write_policy"),
    }


def run_capability(
    agent: dict[str, Any],
    capability_id: str,
    capability_args: list[str],
    capture_output: bool = True,
) -> dict[str, Any]:
    agent_path = agent["path"]
    capability_path = agent_path / "capabilities" / capability_id
    manifest = capability_path / "capability.yaml"
    if not manifest.exists():
        available = ", ".join(item["id"].split(".")[-1] for item in list_capabilities(agent_path))
        raise DevKitError(
            f"capability not found: {capability_id}. available: {available or 'none'}"
        )

    data = load_manifest(manifest)
    try:
        source = None
        if supports_runtime_source(str(agent.get("id")), capability_id):
            source_id, capability_args = extract_source_arg(capability_args)
            source = resolve_source(source_id=source_id) if source_id else None
            capability_args = apply_source_to_args(source, str(agent.get("id")), capability_id, capability_args)
        runtime_env = os.environ | source_env(source)
    except SourceRegistryError as exc:
        return run_payload(
            status="blocked",
            agent=summarize_agent(agent),
            capability=data.get("id", capability_id),
            runner=None,
            returncode=2,
            error=str(exc),
            risks=["Source configuration could not be resolved."],
            next_steps=["Inspect available sources with `agent source list` or configure one with `agent source add`."],
            exit_code=2,
        )
    guardrail = evaluate_execution_guardrails(data, capability_args)
    capability_args = guardrail["args"]
    if not guardrail["ready"]:
        return run_payload(
            status="blocked",
            agent=summarize_agent(agent),
            capability=data.get("id", capability_id),
            runner=None,
            returncode=2,
            guardrail={
                "reason": guardrail["reason"],
                "write_policy": guardrail["write_policy"],
                "execute_requested": True,
            },
            risks=guardrail["risks"],
            next_steps=guardrail["next_steps"],
            exit_code=2,
        )
    readiness = evaluate_provider_requirements(ROOT, data)
    if not readiness["ready"]:
        return run_payload(
            status=readiness["status"],
            agent=summarize_agent(agent),
            capability=data.get("id", capability_id),
            runner=None,
            returncode=readiness.get("exit_code") or 0,
            providers=readiness["providers"],
            fallback_applied=readiness["fallback_applied"],
            evidence=readiness["evidence"],
            risks=readiness["risks"],
            next_steps=readiness["next_steps"],
            artifacts=readiness["artifacts"],
            exit_code=readiness.get("exit_code"),
        )

    runner_ref = (data.get("entrypoint", {}) or {}).get("runner")
    if not runner_ref:
        if capture_output:
            return run_payload(
                status="failed",
                agent=summarize_agent(agent),
                capability=data.get("id", capability_id),
                runner=None,
                returncode=2,
                providers=readiness["providers"],
                error=f"capability has no runner: {capability_id}",
                risks=["Capability cannot be executed by the runtime because no runner is declared."],
                next_steps=["Add `entrypoint.runner` to the capability manifest or use a capability with an executable runner."],
                exit_code=2,
            )
        raise DevKitError(f"capability has no runner: {capability_id}")

    runner_path = (capability_path / runner_ref).resolve()
    if not runner_path.exists():
        if capture_output:
            relative_runner = str(runner_path.relative_to(ROOT))
            return run_payload(
                status="failed",
                agent=summarize_agent(agent),
                capability=data.get("id", capability_id),
                runner=relative_runner,
                returncode=2,
                providers=readiness["providers"],
                error=f"runner not found: {relative_runner}",
                risks=["Capability runner declared in the manifest does not exist on disk."],
                next_steps=["Fix `entrypoint.runner` in the capability manifest or restore the missing runner file."],
                exit_code=2,
            )
        raise DevKitError(f"runner not found: {runner_path.relative_to(ROOT)}")

    timeout_seconds = runner_timeout_seconds()
    try:
        if capture_output:
            process = subprocess.run(
                [sys.executable, str(runner_path), *capability_args],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=runtime_env,
                timeout=timeout_seconds,
            )
        else:
            process = subprocess.run(
                [sys.executable, str(runner_path), *capability_args],
                cwd=ROOT,
                check=False,
                text=True,
                env=runtime_env,
                timeout=timeout_seconds,
            )
    except subprocess.TimeoutExpired as exc:
        if capture_output:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode(errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors="replace")
            return run_payload(
                status="failed",
                agent=summarize_agent(agent),
                capability=data.get("id", capability_id),
                runner=str(runner_path.relative_to(ROOT)),
                stdout=stdout,
                stderr=stderr,
                returncode=124,
                providers=readiness["providers"],
                error=f"runner timed out after {timeout_seconds}s: {agent.get('id')}/{capability_id}",
                risks=["Capability runner exceeded the configured timeout."],
                next_steps=["Review runner performance, inputs, provider latency, or increase `AI_DEVKIT_RUN_TIMEOUT` for this execution."],
                exit_code=124,
            )
        raise DevKitError(f"runner timed out after {timeout_seconds}s: {agent.get('id')}/{capability_id}") from exc
    if process.returncode != 0:
        stderr = process.stderr if capture_output else ""
        if capture_output:
            stdout = process.stdout or ""
            message = (stderr or stdout or f"runner failed: {process.returncode}").strip()
            return run_payload(
                status="failed",
                agent=summarize_agent(agent),
                capability=data.get("id", capability_id),
                runner=str(runner_path.relative_to(ROOT)),
                stdout=stdout,
                stderr=stderr,
                returncode=process.returncode,
                providers=readiness["providers"],
                error=message,
                risks=["Capability runner returned a non-zero exit code."],
                next_steps=["Review stdout/stderr and rerun after correcting the capability inputs or environment."],
                exit_code=process.returncode,
            )
        raise DevKitError((stderr or "").strip() or f"runner failed: {process.returncode}")

    return run_payload(
        status="ok",
        agent=summarize_agent(agent),
        capability=data.get("id", capability_id),
        runner=str(runner_path.relative_to(ROOT)),
        stdout=process.stdout if capture_output else "",
        stderr=process.stderr if capture_output else "",
        returncode=process.returncode,
        providers=readiness["providers"],
    )


def supports_runtime_source(agent_id: str, capability_id: str) -> bool:
    return agent_id == "azure-devops-orchestrator" and capability_id == "read-card"


def doctor(project: str | None = None, home: str | None = None, scope: str = "auto") -> dict[str, Any]:
    agents = list_agents()
    capabilities = list_all_capabilities()
    declared_runners = sum(1 for item in capabilities if item.get("has_runner"))
    workflows = sum(1 for item in capabilities if item.get("has_workflow"))
    decision_rules = sum(1 for item in capabilities if item.get("has_decision_rules"))
    validator = ROOT / "scripts" / "validate-repo.py"
    errors: list[str] = []
    warnings: list[str] = []

    if not ROOT.exists():
        errors.append(f"root not found: {ROOT}")
    if not AGENTS_DIR.is_dir():
        errors.append(f"agents directory not found: {AGENTS_DIR}")
    if not validator.exists():
        warnings.append("scripts/validate-repo.py not found")
    project_path = doctor_project_path(project, scope)
    home_path = Path(home) if home else None
    locks = lock_status(project_path, home_path)
    if project and locks["status"] == "diverged":
        warnings.append("lock divergence between global runtime.lock and project ai-devkit.lock")
    checks = {
        "root_exists": ROOT.exists(),
        "agents_dir_exists": AGENTS_DIR.is_dir(),
        "validator_exists": validator.exists(),
        "agent_command_exists": (ROOT / "agent").exists(),
        "aikit_command_exists": (ROOT / "aikit").exists(),
        "ai_devkit_command_exists": (ROOT / "ai-devkit").exists(),
        "agent_on_path": shutil.which("agent") is not None,
    }
    diagnostics = build_diagnostics(
        ROOT,
        project=project_path,
        home=home_path,
        runtime_checks=checks,
        runtime_status="ok" if not errors else "error",
        locks=locks,
    )

    return {
        "kind": "doctor",
        "status": "ok" if not errors else "error",
        "scope": scope,
        "root": str(ROOT),
        "summary": {
            "agents": len(agents),
            "capabilities": len(capabilities),
            "declared_runners": declared_runners,
            "workflows": workflows,
            "decision_rules": decision_rules,
        },
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "locks": locks,
        "diagnostics": diagnostics,
    }


def doctor_project_path(project: str | None, scope: str) -> Path | None:
    if project:
        return Path(project)
    if scope == "project":
        return Path.cwd()
    return None


def resolve_refs(base: Path, refs: dict[str, Any]) -> dict[str, Any]:
    resolved = {}
    for key, value in refs.items():
        if isinstance(value, str):
            resolved[key] = {
                "ref": value,
                "path": str((base / value).resolve().relative_to(ROOT)),
                "exists": (base / value).resolve().exists(),
            }
        else:
            resolved[key] = value
    return resolved


def resolve_integration_refs(base: Path, integration: dict[str, Any]) -> dict[str, Any]:
    if not integration:
        return {}

    resolved: dict[str, Any] = {}
    repository = integration.get("repository")
    if repository:
        repository_path = (base / repository).resolve()
        resolved["repository"] = {
            "ref": repository,
            "path": str(repository_path.relative_to(ROOT)),
            "exists": repository_path.exists(),
        }

    methods = []
    for method in integration.get("methods", []) or []:
        method_path = (base / method).resolve()
        methods.append(
            {
                "ref": method,
                "path": str(method_path.relative_to(ROOT)),
                "exists": method_path.exists(),
            }
        )
    resolved["methods"] = methods
    return resolved


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return load_simple_yaml(path)

    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise DevKitError(f"manifest must be a mapping: {path}")
    return data


def load_simple_yaml(path: Path) -> dict[str, Any]:
    # Fallback parser for simple top-level YAML used by the CLI when PyYAML is
    # unavailable. It is intentionally narrow; install PyYAML for full support.
    data: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            if value:
                data[current_key] = parse_scalar(value)
                current_list = None
            else:
                current_list = []
                data[current_key] = current_list
            continue
        if current_key and current_list is not None and stripped.startswith("- "):
            current_list.append(stripped[2:].strip())
    return data


def parse_scalar(value: str) -> Any:
    if value in {"true", "false"}:
        return value == "true"
    return value.strip('"').strip("'")


def compact_text(value: Any) -> str | None:
    if value is None:
        return None
    return " ".join(str(value).split())


def print_human(result: dict[str, Any]) -> None:
    kind = result["kind"]
    if kind == "version":
        print(f"{result.get('program', 'aikit')} {result['version']}")
    elif kind == "agents":
        print_agents(result["items"])
    elif kind == "capabilities":
        print_capabilities(result["agent"], result["items"])
    elif kind == "capability":
        print_capability(result)
    elif kind == "run":
        print_run(result)
    elif kind == "doctor":
        print_doctor(result)
    elif kind == "commands":
        print_command_modes(result)
    elif kind == "agent":
        print_agent_response(result)
    elif kind == "llm-backends":
        print_llm_backends(result)
    elif kind == "llm-doctor":
        print_llm_doctor(result)
    elif kind == "llm-configure":
        print_llm_configure(result)
    elif kind == "llm-default":
        print_llm_default(result)
    elif kind == "providers":
        print_providers(result)
    elif kind == "provider-status":
        print_provider_status(result)
    elif kind == "provider-configure":
        print_provider_configure(result)
    elif kind == "provider-unset":
        print_provider_unset(result)
    elif kind == "credential-resolution":
        print_credential_resolution(result)
    elif kind == "credential-backends":
        print_credential_backends(result)
    elif kind == "sources":
        print_sources(result)
    elif kind == "source-status":
        print_source_status(result)
    elif kind == "source-configure":
        print_source_configure(result)
    elif kind == "source-remove":
        print_source_remove(result)
    elif kind == "memory":
        print_memory(result)
    elif kind == "memory-reset":
        print_memory_reset(result)
    elif kind == "install":
        print_install(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def print_agents(items: list[dict[str, Any]]) -> None:
    if not items:
        print("No agents found.")
        return
    for item in items:
        count = item.get("capabilities", 0)
        print(f"{item['id']}  {item.get('status') or '-'}  {count} capabilities")
        if item.get("purpose"):
            print(f"  {item['purpose']}")


def print_capabilities(agent: str | None, items: list[dict[str, Any]]) -> None:
    if not items:
        suffix = f" for {agent}" if agent else ""
        print(f"No capabilities found{suffix}.")
        return
    if agent:
        print(f"{agent}:")
    for item in items:
        short_id = item["id"].split(".")[-1]
        prefix = "" if agent else f"{item.get('agent', '-')}/"
        runner = "runner" if item.get("has_runner") else "no-runner"
        workflow = "workflow" if item.get("has_workflow") else "no-workflow"
        rules = "rules" if item.get("has_decision_rules") else "no-rules"
        print(f"- {prefix}{short_id}  {item.get('write_policy') or '-'}  {item.get('status') or '-'}  {runner}  {workflow}  {rules}")
        if item.get("purpose"):
            print(f"  {item['purpose']}")


def print_capability(result: dict[str, Any]) -> None:
    agent = result["agent"]
    capability = result["capability"]
    print(f"{agent['id']} / {capability['id'].split('.')[-1]}")
    print(f"Status: {capability.get('status') or '-'}")
    print(f"Version: {capability.get('version') or '-'}")
    print(f"Write policy: {capability.get('write_policy') or '-'}")
    if capability.get("purpose"):
        print(f"\n{capability['purpose']}")
    print("\nEntrypoints:")
    for key, value in capability.get("entrypoint", {}).items():
        if isinstance(value, dict):
            marker = "ok" if value["exists"] else "missing"
            print(f"- {key}: {value['path']} [{marker}]")
    integration = capability.get("integration", {})
    if integration:
        print("\nIntegration:")
        repo = integration.get("repository")
        if repo:
            marker = "ok" if repo["exists"] else "missing"
            print(f"- repository: {repo['path']} [{marker}]")
        for method in integration.get("methods", []):
            marker = "ok" if method["exists"] else "missing"
            print(f"- method: {method['path']} [{marker}]")


def print_run(result: dict[str, Any]) -> None:
    if result.get("status") in {None, "ok"}:
        print(result.get("stdout", ""), end="")
        return

    print(f"Run {result['status']}: {result['agent']['id']} / {result['capability'].split('.')[-1]}")
    if result.get("fallback_applied"):
        print(f"Fallback: {result['fallback_applied']}")
    providers = result.get("providers") or {}
    missing = providers.get("missing") or []
    if missing:
        print(f"Missing providers: {', '.join(missing)}")
    if result.get("risks"):
        print("\nRisks:")
        for risk in result["risks"]:
            print(f"- {risk}")
    if result.get("next_steps"):
        print("\nNext steps:")
        for step in result["next_steps"]:
            print(f"- {step}")


def print_doctor(result: dict[str, Any]) -> None:
    print(f"AI DevKit doctor: {result['status']}")
    print(f"Root: {result['root']}")
    summary = result["summary"]
    print(f"Agents: {summary['agents']}")
    print(f"Capabilities: {summary['capabilities']}")
    print(f"Declared runners: {summary['declared_runners']}")
    print(f"Workflows: {summary['workflows']}")
    print(f"Decision rules: {summary['decision_rules']}")
    diagnostics = result.get("diagnostics") or {}
    if diagnostics:
        providers = diagnostics.get("providers") or {}
        llm = diagnostics.get("llm") or {}
        plugins = diagnostics.get("plugins") or {}
        locks = diagnostics.get("locks") or {}
        print("\nDiagnostics:")
        print(f"- Locks: {locks.get('status', '-')}")
        print(f"- Plugins: {plugins.get('status', '-')}")
        print(f"- Providers: {providers.get('status', '-')} ({providers.get('ok', 0)} ok, {providers.get('missing', 0)} missing)")
        print(f"- LLM: {llm.get('status', '-')} ({llm.get('ok', 0)} ok, {llm.get('missing', 0)} missing)")
    if result["warnings"]:
        print("\nWarnings:")
        for warning in result["warnings"]:
            print(f"- {warning}")
    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"- {error}")


def print_command_modes(result: dict[str, Any]) -> None:
    print("Deterministic commands (no LLM required):")
    for item in result["deterministic"]:
        print(f"- {item['command']}")
    print("\nLLM commands:")
    for item in result["llm"]:
        print(f"- {item['command']}")


def print_agent_response(result: dict[str, Any]) -> None:
    if result.get("status") == "ok":
        print(result.get("response", ""))
        return
    print(result.get("message") or result.get("response") or "Agent execution did not complete.")
    if result.get("llm_backend"):
        print(f"Requested backend: {result['llm_backend']}")
    if result.get("next_steps"):
        print("\nNext steps:")
        for step in result["next_steps"]:
            print(f"- {step}")


def print_sources(result: dict[str, Any]) -> None:
    print(f"Sources config: {result['config_path']}")
    if not result["items"]:
        print("No sources configured.")
        return
    for item in result["items"]:
        print(f"- {item['id']}  {item['provider']}  {item.get('label') or '-'}")


def print_source_status(result: dict[str, Any]) -> None:
    print(f"Source status: {result['status']}")
    for item in result["items"]:
        print(f"- {item['id']}: {item['status']}")
        missing = item.get("missing_env_refs") or []
        if missing:
            print(f"  Missing env refs: {', '.join(missing)}")


def print_source_configure(result: dict[str, Any]) -> None:
    source = result["source"]
    print(f"Source configured: {source['id']}")
    print(f"Provider: {source['provider']}")
    print(f"Config: {result['config_path']}")
    print("Stored secret: no")


def print_source_remove(result: dict[str, Any]) -> None:
    print(f"Source removed: {result['source']['id']}")
    print(f"Config: {result['config_path']}")


def print_memory(result: dict[str, Any]) -> None:
    print(f"Memory home: {result['memory_home']}")
    for bucket in ("prompts", "routes", "sources"):
        print(f"\n{bucket.title()}:")
        items = result["usage"].get(bucket) or []
        if not items:
            print("- none")
            continue
        for item in items:
            print(f"- {item['key']} ({item.get('count', 0)})")


def print_memory_reset(result: dict[str, Any]) -> None:
    print("Memory reset.")
    print(f"Config: {result['config_path']}")


def print_llm_backends(result: dict[str, Any]) -> None:
    print(f"LLM config: {result['config_path']}")
    print(f"Default: {result.get('default') or '-'}")
    for item in result["items"]:
        markers = []
        if item.get("configured"):
            markers.append("configured")
        if item.get("default"):
            markers.append("default")
        suffix = f" [{' '.join(markers)}]" if markers else ""
        print(f"- {item['id']}  {item['kind']}  {item['auth']}{suffix}")
        if item.get("notes"):
            print(f"  {item['notes']}")


def print_llm_doctor(result: dict[str, Any]) -> None:
    print(f"LLM doctor: {result['status']}")
    print(f"Config: {result['config_path']}")
    print(f"Default: {result.get('default') or '-'}")
    for item in result["items"]:
        print(f"- {item['id']}: {item['status']}")
        if item.get("message"):
            print(f"  {item['message']}")


def print_llm_configure(result: dict[str, Any]) -> None:
    print(f"LLM backend configured: {result['backend']}")
    print(f"Config: {result['config_path']}")
    print(f"Default: {result.get('default') or '-'}")
    print("Stored secret: no")


def print_llm_default(result: dict[str, Any]) -> None:
    print(f"Default LLM backend: {result['default']}")
    print(f"Config: {result['config_path']}")


def print_providers(result: dict[str, Any]) -> None:
    if not result["items"]:
        print("No providers found.")
        return
    for item in result["items"]:
        write_marker = "writes" if item.get("writes") else "read"
        print(f"- {item['id']}  {item['kind']}  {item['status']}  {write_marker}")
        if item.get("description"):
            print(f"  {item['description']}")


def print_provider_status(result: dict[str, Any]) -> None:
    print(f"Provider status: {result['status']}")
    for item in result["items"]:
        print(f"- {item['id']}: {item['status']}")
        if item.get("message"):
            print(f"  {item['message']}")
        missing = item.get("missing_required_fields") or []
        if missing:
            print(f"  Missing config: {', '.join(missing)}")
        auth = item.get("auth") or {}
        missing_secret_fields = auth.get("missing_secret_fields") or []
        if missing_secret_fields:
            print(f"  Missing secret refs: {', '.join(missing_secret_fields)}")
        detected_env_file = item.get("detected_env_file") or []
        if detected_env_file:
            print(f"  Detected in env-file: {', '.join(detected_env_file)}")


def print_provider_configure(result: dict[str, Any]) -> None:
    print(result.get("message") or f"Provider configuration {result['status']}.")
    print(f"Provider: {result['provider']}")
    if result.get("status") == "configured":
        print(f"Config: {result['config_path']}")
        print("Stored secret: no")
        return
    if result.get("status") == "session-only":
        print("Session-only: yes")
        print("Stored secret: no")
        return
    if result.get("required_config_fields"):
        print("Required config fields:")
        for field in result["required_config_fields"]:
            print(f"- {field}")
    print("Next steps:")
    for step in result["next_steps"]:
        print(f"- {step}")


def print_provider_unset(result: dict[str, Any]) -> None:
    print(f"Provider config {result['status']}: {result['provider']}")
    print(f"Config: {result['config_path']}")


def print_credential_resolution(result: dict[str, Any]) -> None:
    print(f"Credential resolution for {result['provider']}: {result['status']}")
    if result.get("detected_env"):
        print(f"Detected in env: {', '.join(result['detected_env'])}")
    if result.get("detected_env_file"):
        print(f"Detected in env-file: {', '.join(result['detected_env_file'])}")
    if result.get("missing_required_fields"):
        print(f"Missing required fields: {', '.join(result['missing_required_fields'])}")
    auth = result.get("auth") or {}
    if auth.get("missing_secret_fields"):
        print(f"Missing secret refs: {', '.join(auth['missing_secret_fields'])}")
    print("Secret values returned: no")


def print_credential_backends(result: dict[str, Any]) -> None:
    print("Credential resolver backends:")
    for item in result["items"]:
        print(f"- {item}")


def print_install(result: dict[str, Any]) -> None:
    print(f"AI DevKit install: {result['status']}")
    print(f"Scope: {result['scope']}")
    print(f"Target: {result['target']}")
    print(f"Hosts: {', '.join(result['hosts'])}")
    print("Stored secret: no")
    paths = result["planned"] if result.get("dry_run") else result["written"]
    if paths:
        label = "Planned writes" if result.get("dry_run") else "Written files"
        print(f"\n{label}:")
        for path in paths:
            print(f"- {path}")
    if result.get("next_steps"):
        print("\nNext steps:")
        for step in result["next_steps"]:
            print(f"- {step}")


if __name__ == "__main__":
    raise SystemExit(main())
