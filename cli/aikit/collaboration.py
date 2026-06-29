"""Structured multi-agent collaboration helpers."""

from __future__ import annotations

from typing import Any

from cli.aikit.memory import redact_secrets


COLLABORATION_SCHEMA_VERSION = "ai-devkit.collaboration/v1"
TASK_ROLES = {"collector", "analyzer", "reviewer", "coordinator"}
TEXT_PREVIEW_LIMIT = 600


def normalize_collaborative_task(
    task: dict[str, Any],
    *,
    role: str | None = None,
    depends_on: list[str] | None = None,
    sequence: int | None = None,
) -> dict[str, Any]:
    item = dict(task)
    task_id = str(item.get("task_id") or item.get("id") or "").strip()
    item["task_id"] = task_id
    item["role"] = normalize_role(role or item.get("role"))
    item["depends_on"] = normalize_depends_on(depends_on if depends_on is not None else item.get("depends_on"))
    item["handoff"] = normalize_handoff(item.get("handoff"))
    item["critical"] = item.get("primary") is True or item.get("critical") is True
    item["parallel_safe"] = item.get("parallel_safe") is True
    if sequence is not None:
        item["sequence"] = sequence
    return item


def normalize_role(value: Any) -> str:
    role = str(value or "").strip()
    return role if role in TASK_ROLES else "analyzer"


def normalize_depends_on(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def normalize_handoff(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {
            "produces": normalize_string_list(value.get("produces")),
            "consumes": normalize_string_list(value.get("consumes")),
            "summary": str(value.get("summary") or "").strip(),
        }
    return {"produces": [], "consumes": [], "summary": ""}


def normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def initial_shared_context(prompt: str, routing_decision: dict[str, Any] | None) -> dict[str, Any]:
    routing = routing_decision if isinstance(routing_decision, dict) else {}
    confidence_label = str(routing.get("confidence_label") or "").strip()
    human_escalations = []
    if routing.get("requires_confirmation"):
        human_escalations.append(
            human_escalation(
                reason=str(routing.get("reason") or "Routing requires confirmation."),
                source="task-orchestrator",
                kind="routing-confirmation",
                confidence=confidence_label or "low",
            )
        )
    return {
        "schema_version": COLLABORATION_SCHEMA_VERSION,
        "facts": [
            {
                "source": "task-orchestrator",
                "kind": "prompt",
                "summary": preview_text(prompt),
            }
        ],
        "inferences": [
            {
                "source": "task-orchestrator",
                "kind": "routing",
                "status": routing.get("status"),
                "selected_agent_id": routing.get("selected_agent_id"),
                "selected_capability_id": routing.get("selected_capability_id"),
                "confidence": routing.get("confidence"),
            }
        ]
        if routing
        else [],
        "artifacts": [],
        "blockers": [],
        "decisions": [],
        "risks": [],
        "questions": [],
        "handoffs": [],
        "conflicts": [],
        "human_escalations": human_escalations,
    }


def build_collaboration_graph(
    specialist_tasks: list[dict[str, Any]],
    configuration_tasks: list[dict[str, Any]],
    review_task: dict[str, Any] | None,
) -> dict[str, Any]:
    nodes = []
    edges = []
    all_tasks = [*specialist_tasks, *configuration_tasks]
    if review_task:
        all_tasks.append(review_task)
    for task in all_tasks:
        if not isinstance(task, dict):
            continue
        task_id = str(task.get("task_id") or task.get("id") or "")
        if not task_id:
            continue
        nodes.append(
            {
                "task_id": task_id,
                "agent_id": task.get("agent_id"),
                "capability_id": task.get("capability_id"),
                "role": normalize_role(task.get("role")),
                "status": task.get("status"),
                "parallel_safe": task.get("parallel_safe") is True,
            }
        )
        for dependency in normalize_depends_on(task.get("depends_on")):
            edges.append({"from": dependency, "to": task_id, "type": "depends_on"})
    return {
        "schema_version": COLLABORATION_SCHEMA_VERSION,
        "nodes": nodes,
        "edges": edges,
        "parallel_groups": parallel_groups(nodes, edges),
    }


def parallel_groups(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[list[str]]:
    blocked = {str(edge.get("to")) for edge in edges if edge.get("to")}
    group = [
        str(node["task_id"])
        for node in nodes
        if node.get("parallel_safe") is True and str(node.get("task_id") or "") not in blocked
    ]
    return [group] if len(group) > 1 else []


def collaborative_task_sequence(plan: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = [task for task in plan.get("specialist_tasks") or [] if isinstance(task, dict)]
    if not plan.get("collaboration_enabled"):
        return [task for task in tasks if task.get("primary")]
    return dependency_order(tasks)


def dependency_order(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {str(task.get("task_id") or task.get("id")): task for task in tasks if task.get("task_id") or task.get("id")}
    ordered: list[dict[str, Any]] = []
    remaining = dict(by_id)
    while remaining:
        progressed = False
        for task_id, task in list(remaining.items()):
            dependencies = normalize_depends_on(task.get("depends_on"))
            if all(dependency not in remaining for dependency in dependencies):
                ordered.append(task)
                remaining.pop(task_id)
                progressed = True
        if not progressed:
            ordered.extend(remaining.values())
            break
    return sorted(ordered, key=lambda task: int(task.get("sequence") or 0))


def blocked_dependency(task: dict[str, Any], completed: set[str], failed: set[str]) -> str | None:
    dependencies = normalize_depends_on(task.get("depends_on"))
    failed_dependencies = [dependency for dependency in dependencies if dependency in failed]
    if failed_dependencies:
        return f"Task dependency failed: {', '.join(failed_dependencies)}."
    missing = [dependency for dependency in dependencies if dependency not in completed]
    if missing:
        return f"Task dependency not completed: {', '.join(missing)}."
    return None


def merge_task_handoff(shared_context: dict[str, Any], task: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    context = normalize_shared_context(shared_context)
    handoff = summarize_handoff(task, result)
    if handoff.get("fact"):
        context["facts"].append(handoff["fact"])
    if handoff.get("artifact"):
        context["artifacts"].append(handoff["artifact"])
    if handoff.get("blocker"):
        context["blockers"].append(handoff["blocker"])
    for risk in handoff.get("risks") or []:
        context["risks"].append(risk)
    for question in handoff.get("questions") or []:
        context["questions"].append(question)
    context["handoffs"].append(build_handoff(task, None, result, handoff=handoff))
    if handoff.get("blocker"):
        context["conflicts"].append(
            conflict(
                source=task.get("task_id") or task.get("id"),
                kind="blocked-task",
                summary=str(handoff["blocker"].get("reason") or "Task blocked."),
                evidence=[task.get("agent_id"), task.get("capability_id")],
                severity="high" if result.get("status") == "blocked" else "medium",
            )
        )
        context["human_escalations"].append(
            human_escalation(
                reason=str(handoff["blocker"].get("reason") or "Task requires human decision."),
                source=task.get("task_id") or task.get("id"),
                kind="blocked-task",
                confidence="low",
            )
        )
    context["decisions"].append(
        {
            "source": task.get("task_id") or task.get("id"),
            "agent_id": task.get("agent_id"),
            "status": result.get("status"),
            "ok": bool(result.get("ok")),
        }
    )
    return context


def normalize_shared_context(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        context = dict(value)
    else:
        context = {}
    context.setdefault("schema_version", COLLABORATION_SCHEMA_VERSION)
    for key in (
        "facts",
        "inferences",
        "artifacts",
        "blockers",
        "decisions",
        "risks",
        "questions",
        "handoffs",
        "conflicts",
        "human_escalations",
    ):
        if not isinstance(context.get(key), list):
            context[key] = []
    return context


def summarize_handoff(task: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    source = task.get("task_id") or task.get("id")
    summary = preview_text(result.get("message") or result.get("response") or result.get("stdout") or result.get("error") or result.get("reason") or "")
    handoff: dict[str, Any] = {
        "fact": {
            "source": source,
            "agent_id": task.get("agent_id"),
            "capability_id": task.get("capability_id"),
            "status": result.get("status"),
            "summary": summary,
        }
    }
    artifacts = result.get("artifacts")
    if isinstance(artifacts, list) and artifacts:
        handoff["artifact"] = {
            "source": source,
            "items": [safe_artifact(item) for item in artifacts[:10]],
        }
    if not result.get("ok"):
        handoff["blocker"] = {
            "source": source,
            "reason": preview_text(result.get("reason") or result.get("error") or "Task did not complete successfully."),
        }
    risks = result.get("risks") if isinstance(result.get("risks"), list) else []
    if risks:
        handoff["risks"] = [{"source": source, "summary": preview_text(risk)} for risk in risks[:10]]
    questions = result.get("questions") or result.get("next_questions")
    if isinstance(questions, list) and questions:
        handoff["questions"] = [{"source": source, "summary": preview_text(question)} for question in questions[:10]]
    return handoff


def build_handoff(
    from_task: dict[str, Any],
    to_task: dict[str, Any] | None,
    result: dict[str, Any],
    *,
    handoff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = handoff or summarize_handoff(from_task, result)
    return {
        "from": str(from_task.get("agent_id") or ""),
        "from_task_id": from_task.get("task_id") or from_task.get("id"),
        "to": str((to_task or {}).get("agent_id") or "agent-devkit-core"),
        "to_task_id": (to_task or {}).get("task_id") or (to_task or {}).get("id"),
        "summary": ((summary.get("fact") or {}).get("summary") or ""),
        "facts": [summary["fact"]] if summary.get("fact") else [],
        "artifacts": [summary["artifact"]] if summary.get("artifact") else [],
        "risks": list(summary.get("risks") or []),
        "open_questions": list(summary.get("questions") or []),
        "confidence": handoff_confidence(result),
    }


def conflict(
    *,
    source: Any,
    kind: str,
    summary: str,
    evidence: list[Any] | None = None,
    severity: str = "medium",
) -> dict[str, Any]:
    return {
        "source": str(source or "unknown"),
        "kind": kind,
        "summary": preview_text(summary),
        "evidence": [str(item) for item in evidence or [] if item],
        "severity": severity if severity in {"low", "medium", "high"} else "medium",
    }


def human_escalation(*, reason: str, source: Any, kind: str, confidence: str = "low") -> dict[str, Any]:
    return {
        "source": str(source or "unknown"),
        "kind": kind,
        "reason": preview_text(reason),
        "confidence": confidence if confidence in {"high", "medium", "low"} else "low",
        "status": "waiting-for-user",
    }


def handoff_confidence(result: dict[str, Any]) -> str:
    explicit = str(result.get("confidence") or "").strip().lower()
    if explicit in {"high", "medium", "low"}:
        return explicit
    if result.get("ok"):
        return "high"
    if result.get("status") == "needs-input":
        return "medium"
    return "low"


def safe_artifact(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): preview_text(item) if isinstance(item, str) else item for key, item in value.items()}
    if isinstance(value, str):
        return preview_text(value)
    return value


def preview_text(value: Any, *, limit: int = TEXT_PREVIEW_LIMIT) -> str:
    text = redact_secrets(str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
