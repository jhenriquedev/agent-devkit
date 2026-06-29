"""Human-readable rendering for Agent DevKit CLI payloads."""

from __future__ import annotations

import json
from typing import Any

from cli.aikit.calendar import calendar_summary
from cli.aikit.github_pr import summarize_pr_list


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
    elif kind in {"onboarding", "onboarding-plan"}:
        print_onboarding(result)
    elif kind == "architecture":
        print_architecture(result)
    elif kind == "roadmap":
        print_roadmap(result)
    elif kind in {"catalog", "catalog-item", "catalog-index"}:
        print_catalog(result)
    elif kind == "agentic-plan":
        print_agentic_plan(result)
    elif kind == "route-explain":
        print_route_explain(result)
    elif kind in {"eval-suites", "eval-run", "eval-report"}:
        print_eval(result)
    elif kind in {"secrets-doctor", "secret-backends", "secret-references", "secret-reference", "secret-reference-remove"}:
        print_secrets(result)
    elif kind in {"local-extensions", "local-extension", "local-extension-remove", "local-extension-validation"}:
        print_local_extensions(result)
    elif kind in {
        "local-skills",
        "local-skill",
        "local-scripts",
        "local-script",
        "local-script-run",
        "local-agents",
        "local-agent",
        "local-agent-validation",
        "local-automations",
        "local-automation",
        "local-automation-validation",
    }:
        print_local_artifacts(result)
    elif kind in {"workflows", "workflow", "workflow-install", "workflow-run"}:
        print_workflows(result)
    elif kind in {"team", "team-doctor", "team-onboarding", "team-profiles", "team-profile", "team-profile-export", "team-profile-import"}:
        print_team(result)
    elif kind in {"knowledge", "knowledge-doctor", "knowledge-search", "knowledge-index", "knowledge-snapshot", "knowledge-review", "knowledge-publish", "knowledge-base", "knowledge-base-tokens", "knowledge-base-token"}:
        print_knowledge(result)
    elif kind in {"contributions", "contribution-checklist", "contribution-validation", "contribution-prepare", "contribution-review", "contribution-pr"}:
        print_contribution(result)
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
    elif kind in {"wizards", "wizard"}:
        print_wizard(result)
    elif kind in {"shared-memory", "shared-memories", "shared-memory-read", "shared-memory-submission", "shared-memory-review", "shared-memory-publish"}:
        print_shared_memory(result)
    elif kind == "memory":
        print_memory(result)
    elif kind in {"memory-backup", "memory-backups", "memory-backup-restore", "memory-backup-delete"}:
        print_memory_backup(result)
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
    elif kind in {"setup", "mini-brain-setup"}:
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
    elif kind == "notification-event":
        print_notification_event(result)
    elif kind == "notifications":
        print_notifications(result)
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
    elif kind in {"local-llm", "local-llm-doctor", "local-llm-models", "local-llm-install", "local-llm-remove", "local-llm-benchmark"}:
        print_local_llm(result)
    elif kind in {"mcp-manifest", "mcp-tools", "mcp-doctor"}:
        print_mcp(result)
    elif kind == "install":
        print_install(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    print_structured_warnings(result)


def print_agents(items: list[dict[str, Any]]) -> None:
    if not items:
        print("No agents found.")
        return
    for item in items:
        count = item.get("capabilities", 0)
        print(f"{item['id']}  {item.get('status') or '-'}  {count} capabilities")
        if item.get("purpose"):
            print(f"  {item['purpose']}")


def print_roadmap(result: dict[str, Any]) -> None:
    print(f"Agent DevKit roadmap {result.get('version_scope')}: {len(result.get('active_problems') or [])} active problems")
    preteridos = result.get("preteridos") or []
    if preteridos:
        print(f"Out of scope: {', '.join(str(item) for item in preteridos)}")
    for phase in result.get("phases") or []:
        problems = ", ".join(str(item) for item in phase.get("problems") or []) or "-"
        print(f"- {phase.get('number')}: {phase.get('name')} [{problems}]")


def print_catalog(result: dict[str, Any]) -> None:
    if result["kind"] == "catalog-index":
        print(f"Catalog index {result.get('status')}: {result.get('count', 0)} item(s)")
        print(f"Path: {result.get('path')}")
        return
    if result["kind"] == "catalog-item":
        item = result["item"]
        print(f"{item.get('type')} {item.get('id')}")
        if item.get("description"):
            print(item["description"])
        print(f"Path: {item.get('path') or '-'}")
        print(f"Status: {item.get('status') or '-'}")
        return
    print(f"Catalog {result.get('action')}: {result.get('count', 0)} item(s)")
    for item in result.get("items") or []:
        print(f"- {item.get('type')} {item.get('id')}  {item.get('status') or '-'}")


def print_route_explain(result: dict[str, Any]) -> None:
    selected = result.get("selected") or {}
    print(f"Route: {result.get('decision')} ({result.get('confidence_label')})")
    print(f"Selected: {selected.get('agent_id') or '-'} / {selected.get('capability_id') or '-'}")
    print(f"Execution: {result.get('execution')}")
    if result.get("reason"):
        print(result["reason"])
    if result.get("next_step"):
        print(f"Next: {result['next_step']}")


def print_agentic_plan(result: dict[str, Any]) -> None:
    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    print(f"Agentic plan: {result.get('status')}")
    print(f"Routing: {summary.get('routing_status') or '-'}")
    print(f"Selected: {summary.get('selected_agent_id') or '-'} / {summary.get('selected_capability_id') or '-'}")
    print(f"Model: {summary.get('model_strategy') or '-'}")
    print(f"Tasks: {summary.get('specialist_tasks', 0)} specialist, {summary.get('configuration_tasks', 0)} configuration")
    if summary.get("review_required"):
        print("Review: required")
    if summary.get("needs_input"):
        print("Next: provide the missing configuration, route confirmation, or model permission.")


def print_eval(result: dict[str, Any]) -> None:
    if result["kind"] == "eval-suites":
        print("Eval suites:")
        for suite in result.get("suites") or []:
            print(f"- {suite.get('id')}")
        return
    if result["kind"] == "eval-run":
        print(f"Eval {result.get('suite')}: {result.get('status')}")
        for check in result.get("checks") or []:
            print(f"- {check.get('id')}: {check.get('status')}")
        return
    print(result.get("message") or "Eval report")


def print_secrets(result: dict[str, Any]) -> None:
    print(f"{result['kind']}: {result.get('status')}")
    if result.get("backends"):
        for backend in result["backends"]:
            print(f"- {backend.get('id')}: {backend.get('status')}")
    if result.get("references"):
        print(f"References: {len(result['references'])}")


def print_local_extensions(result: dict[str, Any]) -> None:
    print(f"{result['kind']}: {result.get('status')}")
    for item in result.get("items") or []:
        state = "enabled" if item.get("enabled") else "disabled"
        print(f"- {item.get('id')} {state} {item.get('path')}")


def print_local_artifacts(result: dict[str, Any]) -> None:
    kind = result.get("kind")
    print(f"{kind}: {result.get('status')}")
    if "items" in result:
        for item in result.get("items") or []:
            state = "enabled" if item.get("enabled") else "disabled"
            schedule = item.get("schedule") if isinstance(item.get("schedule"), dict) else {}
            schedule_label = schedule.get("type") or ""
            if schedule.get("every"):
                schedule_label = f"{schedule_label}:{schedule.get('every')}"
            if schedule.get("cron"):
                schedule_label = f"{schedule_label}:{schedule.get('cron')}"
            suffix = f" [{schedule_label}]" if schedule_label else ""
            title = f" - {item.get('title')}" if item.get("title") else ""
            print(f"- {item.get('id')} {state}{suffix}{title} {item.get('path')}")
        if not result.get("items"):
            print("- none")
        return
    automation = result.get("automation") if isinstance(result.get("automation"), dict) else None
    if automation:
        print(f"Automation: {automation.get('id')}")
        print(f"Title: {automation.get('title') or '-'}")
        schedule = automation.get("schedule") if isinstance(automation.get("schedule"), dict) else {}
        print(f"Schedule: {schedule.get('type') or 'manual'}")
        print(f"Enabled: {'yes' if automation.get('enabled') is not False else 'no'}")
    if result.get("id"):
        print(f"Id: {result.get('id')}")
    if result.get("path"):
        print(f"Path: {result.get('path')}")
    if result.get("checks"):
        for check in result.get("checks") or []:
            print(f"- {check.get('id')}: {check.get('status')}")
    if result.get("message"):
        print(result["message"])


def print_workflows(result: dict[str, Any]) -> None:
    print(f"{result['kind']}: {result.get('status')}")
    for item in result.get("items") or []:
        print(f"- {item.get('id')}: {item.get('description')}")
    if result.get("workflow"):
        workflow = result["workflow"]
        print(f"{workflow.get('id')}: {workflow.get('description')}")


def print_team(result: dict[str, Any]) -> None:
    print(f"{result['kind']}: {result.get('status')}")
    if result.get("path"):
        print(f"Path: {result.get('path')}")
    if result.get("active_profile"):
        print(f"Active: {result.get('active_profile')}")
    if result.get("profiles"):
        print(f"Profiles: {', '.join(str(item) for item in result.get('profiles') or [])}")
    if result.get("items"):
        for item in result.get("items") or []:
            print(f"- {item.get('id')}: {item.get('description') or '-'}")
    if result.get("profile"):
        profile = result["profile"]
        print(f"Profile: {profile.get('id')}")
        print(f"Workflows: {', '.join(str(item) for item in profile.get('workflows') or []) or '-'}")
    for check in result.get("checks") or []:
        print(f"- {check.get('id')}: {check.get('status')}")
    for step in result.get("next_steps") or []:
        print(f"Next: {step}")


def print_knowledge(result: dict[str, Any]) -> None:
    print(f"{result['kind']}: {result.get('status')}")
    if result.get("path"):
        print(f"Path: {result.get('path')}")
    if result.get("snapshot_id"):
        print(f"Snapshot: {result.get('snapshot_id')}")
    if result.get("count") is not None:
        print(f"Count: {result.get('count')}")
    for item in result.get("items") or []:
        suffix = f" ({item.get('score')})" if item.get("score") is not None else ""
        print(f"- {item.get('path')}{suffix}")
    for check in result.get("checks") or []:
        print(f"- {check.get('id')}: {check.get('status')}")
    for finding in result.get("findings") or []:
        print(f"Finding: {finding.get('reason')} {finding.get('path') or ''}".rstrip())
    for step in result.get("next_steps") or []:
        print(f"Next: {step}")


def print_contribution(result: dict[str, Any]) -> None:
    print(f"{result['kind']}: {result.get('status')}")
    for check in result.get("checks") or []:
        print(f"- {check.get('id')}: {check.get('status')}")


def print_structured_warnings(result: dict[str, Any]) -> None:
    warnings = [
        warning
        for warning in (result.get("warnings") or [])
        if isinstance(warning, dict)
    ]
    audit_warning = result.get("audit_warning")
    if isinstance(audit_warning, dict) and audit_warning not in warnings:
        warnings.insert(0, audit_warning)
    if not warnings:
        return
    print("\nWarnings:")
    for warning in warnings:
        if warning.get("kind") == "audit-warning":
            reason = warning.get("reason")
            suffix = f" Reason: {reason}" if reason else ""
            print(f"- Warning: audit trail was not recorded.{suffix}")
            continue
        message = warning.get("message") or warning.get("code") or "Warning"
        detail = warning.get("error")
        if detail:
            print(f"- {message}: {detail}")
        else:
            print(f"- {message}")


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
        print(f"- {prefix}{short_id}  {format_write_policy(item)}  {item.get('status') or '-'}  {runner}  {workflow}  {rules}")
        if item.get("purpose"):
            print(f"  {item['purpose']}")


def print_capability(result: dict[str, Any]) -> None:
    agent = result["agent"]
    capability = result["capability"]
    print(f"{agent['id']} / {capability['id'].split('.')[-1]}")
    print(f"Status: {capability.get('status') or '-'}")
    print(f"Version: {capability.get('version') or '-'}")
    print(f"Write policy: {format_write_policy(capability)}")
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


def format_write_policy(item: dict[str, Any]) -> str:
    policy = item.get("write_policy") or "-"
    metadata = item.get("write_policy_metadata") if isinstance(item.get("write_policy_metadata"), dict) else {}
    raw = metadata.get("raw") or item.get("write_policy_raw")
    if raw and raw != policy:
        return f"{policy} (raw: {raw})"
    return str(policy)


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
    operational = result.get("operational") or {}
    if operational:
        print("\nOperational:")
        for key, value in operational.items():
            if isinstance(value, dict):
                suffix = f" ({value.get('count')})" if value.get("count") is not None else ""
                print(f"- {key}: {value.get('status', '-')}{suffix}")
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


def print_onboarding(result: dict[str, Any]) -> None:
    if result.get("kind") == "onboarding-plan":
        print_onboarding_plan(result)
        return
    agent = result.get("agent") or {}
    print(f"{agent.get('name') or 'Agent DevKit'}")
    print(f"Status: {result.get('status')}")

    home = result.get("home") or {}
    print(f"Home: {home.get('home')}")

    memory = result.get("memory") or {}
    created = memory.get("created") or []
    memory_suffix = f" ({len(created)} file(s) created)" if created else ""
    print(f"Memoria local: {memory.get('status')}{memory_suffix}")

    sessions = result.get("sessions") or {}
    active = sessions.get("active_session_id") or "-"
    print(f"Sessao ativa: {active} ({sessions.get('count', 0)} total)")

    llm = result.get("llm") or {}
    print(f"LLMs: {llm.get('usable_count', 0)} usable / {llm.get('configured_count', 0)} configured")

    ollama = result.get("ollama") or {}
    print(f"Ollama: {ollama.get('status')} ({ollama.get('model_count', 0)} model(s))")

    toolchain = result.get("toolchain") or {}
    print(
        "Toolchain: "
        f"{toolchain.get('status')} "
        f"({toolchain.get('ok_count', 0)} ok, {toolchain.get('missing_count', 0)} missing)"
    )

    sources = result.get("sources") or {}
    tasks = result.get("tasks") or {}
    specialists = result.get("specialists") or {}
    print(f"Sources: {sources.get('count', 0)} configured")
    if specialists:
        missing = specialists.get("missing_providers") or []
        missing_label = ""
        if missing:
            first_missing = missing[0] if isinstance(missing[0], dict) else {}
            if first_missing.get("id"):
                missing_label = f", first missing: {first_missing['id']}"
        print(
            "Especialistas: "
            f"{specialists.get('ready_agents', 0)} ready / "
            f"{specialists.get('agents_with_provider_requirements', 0)} provider-bound"
            f"{missing_label}"
        )
    print(f"Tasks: {tasks.get('enabled_count', 0)} enabled / {tasks.get('count', 0)} total")
    if tasks.get("due_count"):
        print(f"Due tasks: {tasks.get('due_count')}")

    if result.get("assistant_prompt"):
        print(f"\n{result['assistant_prompt']}")

    blockers = result.get("blockers") or []
    if blockers:
        print("\nNeeds setup:")
        for blocker in blockers:
            print(f"- {blocker.get('message')}")
            if blocker.get("command"):
                print(f"  {blocker['command']}")

    actions = result.get("suggested_actions") or []
    if actions:
        print("\nNext:")
        for action in actions[:8]:
            label = action.get("label") or action.get("id")
            command = action.get("command")
            print(f"- {label}: {command}")

    modes = result.get("onboarding_modes") or []
    if modes:
        print("\nOnboarding:")
        for mode in modes:
            print(f"- {mode.get('label')}: {mode.get('command')}")


def print_onboarding_plan(result: dict[str, Any]) -> None:
    print(f"Onboarding {result.get('mode')}: {result.get('status')}")
    print("External actions executed: no")
    catalog = result.get("agent_catalog") or {}
    print(f"Catalog: {catalog.get('agents', 0)} agents / {catalog.get('capabilities', 0)} capabilities")
    steps = result.get("steps") or []
    if steps:
        print("\nSteps:")
        for step in steps:
            print(f"- {step.get('id')}: {step.get('command')}")


def print_architecture(result: dict[str, Any]) -> None:
    principal = result.get("principal_agent") or {}
    print(f"{principal.get('name', 'Agent DevKit')}: {principal.get('role', 'runtime-agent')}")
    if principal.get("description"):
        print(principal["description"])
    print("\nModel:")
    for key, value in (result.get("model") or {}).items():
        print(f"- {key}: {value}")
    counts = result.get("counts") or {}
    print("\nInventory:")
    print(f"- Runtime agents: {counts.get('runtime_agents', 0)}")
    print(f"- Specialist agents: {counts.get('specialist_agents', 0)}")
    print(f"- Capabilities: {counts.get('capabilities', 0)}")
    print(f"- Executable capabilities: {counts.get('executable_capabilities', 0)}")
    phases = result.get("implementation_phases") or []
    if phases:
        print("\nImplementation phases:")
        for phase in phases:
            print(f"- {phase.get('number')}: {phase.get('name')}")
    acceptance = result.get("acceptance_model") or {}
    sections = acceptance.get("sections") or []
    change_types = acceptance.get("change_types") or []
    if sections:
        section_ids = ", ".join(str(section.get("id")) for section in sections)
        change_type_ids = ", ".join(str(change_type.get("id")) for change_type in change_types)
        print("\nAcceptance model:")
        print(f"- Sections: {section_ids}")
        print(f"- Change types: {change_type_ids}")
    impact = result.get("impact_model") or {}
    areas = impact.get("areas") or []
    if areas:
        area_ids = ", ".join(str(area.get("id")) for area in areas)
        print("\nImpact model:")
        print(f"- Areas: {area_ids}")


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
    wizard = result.get("setup_wizard") if isinstance(result.get("setup_wizard"), dict) else {}
    if wizard.get("wizard_id"):
        print(f"\nWizard: {wizard['wizard_id']}")
        print(f"Responder: agent wizard answer {wizard['wizard_id']} <resposta>")
    if result.get("llm_backend"):
        print(f"Requested backend: {result['llm_backend']}")
    if result.get("next_steps"):
        print("\nNext steps:")
        for step in result["next_steps"]:
            print(f"- {step}")


def print_wizard(result: dict[str, Any]) -> None:
    if result.get("kind") == "wizards":
        items = result.get("items") or []
        print(f"Wizards: {len(items)}")
        for item in items:
            print(f"- {item.get('wizard_id')}  {item.get('status')}  {item.get('provider')}")
        return
    wizard = result.get("wizard") if isinstance(result.get("wizard"), dict) else result.get("setup_wizard")
    if not isinstance(wizard, dict):
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(f"Wizard {wizard.get('wizard_id')}: {wizard.get('status')}")
    print(f"Provider: {wizard.get('provider')}")
    question = result.get("next_question") or wizard.get("next_question")
    if isinstance(question, dict) and question.get("text"):
        print(f"Pergunta: {question['text']}")
        if question.get("type") == "confirm":
            print("[s/N]")
        print(f"Responder: agent wizard answer {wizard.get('wizard_id')} <resposta>")
    if result.get("source_result"):
        source = result["source_result"].get("source") or {}
        print(f"Source configurada: {source.get('id')}")
    if result.get("resumed_prompt"):
        resume = result.get("resume_result") or {}
        print(f"Prompt retomado: {resume.get('status')}")


def print_sources(result: dict[str, Any]) -> None:
    print(f"Sources config: {result['config_path']}")
    if not result["items"]:
        print("No sources configured.")
        return
    for item in result["items"]:
        marker = "  [unsafe config]" if item.get("stored_secret") else ""
        print(f"- {item['id']}  {item['provider']}  {item.get('label') or '-'}{marker}")
        if item.get("unsafe_config_keys"):
            print(f"  Unsafe config keys: {', '.join(item['unsafe_config_keys'])}")


def print_source_status(result: dict[str, Any]) -> None:
    print(f"Source status: {result['status']}")
    for item in result["items"]:
        print(f"- {item['id']}: {item['status']}")
        missing = item.get("missing_env_refs") or []
        if missing:
            print(f"  Missing env refs: {', '.join(missing)}")
        unsafe = item.get("unsafe_config_keys") or []
        if unsafe:
            print(f"  Unsafe config keys: {', '.join(unsafe)}")
        for step in item.get("next_steps") or []:
            print(f"  - {step}")


def print_source_configure(result: dict[str, Any]) -> None:
    if result.get("status") == "blocked":
        print("Source configuration blocked.")
        print(f"Field: {result.get('field') or '-'}")
        print(f"Reason: {result.get('reason') or '-'}")
        if result.get("message"):
            print(str(result["message"]))
        print("Stored secret: no")
        return
    source = result["source"]
    print(f"Source configured: {source['id']}")
    print(f"Provider: {source['provider']}")
    print(f"Config: {result['config_path']}")
    print(f"Stored secret: {'yes' if result.get('stored_secret') else 'no'}")


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


def print_memory_backup(result: dict[str, Any]) -> None:
    print(f"Memory backup: {result.get('status')}")
    if result.get("home"):
        print(f"Home: {result.get('home')}")
    backup = result.get("backup") if isinstance(result.get("backup"), dict) else {}
    if backup:
        print(f"ID: {backup.get('id')}")
        print(f"Path: {backup.get('path')}")
        print(f"Files: {backup.get('file_count', 0)}")
        print(f"Remote upload: {'yes' if backup.get('remote_upload') else 'no'}")
        print(f"Encrypted: {'yes' if backup.get('encrypted') else 'no'}")
    if result.get("items"):
        for item in result["items"]:
            print(f"- {item.get('id')}: {item.get('file_count', 0)} file(s)")
    if result.get("next_steps"):
        print("Next steps:")
        for step in result["next_steps"]:
            print(f"- {step}")


def print_shared_memory(result: dict[str, Any]) -> None:
    print(f"Shared memory: {result.get('status')}")
    memory = result.get("memory") if isinstance(result.get("memory"), dict) else {}
    if memory:
        print(f"ID: {memory.get('id')}")
        print(f"URL: {memory.get('share_url')}")
    if result.get("submission_id"):
        print(f"Submission: {result.get('submission_id')}")
    if result.get("path"):
        print(f"Path: {result.get('path')}")
    if result.get("content"):
        print(result["content"])
    if result.get("items"):
        for item in result["items"]:
            print(f"- {item.get('id')}: {item.get('title')}")
    access = result.get("contributor_access") if isinstance(result.get("contributor_access"), dict) else {}
    if access:
        print("Contributor access:")
        print(f"- URL: {access.get('url')}")
        print(f"- Key: {access.get('key')}")
    owner_access = result.get("owner_access") if isinstance(result.get("owner_access"), dict) else {}
    if owner_access:
        print("Owner access:")
        print(f"- Key: {owner_access.get('key')}")


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
    if result.get("status") == "needs-input" and result.get("questions"):
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
    if result.get("kind") == "mini-brain-setup":
        mini_brain = result.get("mini_brain") or {}
        print(f"Mini-brain: {mini_brain.get('status', '-')}")
        print(f"Model: {mini_brain.get('ollama_model') or mini_brain.get('hf_model') or '-'}")
        pull = result.get("pull") or {}
        if pull:
            print(f"Ollama pull: {pull.get('status', '-')}")
        if result.get("message"):
            print(result["message"])
        if result.get("next_steps"):
            print("Next steps:")
            for step in result["next_steps"]:
                print(f"- {step}")
        return
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
    if result.get("run_id"):
        print(f"Run: {result['run_id']}")
    if result.get("duration_seconds") is not None:
        print(f"Duration: {result['duration_seconds']}s")
    if result.get("audit_id"):
        print(f"Audit: {result['audit_id']}")
    if result.get("message"):
        print(result["message"])
    notification = result.get("notification")
    if isinstance(notification, dict):
        print(f"Notification: {notification.get('status')}")
        if notification.get("reason"):
            print(f"Reason: {notification['reason']}")


def print_scheduler(result: dict[str, Any]) -> None:
    print(f"Scheduler: {result['status']}")
    if result.get("message"):
        print(result["message"])
    if "due_count" in result:
        print(f"Due tasks: {result['due_count']}")
    if result.get("events_path"):
        print(f"Events: {result['events_path']}")


def print_notifications(result: dict[str, Any]) -> None:
    action = result.get("action")
    status = result.get("status") or "ok"
    print(f"Notifications: {status}")
    if action:
        print(f"Action: {action}")
    if result.get("reason"):
        print(f"Reason: {result['reason']}")
    if result.get("channel"):
        print(f"Channel: {result['channel']}")
    if isinstance(result.get("notification"), dict):
        notification = result["notification"]
        print(f"Event: {notification.get('event')}")
        print(f"Summary: {notification.get('summary') or notification.get('message')}")
    deliveries = result.get("deliveries") if isinstance(result.get("deliveries"), list) else []
    if deliveries:
        print("Deliveries:")
        for delivery in deliveries:
            detail = delivery.get("reason") or delivery.get("status") or "-"
            print(f"- {delivery.get('channel') or '-'}: {detail}")
    desktop = result.get("desktop")
    if isinstance(desktop, dict):
        print(f"Desktop enabled: {desktop.get('enabled', '-')}")
        events = desktop.get("events") or []
        if events:
            print(f"Events: {', '.join(str(item) for item in events)}")
        backend = desktop.get("backend")
        if isinstance(backend, dict):
            print(f"Backend: {backend.get('name') or '-'} ({backend.get('status') or '-'})")
    if result.get("events"):
        print("Events:")
        for event in result["events"]:
            print(f"- {event}")
    if result.get("channels"):
        print("Channels:")
        for channel in result["channels"]:
            print(f"- {channel.get('id')}: {channel.get('status')}")
    channel_config = result.get("channel_config")
    if isinstance(channel_config, dict):
        print(f"Channel enabled: {channel_config.get('enabled', '-')}")
        events = channel_config.get("events") or []
        if events:
            print(f"Channel events: {', '.join(str(item) for item in events)}")
    if result.get("config_path"):
        print(f"Config: {result['config_path']}")
    if result.get("history_path"):
        print(f"History: {result['history_path']}")


def print_notification_event(result: dict[str, Any]) -> None:
    print(f"Notification event: {result.get('event')}")
    print(f"Status: {result.get('status')}")
    print(f"Title: {result.get('title')}")
    print(f"Summary: {result.get('summary')}")


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


def print_local_llm(result: dict[str, Any]) -> None:
    kind = result.get("kind")
    print(f"Local LLM: {result.get('status')}")
    if kind == "local-llm":
        mini = result.get("mini_brain") or {}
        print(f"Mini-brain: {mini.get('status')} enabled={mini.get('enabled')}")
        print(f"Workers: {len(result.get('workers') or [])}")
        return
    if kind == "local-llm-doctor":
        ollama = result.get("ollama") or {}
        mini = result.get("mini_brain") or {}
        print(f"Ollama: {ollama.get('status')}")
        print(f"Mini-brain: {mini.get('status')} enabled={mini.get('enabled')}")
        for step in result.get("next_steps") or []:
            print(f"- {step}")
        return
    if kind == "local-llm-models":
        print(f"Binary: {result.get('binary') or '-'}")
        for item in result.get("items") or []:
            print(f"- {item.get('name')}  {item.get('size') or '-'}")
        recommended = [item for item in result.get("recommended") or [] if not item.get("installed")]
        if recommended:
            print("Recommended:")
            for item in recommended[:5]:
                print(f"- {item.get('name')}: {item.get('recommended_for')}")
        return
    if kind == "local-llm-benchmark":
        print(f"Model: {result.get('model')}")
        for check in result.get("checks") or []:
            print(f"- {check.get('id')}: {check.get('status')}")
        for step in result.get("next_steps") or []:
            print(f"Next: {step}")
        return
    if result.get("command"):
        command = result["command"]
        print("Command: " + (" ".join(command) if isinstance(command, list) else str(command)))
    if result.get("message"):
        print(result["message"])


def print_mcp(result: dict[str, Any]) -> None:
    print(f"MCP: {result.get('status', 'ok')}")
    print(f"Transport: {result.get('transport', '-')}")
    print(f"Protocol: {result.get('protocol_version', '-')}")
    server = result.get("server") if isinstance(result.get("server"), dict) else {}
    if server:
        print(f"Server: {server.get('name', '-')} {server.get('version', '')}".rstrip())
    tools = result.get("tools")
    if isinstance(tools, list):
        print("Tools:")
        for tool in tools:
            print(f"- {tool.get('name')}")
    elif isinstance(tools, dict):
        print(f"Tools: {tools.get('count', 0)}")


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
