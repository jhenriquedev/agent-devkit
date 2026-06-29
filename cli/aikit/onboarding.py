"""First-run and no-argument onboarding for Agent DevKit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.aikit.agent_registry import load_agent_registry
from cli.aikit.app_home import app_home_status
from cli.aikit.llm import doctor_backends, list_backends
from cli.aikit.memory import ensure_memory
from cli.aikit.ollama import ollama_status
from cli.aikit.personality import load_personality
from cli.aikit.sessions import list_sessions, show_session
from cli.aikit.setup_wizard import setup_wizard
from cli.aikit.sources import list_sources, source_status
from cli.aikit.specialist_readiness import specialist_readiness
from cli.aikit.tasks import load_tasks, public_task, task_is_due, list_tasks


ONBOARDING_MODE_SCHEMA_VERSION = "agent-devkit.onboarding-plan/v1"


def onboarding_status(root: Path) -> dict[str, Any]:
    """Return a local, deterministic startup snapshot for `agent` without args."""

    home = app_home_status()
    memory = ensure_memory()
    personality = load_personality()
    sessions = summarize_sessions()
    setup = setup_wizard(root, dry_run=True, yes=False)
    llms = summarize_llms()
    ollama = ollama_status()
    sources = summarize_sources()
    tasks = summarize_tasks()
    specialists = specialist_readiness(root)

    blockers = startup_blockers(setup=setup, llms=llms)
    suggestions = suggested_actions(
        memory=memory,
        personality=personality,
        sessions=sessions,
        setup=setup,
        llms=llms,
        ollama=ollama,
        sources=sources,
        tasks=tasks,
        specialists=specialists,
    )
    status = "ready"
    if blockers:
        status = "needs-setup"
    elif suggestions:
        status = "needs-attention"

    return {
        "kind": "onboarding",
        "schema_version": "agent-devkit.onboarding/v1",
        "status": status,
        "agent": {
            "name": personality.get("agent_name") or "Agent DevKit",
            "tone": personality.get("tone"),
            "detail_level": personality.get("detail_level"),
            "language": personality.get("language"),
            "user_name": personality.get("user_name"),
        },
        "home": home,
        "memory": {
            "status": memory.get("status"),
            "home": memory.get("home"),
            "created": memory.get("created") or [],
            "file_count": len(memory.get("files") or []),
        },
        "sessions": {
            "status": sessions.get("status"),
            "home": sessions.get("home"),
            "active_session_id": sessions.get("active_session_id"),
            "count": len(sessions.get("items") or []),
            "active": sessions.get("active"),
            "recent": sessions.get("recent") or [],
        },
        "llm": llms,
        "ollama": summarize_ollama(ollama),
        "toolchain": summarize_toolchain(setup.get("toolchain") or {}),
        "sources": sources,
        "tasks": tasks,
        "specialists": summarize_specialists(specialists),
        "blockers": blockers,
        "suggested_actions": suggestions,
        "onboarding_modes": onboarding_modes(),
        "startup_flow": startup_flow(status=status, sessions=sessions, tasks=tasks, blockers=blockers),
        "assistant_prompt": assistant_prompt(status=status, sessions=sessions, tasks=tasks, blockers=blockers, actions=suggestions),
    }


def onboarding_plan(root: Path, mode: str) -> dict[str, Any]:
    selected_mode = normalize_onboarding_mode(mode)
    status = onboarding_status(root)
    registry = load_agent_registry(root)
    minimal_steps = [
        plan_step(
            "personality",
            "Configurar nome publico, usuario, idioma, tom e nivel de detalhe.",
            "agent setup personality",
            write_policy="local_config_write",
        ),
        plan_step(
            "coordinator-llm",
            "Registrar Claude Code, Codex CLI ou API como coordenador/planejador/revisor opcional para tarefas de alto nivel.",
            "agent llm list",
            write_policy="local_config_write",
        ),
        plan_step(
            "mini-brain",
            "Validar o mini cerebro embarcado Qwen2.5-0.5B para conversa simples, setup e tarefas operacionais leves.",
            "agent setup mini-brain --dry-run",
            write_policy="local_config_write",
            model="Qwen/Qwen2.5-0.5B-Instruct",
        ),
        plan_step(
            "sessions-and-memory",
            "Inicializar memoria local, sessoes, preferencias e identidade em .agent-devkit.",
            "agent memory show",
            write_policy="local_config_write",
        ),
    ]
    complete_steps = minimal_steps + [
        plan_step(
            "toolchain",
            "Revisar CLIs locais e planejar instalacao com opt-in por ferramenta.",
            "agent toolchain doctor",
            write_policy="confirm",
        ),
        plan_step(
            "providers-and-sources",
            "Preparar configuracao sob demanda para providers, sources e credenciais por referencia segura.",
            "agent source list",
            write_policy="local_config_write",
        ),
        plan_step(
            "specialist-catalog",
            "Validar catalogo completo e readiness de agentes especialistas por provider/source.",
            "agent doctor",
            write_policy="read_only",
        ),
        plan_step(
            "local-automation-factory",
            "Preparar criacao local de scripts, skills, knowledge e agentes personalizados em .agent-devkit.",
            "agent local list",
            write_policy="local_config_write",
        ),
        plan_step(
            "tasks-and-notifications",
            "Configurar tarefas agendadas e notificacoes locais com eventos de conclusao/bloqueio.",
            "agent notifications doctor",
            write_policy="local_config_write",
        ),
        plan_step(
            "knowledge-and-shared-memory",
            "Inicializar knowledge local e memoria compartilhada com curadoria pelo dono.",
            "agent knowledge doctor",
            write_policy="local_config_write",
        ),
    ]
    steps = minimal_steps if selected_mode == "minimal" else complete_steps
    return {
        "kind": "onboarding-plan",
        "schema_version": ONBOARDING_MODE_SCHEMA_VERSION,
        "status": "planned",
        "mode": selected_mode,
        "external_actions_executed": False,
        "agent": status.get("agent"),
        "home": status.get("home"),
        "agent_catalog": {
            "agents": len(registry.get("agents") or {}),
            "capabilities": len(registry.get("capabilities") or {}),
        },
        "steps": steps,
        "next_steps": [step["command"] for step in steps],
    }


def normalize_onboarding_mode(mode: str) -> str:
    if mode in {"minimal", "complete"}:
        return mode
    raise ValueError(f"unsupported onboarding mode: {mode}")


def onboarding_modes() -> list[dict[str, Any]]:
    return [
        {
            "id": "minimal",
            "label": "Onboarding minimo",
            "command": "agent onboard minimal",
            "purpose": "Deixar o agente conversavel e utilizavel com identidade, coordenador LLM, mini-brain e memoria local.",
        },
        {
            "id": "complete",
            "label": "Onboarding completo",
            "command": "agent onboard complete",
            "purpose": "Revisar tambem toolchain, providers, fontes, catalogo, automacoes locais, tarefas, notificacoes e memorias compartilhadas.",
        },
    ]


def plan_step(
    step_id: str,
    purpose: str,
    command: str,
    *,
    write_policy: str,
    model: str | None = None,
) -> dict[str, Any]:
    payload = {
        "id": step_id,
        "status": "planned",
        "purpose": purpose,
        "command": command,
        "write_policy": write_policy,
        "external_write": False,
    }
    if model:
        payload["model"] = model
    return payload


def summarize_llms() -> dict[str, Any]:
    backends = list_backends()
    doctor = doctor_backends()
    items = doctor.get("items") or []
    usable = [item for item in items if item.get("status") == "ok" and item.get("id") != "ollama"]
    ollama_item = next((item for item in items if item.get("id") == "ollama"), None)
    preference = backends.get("preference") or {}
    return {
        "status": "ok" if usable else "missing",
        "default": backends.get("default"),
        "primary": preference.get("primary"),
        "fallback_enabled": preference.get("fallback_enabled"),
        "configured_count": len([item for item in backends.get("items") or [] if item.get("configured")]),
        "usable_count": len(usable),
        "backends": [
            {
                "id": item.get("id"),
                "status": item.get("status"),
                "configured": item.get("configured"),
                "kind": item.get("kind"),
            }
            for item in items
        ],
        "ollama_backend": {
            "status": ollama_item.get("status") if isinstance(ollama_item, dict) else None,
            "configured": ollama_item.get("configured") if isinstance(ollama_item, dict) else None,
        },
    }


def summarize_ollama(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": payload.get("status"),
        "binary": payload.get("binary"),
        "version": payload.get("version"),
        "daemon": payload.get("daemon"),
        "model_count": payload.get("model_count", 0),
        "install_plan": payload.get("install_plan"),
    }


def summarize_toolchain(payload: dict[str, Any]) -> dict[str, Any]:
    items = payload.get("items") or []
    return {
        "status": payload.get("status"),
        "platform": payload.get("platform"),
        "required_missing": payload.get("required_missing") or [],
        "optional_missing": payload.get("optional_missing") or [],
        "ok_count": len([item for item in items if item.get("status") == "ok"]),
        "missing_count": len([item for item in items if item.get("status") == "missing"]),
    }


def summarize_sources() -> dict[str, Any]:
    sources = list_sources()
    try:
        status = source_status()
    except ValueError:
        status = {"status": "missing", "items": []}
    return {
        "status": status.get("status"),
        "count": len(sources.get("items") or []),
        "defaults": sources.get("defaults") or {},
        "stored_secret": bool(sources.get("stored_secret")),
    }


def summarize_tasks() -> dict[str, Any]:
    tasks = list_tasks()
    raw = load_tasks()
    raw_items = [item for item in raw.get("tasks") or [] if isinstance(item, dict)]
    items = tasks.get("items") or []
    enabled = [item for item in items if item.get("status") == "enabled"]
    due = [public_task(item) for item in raw_items if item.get("status") == "enabled" and task_is_due(item)]
    pending = [item for item in enabled if item.get("run_count", 0) == 0]
    return {
        "status": tasks.get("status"),
        "count": len(items),
        "enabled_count": len(enabled),
        "pending_count": len(pending),
        "due_count": len(due),
        "due": due[:5],
        "pending": pending[:5],
        "path": tasks.get("path"),
    }


def summarize_specialists(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": payload.get("status"),
        "agents_total": payload.get("agents_total"),
        "capabilities_total": payload.get("capabilities_total"),
        "agents_with_provider_requirements": payload.get("agents_with_provider_requirements"),
        "ready_agents": payload.get("ready_agents"),
        "partial_agents": payload.get("partial_agents"),
        "needs_setup_agents": payload.get("needs_setup_agents"),
        "configured_providers": payload.get("configured_providers") or [],
        "missing_providers": payload.get("missing_providers") or [],
        "next_steps": payload.get("next_steps") or [],
    }


def startup_flow(
    *,
    status: str,
    sessions: dict[str, Any],
    tasks: dict[str, Any],
    blockers: list[dict[str, str]],
) -> list[dict[str, str]]:
    steps = [
        {"id": "validate-home", "status": "done", "label": "Validar home local e memoria"},
        {"id": "validate-setup", "status": "attention" if blockers else "done", "label": "Validar setup minimo"},
        {
            "id": "check-session",
            "status": "active" if sessions.get("active") else "empty",
            "label": "Verificar conversa ou analise em andamento",
        },
        {
            "id": "check-tasks",
            "status": "due" if tasks.get("due_count") else ("pending" if tasks.get("pending_count") else "empty"),
            "label": "Verificar tarefas pendentes e dados a retornar",
        },
        {"id": "ask-next-action", "status": status, "label": "Responder ou perguntar o proximo objetivo"},
    ]
    return steps


def assistant_prompt(
    *,
    status: str,
    sessions: dict[str, Any],
    tasks: dict[str, Any],
    blockers: list[dict[str, str]],
    actions: list[dict[str, str]],
) -> str:
    if blockers:
        return "Preciso concluir o setup minimo antes de executar tarefas. Posso iniciar o onboarding minimo ou completo."
    if tasks.get("due_count"):
        return "Encontrei tarefas agendadas prontas para revisao. Posso listar, executar em dry-run ou aguardar sua instrucao."
    if tasks.get("pending_count"):
        pending = tasks.get("pending") if isinstance(tasks.get("pending"), list) else []
        first = pending[0] if pending and isinstance(pending[0], dict) else {}
        title = first.get("title") or first.get("id") or "tarefa pendente"
        active = sessions.get("active") if isinstance(sessions.get("active"), dict) else None
        if active:
            session_title = active.get("title") or active.get("id")
            return f"Existe uma sessao ativa: {session_title}. Tambem encontrei tarefa pendente: {title}. Posso continuar a conversa, listar tarefas ou executar a pendencia em dry-run."
        return f"Encontrei tarefa pendente: {title}. Posso listar, executar em dry-run ou receber uma nova tarefa."
    active = sessions.get("active") if isinstance(sessions.get("active"), dict) else None
    if active:
        title = active.get("title") or active.get("id")
        return f"Existe uma sessao ativa: {title}. Posso continuar essa conversa, mostrar status ou iniciar uma nova tarefa."
    if actions:
        return "Estou pronto. Posso continuar o onboarding, configurar ferramentas sob demanda ou receber uma tarefa em linguagem natural."
    return "Estou pronto. O que voce quer fazer agora?"


def startup_blockers(*, setup: dict[str, Any], llms: dict[str, Any]) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    toolchain = setup.get("toolchain") or {}
    for item in toolchain.get("required_missing") or []:
        blockers.append(
            {
                "id": f"toolchain.{item}",
                "message": f"Required toolchain item is missing: {item}.",
                "command": f"agent toolchain install {item} --dry-run",
            }
        )
    if llms.get("usable_count", 0) < 1:
        blockers.append(
            {
                "id": "llm.unavailable",
                "message": "No usable coordinator LLM backend was detected.",
                "command": "agent llm doctor",
            }
        )
    return blockers


def suggested_actions(
    *,
    memory: dict[str, Any],
    personality: dict[str, Any],
    sessions: dict[str, Any],
    setup: dict[str, Any],
    llms: dict[str, Any],
    ollama: dict[str, Any],
    sources: dict[str, Any],
    tasks: dict[str, Any],
    specialists: dict[str, Any],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    due_tasks = tasks.get("due") if isinstance(tasks.get("due"), list) else []
    pending_tasks = tasks.get("pending") if isinstance(tasks.get("pending"), list) else []
    first_due = due_tasks[0] if due_tasks and isinstance(due_tasks[0], dict) else None
    first_pending = pending_tasks[0] if pending_tasks and isinstance(pending_tasks[0], dict) else None
    if first_due and first_due.get("id"):
        actions.append(
            {
                "id": "tasks.run-due",
                "label": f"Run due task: {first_due.get('title') or first_due.get('id')}",
                "command": f"agent task run {first_due['id']} --dry-run",
            }
        )
    if first_pending and first_pending.get("id"):
        actions.append(
            {
                "id": "tasks.run-pending",
                "label": f"Run pending task: {first_pending.get('title') or first_pending.get('id')}",
                "command": f"agent task run {first_pending['id']} --dry-run",
            }
        )
        actions.append(
            {
                "id": "tasks.review",
                "label": "Review local scheduled and manual tasks",
                "command": "agent task list",
            }
        )
    if memory.get("created"):
        actions.append(
            {
                "id": "memory.review",
                "label": "Review local memory files",
                "command": "agent memory show",
            }
        )
    if not personality.get("user_name"):
        actions.append(
            {
                "id": "personality.setup",
                "label": "Configure agent name, user name and response style",
                "command": "agent setup personality",
            }
        )
    if llms.get("usable_count", 0) < 1:
        actions.append(
            {
                "id": "llm.configure",
                "label": "Configure a coordinator LLM backend",
                "command": "agent llm doctor",
            }
        )
    if ollama.get("status") == "missing":
        actions.append(
            {
                "id": "ollama.install",
                "label": "Inspect local Ollama mini-brain setup",
                "command": "agent ollama status",
            }
        )
    if (setup.get("toolchain") or {}).get("optional_missing"):
        actions.append(
            {
                "id": "toolchain.optional",
                "label": "Review optional local tools",
                "command": "agent toolchain doctor",
            }
        )
    if sources.get("count", 0) < 1:
        actions.append(
            {
                "id": "sources.configure",
                "label": "Add reusable project/provider sources when needed",
                "command": "agent source list",
            }
        )
    if specialists.get("status") in {"needs-setup", "partial"}:
        next_steps = specialists.get("next_steps") if isinstance(specialists.get("next_steps"), list) else []
        actions.append(
            {
                "id": "specialists.readiness",
                "label": "Review specialist agent provider readiness",
                "command": str(next_steps[0] if next_steps else "agent doctor"),
            }
        )
    if tasks.get("count", 0) < 1:
        actions.append(
            {
                "id": "tasks.create",
                "label": "Create scheduled or recurring tasks when useful",
                "command": "agent task list",
            }
        )
    if not sessions.get("active_session_id"):
        actions.append(
            {
                "id": "session.start",
                "label": "Start by sending a natural-language task",
                "command": "agent \"o que voce consegue fazer aqui?\"",
            }
        )
    return dedupe_actions(actions)


def dedupe_actions(actions: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for action in actions:
        action_id = action.get("id")
        if not action_id or action_id in seen:
            continue
        seen.add(action_id)
        deduped.append(action)
    return deduped


def summarize_sessions() -> dict[str, Any]:
    sessions = list_sessions()
    active_id = sessions.get("active_session_id")
    active = None
    if active_id:
        try:
            payload = show_session(str(active_id))
            active = payload.get("session")
            if isinstance(active, dict):
                active["summary"] = payload.get("summary")
                active["recent_messages"] = payload.get("recent_messages") or []
        except ValueError:
            active = None
    return {
        **sessions,
        "active": active,
        "recent": (sessions.get("items") or [])[:5],
    }
