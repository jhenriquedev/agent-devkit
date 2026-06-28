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

from cli.aikit.aliases import add_alias, list_aliases, remove_alias, sync_aliases
from cli.aikit import __version__
from cli.aikit.audit import export_audit, list_audits, record_audit, show_audit
from cli.aikit.calendar import calendar_list, calendar_summary, calendar_today, calendar_tomorrow, configure_calendar
from cli.aikit.configuration_orchestrator import provider_wizard_from_requirement
from cli.aikit.decision_store import list_decisions, reset_decisions, set_decision
from cli.aikit.diagnostics import build_diagnostics
from cli.aikit.fallback import evaluate_provider_requirements
from cli.aikit.github_pr import pr_create_automation, pr_inspect, pr_list_review_requests, pr_review
from cli.aikit.guardrails import evaluate_execution_guardrails
from cli.aikit.identity import enforce_identity_response, is_identity_question, local_identity_response, public_name
from cli.aikit.llm import (
    configure_backend,
    doctor_backends,
    invoke_agent_prompt,
    list_backends,
    llm_preference,
    set_default_backend,
    set_llm_preference,
)
from cli.aikit.memory import memory_path_payload, napkin_context, record_usage, reset_memory, show_memory
from cli.aikit.model_router import build_model_plan
from cli.aikit.ollama import ollama_models, ollama_pull, ollama_status, ollama_update
from cli.aikit.personality import load_personality, reset_personality, setup_personality, update_personality
from cli.aikit.permissions import grant_permission, revoke_permission, show_permissions
from cli.aikit.provider_wizard import missing_source_wizard
from cli.aikit.review_gate import build_review_gate, mark_reviewed
from cli.aikit.sessions import (
    build_contextual_prompt,
    get_or_create_session,
    list_sessions,
    record_exchange,
    resume_session,
    show_session,
)
from cli.aikit.setup_wizard import setup_wizard
from cli.aikit.scheduler import run_scheduler_once, scheduler_daemon_plan
from cli.aikit.tasks import (
    create_task,
    delete_task,
    list_tasks,
    run_task,
    show_task,
    task_history,
    update_task_schedule,
    update_task_status,
)
from cli.aikit.toolchain import doctor_toolchain, install_toolchain, list_toolchain
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
    "personality",
    "setup",
    "alias",
    "session",
    "toolchain",
    "task",
    "scheduler",
    "calendar",
    "pr",
    "permissions",
    "audit",
    "config",
    "tools",
    "integrations",
    "skills",
    "decisions",
    "ollama",
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
        maybe_record_cli_audit(args, result=None, error=str(exc))
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if result is None:
        return 0
    maybe_record_cli_audit(args, result=result, error=None)

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
    parser.add_argument("--dry-run", dest="global_dry_run", action="store_true", help="show execution plan without external write effects")
    parser.add_argument("-v", "--version", action="store_true", help="print CLI version and exit")
    parser.add_argument(
        "-s",
        "--sessions",
        dest="sessions_shortcut",
        action="store_true",
        help="list local conversation sessions and exit",
    )

    subparsers = parser.add_subparsers(dest="command")

    agent_parser = subparsers.add_parser(
        "agent",
        help="handle a natural-language task using an LLM backend",
    )
    agent_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    agent_parser.add_argument("--llm", help="LLM backend id to use")
    agent_parser.add_argument("--dry-run", action="store_true", help="show execution plan without invoking LLM or external writes")
    agent_parser.add_argument("--no-llm-fallback", action="store_true", help="disable automatic fallback to secondary LLM backends")
    agent_parser.add_argument("--session", dest="session_id", help="resume a local conversation session")
    agent_parser.add_argument("--new-session", action="store_true", help="start a new local conversation session")
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
    memory_parser.add_argument("action", nargs="?", default="show", choices=["show", "path", "reset"])
    memory_parser.add_argument("--agent", dest="agent_id")
    memory_parser.add_argument("--source", dest="source_id")
    memory_parser.add_argument("--all", action="store_true", help="reset all local memory")
    memory_parser.add_argument("--sessions", action="store_true", help="reset local conversation sessions")
    memory_parser.add_argument("--tasks", action="store_true", help="reset local task schedules")
    memory_parser.add_argument("--cache", action="store_true", help="reset local cache")

    personality_parser = subparsers.add_parser("personality", help="inspect or update local Agent DevKit personality")
    personality_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    personality_parser.add_argument("action", nargs="?", default="show", choices=["show", "edit", "reset"])
    personality_parser.add_argument("--name", dest="agent_name", help="public agent name")
    personality_parser.add_argument("--user-name", help="user name")
    personality_parser.add_argument("--language", help="default response language")
    personality_parser.add_argument("--tone", help="response tone")
    personality_parser.add_argument("--detail-level", help="response detail level")

    setup_parser = subparsers.add_parser("setup", help="run setup helpers")
    setup_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    setup_parser.add_argument("--dry-run", action="store_true", help="show setup plan without installing external tools")
    setup_parser.add_argument("--yes", action="store_true", help="confirm setup actions")
    setup_parser.add_argument("action", nargs="?", default="plan", choices=["plan", "personality"])

    alias_parser = subparsers.add_parser("alias", help="manage local command aliases for agent")
    alias_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    alias_parser.add_argument("action", nargs="?", default="list", choices=["add", "list", "remove", "sync"])
    alias_parser.add_argument("name", nargs="?")
    alias_parser.add_argument("--force", action="store_true", help="allow replacing an existing local alias file")

    session_parser = subparsers.add_parser("session", help="manage local conversation sessions")
    session_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    session_parser.add_argument("action", nargs="?", default="list", choices=["list", "show", "resume"])
    session_parser.add_argument("session_id", nargs="?")

    toolchain_parser = subparsers.add_parser("toolchain", help="inspect or install external tools")
    toolchain_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    toolchain_parser.add_argument("action", nargs="?", default="list", choices=["list", "doctor", "install"])
    toolchain_parser.add_argument("tool", nargs="?", default="all")
    toolchain_parser.add_argument("--dry-run", action="store_true", help="show install plan without executing it")
    toolchain_parser.add_argument("--yes", action="store_true", help="confirm external tool installation")

    task_parser = subparsers.add_parser("task", help="manage local scheduled tasks")
    task_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    task_parser.add_argument("action", nargs="?", default="list", choices=["create", "list", "show", "history", "run", "pause", "resume", "update", "enable", "disable", "delete"])
    task_parser.add_argument("task_id", nargs="?")
    task_parser.add_argument("--title")
    task_parser.add_argument("--prompt")
    task_parser.add_argument("--every")
    task_parser.add_argument("--cron")
    task_parser.add_argument("--dry-run", action="store_true")
    task_parser.add_argument("--yes", action="store_true")

    scheduler_parser = subparsers.add_parser("scheduler", help="run local scheduler")
    scheduler_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    scheduler_parser.add_argument("action", nargs="?", default="run-once", choices=["run-once", "daemon"])
    scheduler_parser.add_argument("--dry-run", action="store_true")

    calendar_parser = subparsers.add_parser("calendar", help="inspect configured calendar")
    calendar_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    calendar_parser.add_argument("action", nargs="?", default="today", choices=["today", "tomorrow", "list", "configure"])
    calendar_parser.add_argument("--from", dest="date_from")
    calendar_parser.add_argument("--to", dest="date_to")
    calendar_parser.add_argument("--ics")
    calendar_parser.add_argument("--timezone")

    pr_parser = subparsers.add_parser("pr", help="review GitHub pull requests")
    pr_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    pr_parser.add_argument("action", nargs="?", default="list-review-requests", choices=["list-review-requests", "inspect", "review", "automation"])
    pr_parser.add_argument("pr_ref", nargs="?")
    pr_parser.add_argument("automation_action", nargs="?")
    pr_parser.add_argument("--approve", action="store_true")
    pr_parser.add_argument("--request-changes", action="store_true")
    pr_parser.add_argument("--comment")
    pr_parser.add_argument("--allow-write", action="store_true")
    pr_parser.add_argument("--dry-run", action="store_true")
    pr_parser.add_argument("--time", default="09:00")

    permissions_parser = subparsers.add_parser("permissions", help="manage local permission policies")
    permissions_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    permissions_parser.add_argument("action", nargs="?", default="show", choices=["show", "grant", "revoke"])
    permissions_parser.add_argument("agent", nargs="?")
    permissions_parser.add_argument("provider", nargs="?")
    permissions_parser.add_argument("level", nargs="?")
    permissions_parser.add_argument("--project")
    permissions_parser.add_argument("--task", dest="task_id")

    audit_parser = subparsers.add_parser("audit", help="inspect local execution audit trail")
    audit_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    audit_parser.add_argument("action", nargs="?", default="list", choices=["list", "show", "export"])
    audit_parser.add_argument("execution_id", nargs="?")
    audit_parser.add_argument("--limit", type=int, default=20)
    audit_parser.add_argument("--format", default="md", choices=["md", "json"])

    config_parser = subparsers.add_parser("config", help="inspect local Agent DevKit configuration")
    config_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    config_parser.add_argument("action", nargs="?", default="show", choices=["show", "path"])

    for command_name, help_text in (
        ("tools", "manage enabled local tools"),
        ("integrations", "manage provider integration decisions"),
        ("skills", "manage local skill decisions"),
    ):
        control_parser = subparsers.add_parser(command_name, help=help_text)
        control_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        control_parser.add_argument("action", nargs="?", default="list", choices=["list", "enable", "disable"])
        control_parser.add_argument("item_id", nargs="?")

    decisions_parser = subparsers.add_parser("decisions", help="inspect or reset local opt-in and opt-out decisions")
    decisions_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    decisions_parser.add_argument("action", nargs="?", default="list", choices=["list", "forget", "reset"])
    decisions_parser.add_argument("item_id", nargs="?")
    decisions_parser.add_argument("--category", choices=["tools", "integrations", "skills", "llms"])

    ollama_parser = subparsers.add_parser("ollama", help="inspect and manage local Ollama models")
    ollama_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    ollama_parser.add_argument("action", nargs="?", default="status", choices=["status", "models", "pull", "update"])
    ollama_parser.add_argument("model", nargs="?")
    ollama_parser.add_argument("--yes", action="store_true", help="confirm Ollama model or update operation")
    ollama_parser.add_argument("--dry-run", action="store_true", help="show Ollama operation without executing it")

    llm_parser = subparsers.add_parser("llm", help="manage LLM backends")
    llm_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    llm_parser.add_argument(
        "action",
        nargs="?",
        default="list",
        choices=["list", "doctor", "configure", "set-default", "default", "enable", "disable", "preference"],
    )
    llm_parser.add_argument("backend", nargs="?")
    llm_parser.add_argument("preference_value", nargs="?")
    llm_parser.add_argument("--api-key-env", help="environment variable that stores the API key")
    llm_parser.add_argument("--base-url", help="OpenAI-compatible base URL")
    llm_parser.add_argument("--model", help="default model id")
    llm_parser.add_argument("--command", dest="host_command", help="host CLI command name or path")
    llm_parser.add_argument("--set-default", action="store_true", help="set backend as the default LLM")
    llm_parser.add_argument("--primary", help="primary backend for LLM preference")
    llm_parser.add_argument("--order", help="comma-separated fallback order")

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
    if args.sessions_shortcut:
        return list_sessions()

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
    if command == "personality":
        return dispatch_personality(args)
    if command == "setup":
        return dispatch_setup(args)
    if command == "alias":
        return dispatch_alias(args)
    if command == "session":
        return dispatch_session(args)
    if command == "toolchain":
        return dispatch_toolchain(args)
    if command == "task":
        return dispatch_task(args)
    if command == "scheduler":
        return dispatch_scheduler(args)
    if command == "calendar":
        return dispatch_calendar(args)
    if command == "pr":
        return dispatch_pr(args)
    if command == "permissions":
        return dispatch_permissions(args)
    if command == "audit":
        return dispatch_audit(args)
    if command == "config":
        return dispatch_config(args)
    if command in {"tools", "integrations", "skills"}:
        return dispatch_control_category(command, args)
    if command == "decisions":
        return dispatch_decisions(args)
    if command == "ollama":
        return dispatch_ollama(args)
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


def maybe_record_cli_audit(args: argparse.Namespace, *, result: dict[str, Any] | None, error: str | None) -> None:
    command = canonical_command(getattr(args, "command", None) or "")
    if command in {"", "audit"} or getattr(args, "version", False):
        return
    try:
        audit = record_audit(command=command, args=vars(args), result=result, error=error)
    except Exception:
        return
    if result is not None:
        result["audit"] = audit


def dispatch_llm(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action != "preference" and args.preference_value:
            raise DevKitError(f"llm {args.action} received an unexpected argument: {args.preference_value}")
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
        if args.action in {"set-default", "default"}:
            if not args.backend:
                raise DevKitError(f"llm {args.action} requires a backend")
            return set_default_backend(args.backend)
        if args.action in {"enable", "disable"}:
            if not args.backend:
                raise DevKitError(f"llm {args.action} requires a backend")
            state = "enabled" if args.action == "enable" else "disabled_by_user"
            return set_decision("llms", args.backend, state, reason=f"llm {args.action} command")
        if args.action == "preference":
            if args.backend in {None, "show"}:
                return llm_preference()
            if args.backend == "set":
                if not args.primary and not args.order:
                    raise DevKitError("llm preference set requires --primary or --order")
                return set_llm_preference(primary=args.primary, order=args.order)
            if args.backend == "reorder":
                order = args.preference_value or args.order
                if not order:
                    raise DevKitError("llm preference reorder requires an order value or --order")
                return set_llm_preference(order=order)
            raise DevKitError("llm preference action must be show, set or reorder")
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported llm action: {args.action}")


def dispatch_config(args: argparse.Namespace) -> dict[str, Any]:
    from cli.aikit.llm import config_path

    if args.action == "path":
        return {"kind": "config", "status": "ok", "path": str(config_path())}
    if args.action == "show":
        return {
            "kind": "config",
            "status": "ok",
            "path": str(config_path()),
            "decisions": list_decisions(),
            "llm": llm_preference(),
            "ollama": ollama_status(),
        }
    raise DevKitError(f"unsupported config action: {args.action}")


def dispatch_control_category(command: str, args: argparse.Namespace) -> dict[str, Any]:
    try:
        category = command
        if args.action == "list":
            if args.item_id:
                raise DevKitError(f"{command} list does not accept an item id")
            payload = list_decisions(category)
            payload["kind"] = command
            return payload
        if args.action in {"enable", "disable"}:
            if not args.item_id:
                raise DevKitError(f"{command} {args.action} requires an item id")
            state = "enabled" if args.action == "enable" else "disabled_by_user"
            payload = set_decision(category, args.item_id, state, reason=f"{command} {args.action} command")
            payload["kind"] = command[:-1] if command.endswith("s") else command
            return payload
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported {command} action: {args.action}")


def dispatch_decisions(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action == "list":
            if args.item_id:
                raise DevKitError("decisions list does not accept an item id")
            return list_decisions(args.category)
        if args.action == "reset":
            if args.item_id:
                raise DevKitError("decisions reset does not accept an item id")
            return reset_decisions(args.category)
        if args.action == "forget":
            if not args.item_id:
                raise DevKitError("decisions forget requires an item id")
            category = args.category or "tools"
            return set_decision(category, args.item_id, "available", reason="decision forgotten")
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported decisions action: {args.action}")


def dispatch_ollama(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action == "status":
            if args.model:
                raise DevKitError("ollama status does not accept a model")
            return ollama_status()
        if args.action == "models":
            if args.model:
                raise DevKitError("ollama models does not accept a model")
            return ollama_models()
        if args.action == "pull":
            return ollama_pull(args.model, yes=args.yes, dry_run=effective_dry_run(args))
        if args.action == "update":
            if args.model:
                raise DevKitError("ollama update does not accept a model")
            return ollama_update(yes=args.yes, dry_run=effective_dry_run(args))
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported ollama action: {args.action}")


def dispatch_install(args: argparse.Namespace) -> dict[str, Any]:
    try:
        return install_runtime(
            ROOT,
            scope=args.scope,
            host=args.host,
            target=Path(args.target) if args.target else None,
            home=Path(args.home) if args.home else None,
            dry_run=effective_dry_run(args),
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
    if args.action == "path":
        return memory_path_payload()
    if args.action == "reset":
        return reset_memory(
            all_memory=args.all,
            agent_id=args.agent_id,
            source_id=args.source_id,
            reset_sessions=args.sessions,
            reset_tasks=args.tasks,
            reset_cache=args.cache,
        )
    raise DevKitError(f"unsupported memory action: {args.action}")


def dispatch_personality(args: argparse.Namespace) -> dict[str, Any]:
    if args.action == "show":
        return load_personality()
    if args.action == "edit":
        if not any([args.agent_name, args.user_name, args.language, args.tone, args.detail_level]):
            payload = load_personality()
            payload["status"] = "needs-input"
            payload["message"] = "Use --name, --user-name, --language, --tone or --detail-level to edit non-interactively."
            return payload
        return update_personality(
            agent_name=args.agent_name,
            user_name=args.user_name,
            language=args.language,
            tone=args.tone,
            detail_level=args.detail_level,
        )
    if args.action == "reset":
        return reset_personality()
    raise DevKitError(f"unsupported personality action: {args.action}")


def dispatch_setup(args: argparse.Namespace) -> dict[str, Any]:
    if args.action == "personality":
        return setup_personality()
    if args.action == "plan":
        return setup_wizard(ROOT, dry_run=effective_dry_run(args), yes=args.yes)
    raise DevKitError(f"unsupported setup action: {args.action}")


def dispatch_toolchain(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action == "list":
            if args.tool != "all":
                raise DevKitError("toolchain list does not accept a tool argument")
            return list_toolchain(ROOT)
        if args.action == "doctor":
            return doctor_toolchain(ROOT, None if args.tool == "all" else args.tool)
        if args.action == "install":
            return install_toolchain(ROOT, None if args.tool == "all" else args.tool, dry_run=effective_dry_run(args), yes=args.yes)
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported toolchain action: {args.action}")


def dispatch_task(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action == "list":
            return list_tasks()
        if args.action == "create":
            schedule = {"type": "manual"}
            if args.every:
                schedule = {"type": "interval", "every": args.every}
            if args.cron:
                schedule = {"type": "cron", "cron": args.cron}
            return create_task(task_id=args.task_id, title=args.title, prompt=args.prompt, schedule=schedule)
        if args.action == "show":
            require_id(args.task_id, "task show")
            return show_task(args.task_id)
        if args.action == "history":
            require_id(args.task_id, "task history")
            return task_history(args.task_id)
        if args.action == "run":
            require_id(args.task_id, "task run")
            return run_task(args.task_id, dry_run=effective_dry_run(args))
        if args.action in {"pause", "disable"}:
            require_id(args.task_id, f"task {args.action}")
            return update_task_status(args.task_id, "paused" if args.action == "pause" else "disabled")
        if args.action in {"resume", "enable"}:
            require_id(args.task_id, f"task {args.action}")
            return update_task_status(args.task_id, "enabled")
        if args.action == "update":
            require_id(args.task_id, "task update")
            return update_task_schedule(args.task_id, every=args.every, cron=args.cron)
        if args.action == "delete":
            require_id(args.task_id, "task delete")
            return delete_task(args.task_id, yes=args.yes)
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported task action: {args.action}")


def dispatch_scheduler(args: argparse.Namespace) -> dict[str, Any]:
    if args.action == "run-once":
        return run_scheduler_once(dry_run=effective_dry_run(args))
    if args.action == "daemon":
        return scheduler_daemon_plan()
    raise DevKitError(f"unsupported scheduler action: {args.action}")


def dispatch_calendar(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action == "configure":
            return configure_calendar(ics_path=args.ics, timezone=args.timezone)
        if args.action == "today":
            return calendar_today()
        if args.action == "tomorrow":
            return calendar_tomorrow()
        if args.action == "list":
            return calendar_list(args.date_from, args.date_to)
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported calendar action: {args.action}")


def dispatch_pr(args: argparse.Namespace) -> dict[str, Any]:
    if args.action == "list-review-requests":
        if effective_dry_run(args):
            return pr_read_dry_run("list-review-requests")
        return pr_list_review_requests()
    if args.action == "inspect":
        require_id(args.pr_ref, "pr inspect")
        if effective_dry_run(args):
            return pr_read_dry_run("inspect", pr_ref=args.pr_ref)
        return pr_inspect(args.pr_ref)
    if args.action == "review":
        require_id(args.pr_ref, "pr review")
        return pr_review(
            args.pr_ref,
            approve=args.approve,
            request_changes=args.request_changes,
            comment=args.comment,
            allow_write=args.allow_write,
            dry_run=effective_dry_run(args),
        )
    if args.action == "automation":
        if args.automation_action not in {None, "create"}:
            raise DevKitError("pr automation action must be create")
        if effective_dry_run(args):
            return pr_automation_dry_run(time=args.time)
        return pr_create_automation(time=args.time)
    raise DevKitError(f"unsupported pr action: {args.action}")


def dispatch_permissions(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action == "show":
            return show_permissions()
        if args.action == "grant":
            if not args.agent or not args.provider or not args.level:
                raise DevKitError("permissions grant requires agent, provider and level")
            return grant_permission(args.agent, args.provider, args.level, project=args.project, task_id=args.task_id)
        if args.action == "revoke":
            if not args.agent or not args.provider:
                raise DevKitError("permissions revoke requires agent and provider")
            return revoke_permission(args.agent, args.provider, args.level, project=args.project, task_id=args.task_id)
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported permissions action: {args.action}")


def dispatch_audit(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action == "list":
            if args.execution_id:
                raise DevKitError("audit list does not accept an execution id")
            return list_audits(limit=max(1, int(args.limit or 20)))
        if args.action == "show":
            require_id(args.execution_id, "audit show")
            return show_audit(args.execution_id)
        if args.action == "export":
            require_id(args.execution_id, "audit export")
            return export_audit(args.execution_id, fmt=args.format)
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported audit action: {args.action}")


def pr_read_dry_run(action: str, *, pr_ref: str | None = None) -> dict[str, Any]:
    return {
        "kind": "pr",
        "status": "planned",
        "ok": True,
        "dry_run": True,
        "mode": "report-only",
        "provider": "github",
        "action": action,
        "pr_ref": pr_ref,
        "commands": planned_pr_commands(action, pr_ref=pr_ref),
        "summary": "Dry-run only. GitHub would be read through gh; no PR write action would be submitted.",
    }


def pr_automation_dry_run(*, time: str) -> dict[str, Any]:
    return {
        "kind": "pr-automation",
        "status": "planned",
        "ok": True,
        "dry_run": True,
        "mode": "report-only",
        "provider": "github",
        "task": {
            "id": "daily-pr-review",
            "title": "Revisar PRs pendentes diariamente",
            "schedule": {"type": "daily", "time": time},
            "action": {
                "type": "capability",
                "agent": "github-pr-reviewer",
                "capability": "list-review-requests",
                "external_writes": False,
            },
            "permissions": {"mode": "report-only", "comment": False, "approve": False, "request_changes": False},
        },
        "summary": "Dry-run only. A local report-only PR review task would be created.",
    }


def planned_pr_commands(action: str, *, pr_ref: str | None = None) -> list[list[str]]:
    if action == "list-review-requests":
        return [["gh", "pr", "list", "--review-requested", "@me", "--json", "number,title,url,author,headRefName,baseRefName,isDraft"]]
    if action == "inspect":
        return [["gh", "pr", "view", str(pr_ref), "--json", "number,title,url,author,body,headRefName,baseRefName,state,isDraft,reviewDecision,mergeable"]]
    return []


def require_id(value: str | None, command: str) -> None:
    if not value:
        raise DevKitError(f"{command} requires an id")


def effective_dry_run(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "dry_run", False) or getattr(args, "global_dry_run", False))


def dispatch_alias(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action == "list":
            if args.name:
                raise DevKitError("alias list does not accept a name")
            return list_aliases()
        if args.action == "add":
            if not args.name:
                raise DevKitError("alias add requires a name")
            return add_alias(args.name, force=args.force)
        if args.action == "remove":
            if not args.name:
                raise DevKitError("alias remove requires a name")
            return remove_alias(args.name)
        if args.action == "sync":
            if args.name:
                raise DevKitError("alias sync does not accept a name")
            return sync_aliases()
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported alias action: {args.action}")


def dispatch_session(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action == "list":
            if args.session_id:
                raise DevKitError("session list does not accept a session id")
            return list_sessions()
        if args.action == "show":
            if not args.session_id:
                raise DevKitError("session show requires a session id")
            return show_session(args.session_id)
        if args.action == "resume":
            if not args.session_id:
                raise DevKitError("session resume requires a session id")
            return resume_session(args.session_id)
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported session action: {args.action}")


def agent_requires_llm(args: argparse.Namespace) -> dict[str, Any]:
    prompt = " ".join(args.prompt).strip()
    if not prompt:
        raise DevKitError("agent requires a natural-language prompt")
    if effective_dry_run(args):
        return build_agent_dry_run_plan(prompt, args)
    try:
        session = get_or_create_session(
            session_id=args.session_id,
            force_new=args.new_session,
            prompt=prompt,
            project=str(Path.cwd()),
            backend=args.llm,
        )
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    personality = load_personality()
    name = public_name(personality=personality, invoked_as=getattr(args, "prog_name", "agent"))
    if is_identity_question(prompt):
        result = {
            "kind": "agent",
            "status": "ok",
            "ok": True,
            "requires_llm": False,
            "prompt_received": True,
            "prompt_length": len(prompt),
            "identity": {"name": name, "source": "local"},
            "response": local_identity_response(prompt, name=name),
        }
        return finalize_agent_session(result, session, prompt, backend=args.llm)
    natural_result = dispatch_natural_operational_prompt(prompt)
    if natural_result:
        return finalize_agent_session(natural_result, session, prompt, backend=args.llm)
    route = route_prompt(prompt)
    if route:
        result = invoke_deterministic_route(prompt, route)
        return finalize_agent_session(result, session, prompt, backend=args.llm)
    contextual_prompt = build_contextual_prompt(str(session["id"]), prompt)
    model_plan = build_model_plan(prompt)
    result = invoke_agent_prompt(
        contextual_prompt,
        args.llm,
        public_name=name,
        allow_fallback=not args.no_llm_fallback,
    )
    review_gate = build_review_gate(prompt, model_plan=model_plan)
    if result.get("ok"):
        review_gate = mark_reviewed(review_gate, reviewer=str(result.get("llm_backend") or "coordinator"))
    result["model_plan"] = model_plan
    result["review_gate"] = review_gate
    result["prompt_length"] = len(prompt)
    result["session_context_applied"] = contextual_prompt != prompt
    if result.get("response"):
        result["response"] = enforce_identity_response(str(result["response"]), prompt, name=name)
    result["identity"] = {"name": name, "source": "local"}
    return finalize_agent_session(result, session, prompt, backend=result.get("llm_backend") or args.llm)


def dispatch_natural_operational_prompt(prompt: str) -> dict[str, Any] | None:
    normalized = " ".join(prompt.lower().split())
    control_result = dispatch_natural_control_prompt(normalized)
    if control_result:
        control_result["prompt_received"] = True
        control_result["prompt_length"] = len(prompt)
        return control_result
    if "agenda" in normalized:
        if "amanha" in normalized or "amanhã" in normalized:
            payload = calendar_tomorrow()
        else:
            payload = calendar_today()
        payload = dict(payload)
        payload["kind"] = "agent"
        payload["mode"] = "calendar-route"
        payload["requires_llm"] = False
        payload["prompt_received"] = True
        payload["prompt_length"] = len(prompt)
        payload["response"] = calendar_summary(payload)
        if payload.get("status") == "needs-input":
            payload["ok"] = False
        else:
            payload["ok"] = True
        return payload
    if has_pr_intent(normalized):
        if any(marker in normalized for marker in ("diariamente", "todo dia", "diaria", "diária", "recorrente")):
            payload = pr_create_automation()
            return {
                "kind": "agent",
                "status": payload.get("status"),
                "ok": True,
                "mode": "pr-automation-route",
                "requires_llm": False,
                "prompt_received": True,
                "prompt_length": len(prompt),
                "response": "Automacao diaria de revisao de PRs criada em modo report-only.",
                "result": payload,
            }
        payload = pr_list_review_requests()
        return {
            "kind": "agent",
            "status": payload.get("status"),
            "ok": payload.get("status") == "ok",
            "mode": "pr-route",
            "requires_llm": False,
            "prompt_received": True,
            "prompt_length": len(prompt),
            "response": summarize_pr_list(payload),
            "result": payload,
            "exit_code": payload.get("exit_code", 0 if payload.get("status") == "ok" else 2),
        }
    return None


def dispatch_natural_control_prompt(normalized_prompt: str) -> dict[str, Any] | None:
    if "decis" in normalized_prompt and any(marker in normalized_prompt for marker in ("mostre", "liste", "ver", "mostrar", "listar")):
        return {
            "kind": "agent",
            "status": "ok",
            "ok": True,
            "mode": "control-center-route",
            "requires_llm": False,
            "response": "Estas sao as decisoes locais registradas.",
            "result": list_decisions(),
        }
    control_targets = {
        "ollama": ("tools", "ollama"),
        "azure devops": ("tools", "azure-devops"),
        "azure": ("tools", "azure-devops"),
        "github": ("integrations", "github"),
        "figma": ("tools", "figma"),
    }
    action: str | None = None
    if any(marker in normalized_prompt for marker in ("desative", "desabilite", "disable", "bloqueie")):
        action = "disable"
    if any(marker in normalized_prompt for marker in ("reative", "ative", "habilite", "enable")):
        action = "enable"
    if not action:
        return None
    for marker, (category, item_id) in control_targets.items():
        if marker in normalized_prompt:
            state = "enabled" if action == "enable" else "disabled_by_user"
            result = set_decision(category, item_id, state, reason=f"natural prompt: {action}")
            return {
                "kind": "agent",
                "status": "ok",
                "ok": True,
                "mode": "control-center-route",
                "requires_llm": False,
                "response": f"{item_id} foi {'ativado' if state == 'enabled' else 'desativado'} para {category}.",
                "result": {
                    "category": category,
                    "id": item_id,
                    "state": state,
                    "decision": result.get("item"),
                },
            }
    if any(marker in normalized_prompt for marker in ("ferramentas", "tools")) and any(
        marker in normalized_prompt for marker in ("mostre", "liste", "ver", "mostrar", "listar")
    ):
        return {
            "kind": "agent",
            "status": "ok",
            "ok": True,
            "mode": "control-center-route",
            "requires_llm": False,
            "response": "Estas sao as ferramentas com decisoes locais registradas.",
            "result": list_decisions("tools"),
        }
    return None


def build_agent_dry_run_plan(prompt: str, args: argparse.Namespace) -> dict[str, Any]:
    normalized = " ".join(prompt.lower().split())
    route = route_prompt(prompt)
    model_plan = build_model_plan(prompt, route=route)
    review_gate = build_review_gate(prompt, route=route, model_plan=model_plan)
    plan: dict[str, Any] = {
        "kind": "agent",
        "status": "planned",
        "ok": True,
        "dry_run": True,
        "requires_llm": False,
        "prompt_received": True,
        "prompt_length": len(prompt),
        "mode": "dry-run",
        "intent": "llm" if not route else route.get("intent"),
        "route": route,
        "llm_backend": getattr(args, "llm", None),
        "external_writes": False,
        "providers": {"used": [], "missing": [], "skipped": []},
        "commands": [],
        "permissions": [],
        "model_plan": model_plan,
        "review_gate": review_gate,
        "response": "Dry-run: nenhuma chamada LLM ou escrita externa foi executada.",
    }
    if "agenda" in normalized:
        plan.update(
            {
                "intent": "calendar",
                "mode": "calendar-dry-run",
                "providers": {"used": ["calendar"], "missing": [], "skipped": []},
                "data_reads": ["configured calendar provider, if present"],
                "response": "Dry-run: o calendario seria consultado localmente se configurado.",
            }
        )
        return plan
    if has_pr_intent(normalized):
        recurring = any(marker in normalized for marker in ("diariamente", "todo dia", "diaria", "diária", "recorrente"))
        plan.update(
            {
                "intent": "github-pr-review",
                "mode": "pr-dry-run",
                "providers": {"used": ["github"], "missing": [], "skipped": []},
                "commands": planned_pr_commands("list-review-requests"),
                "external_writes": False,
                "permissions": [{"agent": "github-pr-reviewer", "provider": "github", "required_level": "read-only"}],
                "response": (
                    "Dry-run: a automacao diaria de PR seria planejada em modo report-only."
                    if recurring
                    else "Dry-run: PRs aguardando revisao seriam listadas via gh em modo report-only."
                ),
            }
        )
        return plan
    if route:
        plan["providers"] = {"used": [route.get("provider")], "missing": [], "skipped": []}
        plan["response"] = "Dry-run: a capability roteada seria executada somente apos validar source/provider."
        return plan
    plan["response"] = "Dry-run: o prompt exigiria LLM configurada; nenhuma chamada foi feita."
    return plan


def has_pr_intent(normalized_prompt: str) -> bool:
    tokens = {token.strip(".,;:!?()[]{}\"'") for token in normalized_prompt.split()}
    return bool({"pr", "prs"} & tokens) or "pull request" in normalized_prompt or "pull requests" in normalized_prompt


def summarize_pr_list(payload: dict[str, Any]) -> str:
    if payload.get("status") != "ok":
        return str(payload.get("message") or "Nao foi possivel listar PRs.")
    items = payload.get("items") or []
    if not items:
        return "Nenhuma PR aguardando sua revisao foi encontrada."
    lines = []
    for item in items:
        number = item.get("number")
        title = item.get("title") or "-"
        url = item.get("url") or ""
        lines.append(f"- #{number} {title} {url}".strip())
    return "\n".join(lines)


def finalize_agent_session(
    result: dict[str, Any],
    session: dict[str, Any],
    prompt: str,
    *,
    backend: str | None = None,
) -> dict[str, Any]:
    try:
        result["session"] = record_exchange(str(session["id"]), prompt=prompt, result=result, backend=backend)
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    return result


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
        wizard = missing_source_wizard(prompt, route, root=ROOT)
        return {
            "kind": "agent",
            "status": "needs-input",
            "ok": False,
            "requires_source": True,
            "provider": route.get("provider"),
            "source_provider": route.get("provider"),
            "prompt_received": True,
            "prompt_length": len(prompt),
            "route": route,
            "napkin": napkin_context(ROOT, agent_id=route.get("agent_id")),
            "setup_wizard": wizard,
            "next_question": wizard.get("next_question"),
            "message": wizard.get("message"),
            "next_steps": [
                "Responda a pergunta do wizard para autorizar ou negar a configuracao desta fonte.",
                "Se preferir teste local, configure uma source com fixture sem armazenar segredos.",
                "O prompt original sera retomado apos a fonte reutilizavel ser configurada.",
            ],
            "exit_code": 2,
        }

    agent = load_agent(str(route["agent_id"]))
    capability_args = [*route.get("args", []), "--source", str(source["id"])]
    result = run_capability(agent, str(route["capability_id"]), capability_args, capture_output=True)
    response = result.get("stdout") or result.get("error") or ""
    record_usage(prompt, route=route, source_id=str(source["id"]))
    model_plan = build_model_plan(prompt, route=route)
    review_gate = build_review_gate(prompt, route=route, model_plan=model_plan)
    if result.get("ok"):
        review_gate = mark_reviewed(review_gate, reviewer="deterministic-coordinator")
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
        "model_plan": model_plan,
        "review_gate": review_gate,
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
    readiness = evaluate_provider_requirements(ROOT, data, capability_args)
    if not readiness["ready"]:
        payload = run_payload(
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
        wizard = setup_wizard_from_readiness(readiness, agent=summarize_agent(agent), capability_id=str(data.get("id", capability_id)))
        if wizard:
            payload["setup_wizard"] = wizard
            payload["next_question"] = wizard.get("next_question")
            payload["configuration_agent"] = wizard.get("owner_agent")
            payload["next_steps"] = [
                "Responda a pergunta do wizard para autorizar ou negar a configuracao deste provider.",
                "Informe uma referencia segura de credencial por variavel de ambiente, arquivo ou cadeia nativa quando solicitado.",
                "Reexecute ou retome a mesma capability depois que a configuracao estiver salva.",
            ]
        return payload

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


def setup_wizard_from_readiness(readiness: dict[str, Any], *, agent: dict[str, Any], capability_id: str) -> dict[str, Any] | None:
    providers = readiness.get("providers") if isinstance(readiness.get("providers"), dict) else {}
    missing = providers.get("missing") or []
    if not missing:
        return None
    provider_id = str(missing[0])
    details = providers.get("details") or []
    detail = next((item for item in details if isinstance(item, dict) and item.get("id") == provider_id), {})
    try:
        return provider_wizard_from_requirement(
            ROOT,
            provider_id,
            agent_id=str(agent.get("id") or ""),
            capability_id=capability_id,
            reason=str(detail.get("purpose") or "Provider is required but not configured."),
        )
    except Exception:
        return None


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
    elif kind == "llm-preference":
        print_llm_preference(result)
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
    elif kind == "memory-path":
        print_memory_path(result)
    elif kind == "memory-reset":
        print_memory_reset(result)
    elif kind == "personality":
        print_personality(result)
    elif kind == "aliases":
        print_aliases(result)
    elif kind == "alias":
        print_alias(result)
    elif kind == "sessions":
        print_sessions(result)
    elif kind == "session":
        print_session(result)
    elif kind == "setup":
        print_setup(result)
    elif kind == "toolchain":
        print_toolchain(result)
    elif kind == "toolchain-doctor":
        print_toolchain_doctor(result)
    elif kind == "toolchain-install":
        print_toolchain_install(result)
    elif kind == "tasks":
        print_tasks(result)
    elif kind == "task":
        print_task(result)
    elif kind == "task-history":
        print_task_history(result)
    elif kind == "task-run":
        print_task_run(result)
    elif kind == "scheduler":
        print_scheduler(result)
    elif kind == "calendar":
        print_calendar(result)
    elif kind == "calendar-configure":
        print_calendar_configure(result)
    elif kind in {"pr", "pr-review", "pr-automation"}:
        print_pr(result)
    elif kind == "permissions":
        print_permissions(result)
    elif kind in {"audit", "audit-entry", "audit-export"}:
        print_audit(result)
    elif kind == "config":
        print_config(result)
    elif kind in {"tools", "tool", "integrations", "integration", "skills", "skill", "decisions", "decision", "decisions-reset"}:
        print_control(result)
    elif kind in {"ollama-status", "ollama-models", "ollama-pull", "ollama-update"}:
        print_ollama(result)
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
    question = result.get("next_question") or ((result.get("setup_wizard") or {}).get("next_question") if isinstance(result.get("setup_wizard"), dict) else None)
    if isinstance(question, dict) and question.get("text"):
        print(f"\nPergunta: {question['text']}")
        if question.get("type") == "confirm":
            print("[s/N]")
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
    if result.get("files"):
        print("\nFiles:")
        for item in result["files"]:
            print(f"- {item['name']}: {item['path']}")
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


def print_memory_path(result: dict[str, Any]) -> None:
    print(f"Memory home: {result['home']}")
    if result.get("created"):
        print("Created:")
        for path in result["created"]:
            print(f"- {path}")
    print("Files:")
    for item in result["files"]:
        print(f"- {item['name']}: {item['path']}")


def print_personality(result: dict[str, Any]) -> None:
    print(f"Personality: {result.get('status', 'ok')}")
    print(f"Path: {result['path']}")
    print(f"Agent name: {result.get('agent_name') or '-'}")
    print(f"User name: {result.get('user_name') or '-'}")
    print(f"Language: {result.get('language') or '-'}")
    print(f"Tone: {result.get('tone') or '-'}")
    print(f"Detail level: {result.get('detail_level') or '-'}")
    if result.get("message"):
        print(result["message"])
    if result.get("questions"):
        print("Setup questions:")
        for question in result["questions"]:
            print(f"- {question}")


def print_aliases(result: dict[str, Any]) -> None:
    print(f"Aliases config: {result['config_path']}")
    if not result["items"]:
        print("No aliases configured.")
        return
    for item in result["items"]:
        print(f"- {item['name']}: {item['path']}")


def print_alias(result: dict[str, Any]) -> None:
    print(f"Alias {result['status']}: {result['name']}")
    if result.get("path"):
        print(f"Path: {result['path']}")
    if result.get("removed_paths"):
        print("Removed:")
        for path in result["removed_paths"]:
            print(f"- {path}")
    print(f"Config: {result['config_path']}")


def print_sessions(result: dict[str, Any]) -> None:
    print(f"Sessions home: {result['home']}")
    if result.get("active_session_id"):
        print(f"Active: {result['active_session_id']}")
    if not result["items"]:
        print("No sessions found.")
        return
    for item in result["items"]:
        marker = " active" if item.get("active") else ""
        print(
            f"- {item['id']}{marker}  {item.get('title') or '-'}  "
            f"{item.get('exchange_count', 0)} exchanges  ~{item.get('token_estimate', 0)} tokens"
        )
        if item.get("project"):
            print(f"  Project: {item['project']}")


def print_session(result: dict[str, Any]) -> None:
    session = result["session"]
    print(f"Session {result['status']}: {session['id']}")
    print(f"Title: {session.get('title') or '-'}")
    print(f"Path: {session.get('path') or '-'}")
    print(f"Project: {session.get('project') or '-'}")
    print(f"Exchanges: {session.get('exchange_count', 0)}")
    print(f"Token estimate: {session.get('token_estimate', 0)}")


def print_setup(result: dict[str, Any]) -> None:
    print(f"Setup: {result['status']}")
    print(f"Dry-run: {result.get('dry_run', False)}")
    toolchain = result.get("toolchain") or {}
    print(f"Toolchain: {toolchain.get('status', '-')}")
    missing = (toolchain.get("required_missing") or []) + (toolchain.get("optional_missing") or [])
    if missing:
        print(f"Missing: {', '.join(missing)}")
    if result.get("next_steps"):
        print("Next steps:")
        for step in result["next_steps"]:
            print(f"- {step}")


def print_toolchain(result: dict[str, Any]) -> None:
    print(f"Toolchain: {result['status']}")
    print(f"Platform: {result['platform']}")
    for item in result["items"]:
        print(f"- {item['id']}  {item['command']}  required={item['required']}")


def print_toolchain_doctor(result: dict[str, Any]) -> None:
    print(f"Toolchain doctor: {result['status']}")
    print(f"Platform: {result['platform']}")
    for item in result["items"]:
        print(f"- {item['id']}: {item['status']}")
        if item.get("binary"):
            print(f"  {item['binary']}")
        if item.get("install"):
            print(f"  Install: {item['install']}")


def print_toolchain_install(result: dict[str, Any]) -> None:
    print(f"Toolchain install: {result['status']}")
    if result.get("message"):
        print(result["message"])
    for plan in result["plans"]:
        print(f"- {plan['id']}: {plan.get('command') or '-'}")


def print_tasks(result: dict[str, Any]) -> None:
    print(f"Tasks: {len(result['items'])}")
    for item in result["items"]:
        print(f"- {item['id']}  {item['status']}  {item.get('title') or '-'}")


def print_task(result: dict[str, Any]) -> None:
    if result.get("message"):
        print(result["message"])
    task = result.get("task") or {}
    if task:
        print(f"Task {result['status']}: {task.get('id')}")
        print(f"Title: {task.get('title') or '-'}")
        print(f"Status: {task.get('status') or '-'}")


def print_task_history(result: dict[str, Any]) -> None:
    print(result.get("history") or "No history.")


def print_task_run(result: dict[str, Any]) -> None:
    print(f"Task run: {result['status']}")
    if result.get("message"):
        print(result["message"])


def print_scheduler(result: dict[str, Any]) -> None:
    print(f"Scheduler: {result['status']}")
    if result.get("message"):
        print(result["message"])
    if "due_count" in result:
        print(f"Due tasks: {result['due_count']}")


def print_calendar(result: dict[str, Any]) -> None:
    if result.get("status") != "ok":
        print(result.get("message") or "Calendar is not available.")
        for step in result.get("next_steps") or []:
            print(f"- {step}")
        return
    print(calendar_summary(result))


def print_calendar_configure(result: dict[str, Any]) -> None:
    print(f"Calendar configured: {result['provider']}")
    print(f"Source: {result['source_ref']}")
    print("Stored secret: no")


def print_pr(result: dict[str, Any]) -> None:
    if result.get("message"):
        print(result["message"])
    if result.get("items") is not None:
        print(summarize_pr_list(result))
    elif result.get("summary"):
        print(result["summary"])
    elif result.get("task"):
        task = result["task"]
        print(f"PR automation {result['status']}: {task.get('id')}")


def print_permissions(result: dict[str, Any]) -> None:
    print(f"Permissions: {result['status']}")
    if result.get("default_level"):
        print(f"Default: {result['default_level']}")
    if result.get("grant"):
        grant = result["grant"]
        print(f"Grant: {grant.get('agent')} / {grant.get('provider')} -> {grant.get('level')}")
    if result.get("removed") is not None:
        print(f"Removed: {len(result.get('removed') or [])}")
    grants = result.get("grants")
    if grants is not None:
        if not grants:
            print("No explicit grants.")
        for grant in grants:
            print(f"- {grant.get('agent')} / {grant.get('provider')} -> {grant.get('level')}")
    if result.get("json_path"):
        print(f"Policy: {result['json_path']}")


def print_audit(result: dict[str, Any]) -> None:
    if result["kind"] == "audit":
        print(f"Audit home: {result['home']}")
        for item in result.get("items") or []:
            print(f"- {item.get('id')}  {item.get('created_at')}  {item.get('command')}  {item.get('status')}")
        return
    if result["kind"] == "audit-entry":
        entry = result.get("entry") or {}
        print(f"Audit: {entry.get('id')}")
        print(f"Created: {entry.get('created_at')}")
        print(f"Command: {entry.get('command')}")
        print(f"Status: {(entry.get('result') or {}).get('status')}")
        print(f"JSON: {result.get('json_path')}")
        print(f"Markdown: {result.get('markdown_path')}")
        return
    print(result.get("content") or "")


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


def print_llm_preference(result: dict[str, Any]) -> None:
    print(f"LLM preference: {result.get('status', 'ok')}")
    print(f"Primary: {result.get('primary') or '-'}")
    print(f"Fallback enabled: {result.get('fallback_enabled', True)}")
    print("Order:")
    for backend_id in result.get("order") or []:
        print(f"- {backend_id}")
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


def print_config(result: dict[str, Any]) -> None:
    print(f"Config: {result.get('path')}")
    if result.get("llm"):
        print(f"Primary LLM: {(result['llm'] or {}).get('primary') or '-'}")
    if result.get("ollama"):
        print(f"Ollama: {(result['ollama'] or {}).get('status')}")


def print_control(result: dict[str, Any]) -> None:
    kind = result.get("kind")
    if kind == "decisions-reset":
        print(f"Decisions reset: {result.get('category') or 'all'}")
        print(f"Path: {result.get('path')}")
        return
    if "items" in result:
        print(f"{kind}:")
        for item in result.get("items") or []:
            print(f"- {item.get('category')}:{item.get('id')}  {item.get('state')}")
        if not result.get("items"):
            print("- none")
        return
    item = result.get("item") or result
    print(f"{item.get('category') or result.get('category')}:{item.get('id') or result.get('id')}  {item.get('state') or result.get('state')}")


def print_ollama(result: dict[str, Any]) -> None:
    kind = result.get("kind")
    if kind == "ollama-status":
        print(f"Ollama: {result.get('status')}")
        print(f"Binary: {result.get('binary') or '-'}")
        print(f"Version: {result.get('version') or '-'}")
        daemon = result.get("daemon") or {}
        print(f"Daemon: {daemon.get('status') or '-'}")
        print(f"Models: {result.get('model_count', 0)}")
        if result.get("install_plan"):
            print(f"Install: {(result['install_plan'] or {}).get('command')}")
        return
    if kind == "ollama-models":
        print(f"Ollama models: {result.get('status')}")
        for item in result.get("items") or []:
            print(f"- {item.get('name')}  {item.get('size') or '-'}")
        if not result.get("items"):
            print("- none")
        return
    print(f"{kind}: {result.get('status')}")
    if result.get("command"):
        command = result["command"]
        print("Command: " + (" ".join(command) if isinstance(command, list) else str(command)))
    if result.get("message"):
        print(result["message"])


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
