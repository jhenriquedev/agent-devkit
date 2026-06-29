"""Command dispatchers for the Agent DevKit CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from cli.aikit import __version__
from cli.aikit.aliases import add_alias, list_aliases, remove_alias, sync_aliases
from cli.aikit.app_home import app_home_status, migrate_default_home
from cli.aikit.architecture import architecture_contract
from cli.aikit.audit import export_audit, list_audits, record_audit, show_audit, try_record_audit
from cli.aikit.calendar import calendar_list, calendar_today, calendar_tomorrow, configure_calendar
from cli.aikit.cli_parser import DETERMINISTIC_COMMANDS, LLM_COMMANDS
from cli.aikit.core.requests import AgentPromptRequest, CapabilityRunRequest
from cli.aikit.core.runtime import (
    inspect_capability_request,
    list_agent_modules,
    list_capability_modules,
    run_agent_prompt,
    run_capability_request,
)
from cli.aikit.credentials import CredentialResolverError, credential_backends
from cli.aikit.decision_store import forget_decision, list_decisions, reset_decisions, set_decision
from cli.aikit.doctor_runtime import doctor
from cli.aikit.errors import DevKitError
from cli.aikit.github_pr import planned_pr_commands, pr_create_automation, pr_inspect, pr_list_review_requests, pr_review
from cli.aikit.install import InstallError, install_runtime
from cli.aikit.llm import (
    configure_backend,
    doctor_backends,
    list_backends,
    llm_preference,
    set_default_backend,
    set_llm_preference,
)
from cli.aikit.lock import parse_profiles
from cli.aikit.memory import memory_path_payload, reset_memory, show_memory
from cli.aikit.mcp_manifest import mcp_doctor, mcp_manifest, mcp_tools_payload
from cli.aikit.mcp_server import serve_mcp_stdio
from cli.aikit.mini_brain import setup_mini_brain
from cli.aikit.notifications import (
    configure_notification_channel,
    configure_notifications,
    format_notification_event,
    list_notification_channels,
    list_notification_events,
    notification_doctor,
    send_notification_command,
)
from cli.aikit.ollama import ollama_models, ollama_pull, ollama_status, ollama_update
from cli.aikit.permissions import grant_permission, revoke_permission, show_permissions
from cli.aikit.personality import load_personality, reset_personality, setup_personality, update_personality
from cli.aikit.providers import (
    ProviderRegistryError,
    configure_provider,
    credential_resolution,
    list_providers,
    provider_status_with_credentials,
    unset_provider_config,
)
from cli.aikit.runtime_paths import ROOT
from cli.aikit.scheduler import run_scheduler_once, scheduler_daemon_plan
from cli.aikit.sessions import list_sessions, resume_session, show_session
from cli.aikit.setup_wizard import setup_wizard
from cli.aikit.sources import SourceConfigBlockedError, SourceRegistryError, add_source, list_sources, remove_source, source_status
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
from cli.aikit.wizard_state import WizardStateError, answer_wizard, cancel_wizard, list_wizards, show_wizard
from cli.aikit.interactive_wizard import resume_agent_prompt


def dispatch(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.version:
        return {"kind": "version", "program": getattr(args, "prog_name", "aikit"), "version": __version__}
    if args.sessions_shortcut:
        return list_sessions()

    if not args.command:
        raise DevKitError("missing command. Use --help for usage.")

    command = canonical_command(args.command)
    if command == "agent":
        return run_agent_prompt(agent_prompt_request_from_args(args))
    if command == "commands":
        return list_command_modes()
    if command == "architecture":
        return architecture_contract(ROOT)
    if command == "providers":
        return dispatch_providers(args)
    if command == "provider":
        return dispatch_provider(args)
    if command == "credential":
        return dispatch_credential(args)
    if command == "source":
        return dispatch_source(args)
    if command == "wizard":
        return dispatch_wizard(args)
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
    if command == "notifications":
        return dispatch_notifications(args)
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
    if command == "mcp":
        return dispatch_mcp(args)
    if command == "llm":
        return dispatch_llm(args)
    if command == "install":
        return dispatch_install(args)
    if command == "agents":
        return list_agent_modules()
    if command == "capabilities":
        return list_capability_modules(capabilities_agent_from_args(args))
    if command == "inspect":
        return inspect_capability_request(args.agent, args.capability)
    if command == "run":
        return run_capability_request(
            CapabilityRunRequest(
                agent_id=args.agent,
                capability_id=args.capability,
                capability_args=list(args.capability_args),
                capture_output=args.json,
                origin="cli",
                dry_run=effective_dry_run(args),
            )
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


def agent_prompt_request_from_args(args: argparse.Namespace) -> AgentPromptRequest:
    return AgentPromptRequest(
        prompt=" ".join(args.prompt).strip(),
        llm=args.llm,
        dry_run=effective_dry_run(args),
        session_id=args.session_id,
        new_session=args.new_session,
        no_llm_fallback=args.no_llm_fallback,
        prog_name=getattr(args, "prog_name", "agent"),
        project=str(Path.cwd()),
    )


def capabilities_agent_from_args(args: argparse.Namespace) -> str | None:
    if args.agent:
        return args.agent
    action_or_agent = args.action_or_agent
    if action_or_agent == "list":
        return args.legacy_agent
    if args.legacy_agent:
        raise DevKitError("unexpected extra argument for capabilities")
    return action_or_agent


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


def maybe_record_cli_audit(args: argparse.Namespace, *, result: dict[str, Any] | None, error: str | None) -> dict[str, Any] | None:
    command = canonical_command(getattr(args, "command", None) or "")
    if command in {"", "audit"} or getattr(args, "version", False):
        return None
    audit_result = try_record_audit(
        command=command,
        args=vars(args),
        result=result,
        error=error,
        origin="cli",
        required=False,
        recorder=record_audit,
    )
    warning = audit_result.get("audit_warning")
    if warning:
        if result is not None:
            result["audit_warning"] = warning
            add_payload_warning(result, warning)
        return warning
    audit = audit_result.get("audit")
    if result is not None:
        result["audit"] = audit
    return audit


def is_audit_warning(value: object) -> bool:
    return isinstance(value, dict) and value.get("kind") == "audit-warning"


def format_audit_warning(warning: dict[str, object]) -> str:
    reason = str(warning.get("reason") or "").strip()
    suffix = f" ({reason})" if reason else ""
    return f"warning: {warning.get('message') or 'Audit trail could not be written.'}{suffix}"


def add_payload_warning(result: dict[str, Any], warning: dict[str, Any]) -> None:
    warnings = result.get("warnings")
    if isinstance(warnings, list):
        warnings.append(warning)
    elif warnings:
        result["warnings"] = [warnings, warning]
    else:
        result["warnings"] = [warning]


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
        return {"kind": "config", "status": "ok", "path": str(config_path()), "home": app_home_status()}
    if args.action == "migrate-home":
        return migrate_default_home(dry_run=effective_dry_run(args))
    if args.action == "show":
        return {
            "kind": "config",
            "status": "ok",
            "path": str(config_path()),
            "home": app_home_status(),
            "decisions": list_decisions(),
            "llm": llm_preference(),
            "ollama": ollama_status(),
        }
    raise DevKitError(f"unsupported config action: {args.action}")


def dispatch_mcp(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.action == "manifest":
        return mcp_manifest()
    if args.action == "tools":
        return mcp_tools_payload()
    if args.action == "doctor":
        return mcp_doctor()
    if args.action == "serve":
        serve_mcp_stdio()
        return None
    raise DevKitError(f"unsupported mcp action: {args.action}")


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
            return forget_decision(category, args.item_id)
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
    except SourceConfigBlockedError as exc:
        return exc.payload
    except SourceRegistryError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported source action: {args.action}")


def dispatch_wizard(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action == "list":
            return list_wizards(status=args.status)
        if args.action == "show":
            require_id(args.wizard_id, "wizard show")
            return show_wizard(args.wizard_id)
        if args.action == "cancel":
            require_id(args.wizard_id, "wizard cancel")
            return cancel_wizard(args.wizard_id)
        if args.action == "answer":
            require_id(args.wizard_id, "wizard answer")
            answer = " ".join(args.answer or []).strip()
            if not answer:
                raise DevKitError("wizard answer requires an answer")
            payload = answer_wizard(args.wizard_id, answer)
            if payload.get("status") == "completed" and not args.no_run:
                resume_prompt = payload.get("resume_prompt") or (payload.get("wizard") or {}).get("resume_prompt")
                if resume_prompt:
                    payload["resumed_prompt"] = True
                    payload["resume_result"] = resume_agent_prompt(str(resume_prompt))
                else:
                    payload["resumed_prompt"] = False
            else:
                payload.setdefault("resumed_prompt", False)
            return payload
    except WizardStateError as exc:
        raise DevKitError(str(exc)) from exc
    except SourceRegistryError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported wizard action: {args.action}")



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
    if args.action == "mini-brain":
        return setup_mini_brain(
            dry_run=effective_dry_run(args),
            yes=args.yes,
            set_default=args.set_default,
        )
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


def dispatch_notifications(args: argparse.Namespace) -> dict[str, Any]:
    try:
        if args.action == "doctor":
            return notification_doctor()
        if args.action == "list-events":
            return list_notification_events()
        if args.action == "list-channels":
            return list_notification_channels()
        if args.action == "configure":
            enabled = None
            if args.enabled is not None:
                enabled = args.enabled.lower() == "true"
            return configure_notifications(enabled=enabled, events=args.event_filter or None)
        if args.action == "configure-channel":
            enabled = None
            if args.enabled is not None:
                enabled = args.enabled.lower() == "true"
            channel = args.channel[0] if args.channel else "desktop"
            return configure_notification_channel(channel, enabled=enabled, events=args.event_filter or None)
        if args.action == "format":
            return format_notification_event(notification_payload_from_args(args))
        if args.action == "send":
            if not args.message:
                raise DevKitError("notifications send requires --message")
            return send_notification_command(
                title=args.title,
                message=args.message,
                event=args.event,
                status=args.status,
                summary=args.summary,
                severity=args.severity,
                task_id=args.task_id,
                origin=args.origin,
                artifacts=args.artifact,
                next_steps=args.next_step,
                sensitive=args.sensitive,
                channels=args.channel or None,
            )
    except ValueError as exc:
        raise DevKitError(str(exc)) from exc
    raise DevKitError(f"unsupported notifications action: {args.action}")


def notification_payload_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "event": args.event,
        "status": args.status,
        "title": args.title,
        "message": args.message,
        "summary": args.summary,
        "severity": args.severity,
        "task_id": args.task_id,
        "origin": args.origin,
        "artifacts": args.artifact,
        "next_steps": args.next_step,
        "sensitive": args.sensitive,
    }


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
