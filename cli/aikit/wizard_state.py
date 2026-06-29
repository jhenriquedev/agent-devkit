"""Persistent agentic setup wizard state."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.aikit.app_home import app_path, ensure_app_home
from cli.aikit.decision_store import set_decision
from cli.aikit.memory import redact_secrets
from cli.aikit.sources import SourceConfigBlockedError, SourceRegistryError, add_source


YES_VALUES = {"s", "sim", "y", "yes", "true", "1", "ok"}
NO_VALUES = {"n", "nao", "não", "no", "false", "0"}
ENV_VAR_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SOURCE_ID_PATTERN = re.compile(r"[^a-z0-9._-]+")


class WizardStateError(ValueError):
    """Raised for user-facing wizard state errors."""


def wizard_home() -> Path:
    ensure_app_home()
    path = app_path("state", "wizards")
    path.mkdir(parents=True, exist_ok=True)
    return path


def wizard_path(wizard_id: str) -> Path:
    validate_wizard_id(wizard_id)
    return wizard_home() / f"{wizard_id}.json"


def create_provider_wizard(
    setup_wizard: dict[str, Any],
    *,
    execution_plan: dict[str, Any] | None = None,
    route: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist a provider setup wizard and return its public representation."""
    now = now_iso()
    wizard_id = f"wiz-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    provider = str(setup_wizard.get("provider") or "provider")
    safe_setup = sanitize_setup_wizard(setup_wizard, wizard_id=wizard_id)
    first_question = safe_setup.get("next_question")
    pending_questions: list[dict[str, Any]] = []
    if isinstance(first_question, dict):
        pending_questions.append(dict(first_question))
    pending_questions.extend(dict(item) for item in safe_setup.get("questions") or [] if isinstance(item, dict))
    status = "denied-by-user" if safe_setup.get("status") == "denied-by-user" else "waiting-for-user"
    state = {
        "kind": "provider-setup-wizard-state",
        "schema_version": "ai-devkit.provider-wizard-state/v1",
        "id": wizard_id,
        "status": status,
        "provider": provider,
        "created_at": now,
        "updated_at": now,
        "setup_wizard": safe_setup,
        "execution_plan": sanitize_execution_plan(execution_plan),
        "route": sanitize_route(route),
        "pending_questions": pending_questions,
        "answered_questions": [],
        "answers": {},
        "source_result": None,
        "stored_secret": False,
    }
    save_state(state)
    return public_wizard(state)


def list_wizards(*, status: str | None = None) -> dict[str, Any]:
    items = [public_wizard(load_state(path.stem)) for path in wizard_home().glob("*.json")]
    if status:
        items = [item for item in items if item.get("status") == status]
    items.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
    return {
        "kind": "wizards",
        "status": "ok",
        "items": items,
        "home": str(wizard_home()),
        "stored_secret": False,
    }


def show_wizard(wizard_id: str) -> dict[str, Any]:
    return {
        "kind": "wizard",
        "status": "ok",
        "wizard": public_wizard(load_state(wizard_id)),
        "stored_secret": False,
    }


def cancel_wizard(wizard_id: str, *, reason: str | None = None) -> dict[str, Any]:
    state = load_state(wizard_id)
    state["status"] = "cancelled"
    state["updated_at"] = now_iso()
    state["cancel_reason"] = reason or "cancelled by user"
    state["pending_questions"] = []
    save_state(state)
    return {
        "kind": "wizard",
        "status": "cancelled",
        "wizard": public_wizard(state),
        "stored_secret": False,
    }


def answer_wizard(wizard_id: str, answer: str) -> dict[str, Any]:
    state = load_state(wizard_id)
    if state.get("status") in {"completed", "cancelled", "denied-by-user"}:
        return {
            "kind": "wizard",
            "status": str(state.get("status")),
            "wizard": public_wizard(state),
            "stored_secret": False,
        }
    question = current_question(state)
    if not question:
        return complete_wizard(state)

    parsed = parse_answer(question, answer)
    if is_opt_in_question(state, question):
        if not parsed:
            provider = str(state.get("provider") or "")
            set_decision("tools", provider, "denied_by_user", reason="agentic provider setup wizard opt-out")
            state["status"] = "denied-by-user"
            state["updated_at"] = now_iso()
            state["pending_questions"] = []
            append_answer(state, question, parsed)
            save_state(state)
            return {
                "kind": "wizard",
                "status": "denied-by-user",
                "wizard": public_wizard(state),
                "stored_secret": False,
            }
        pop_current_question(state)
        append_answer(state, question, parsed)
        state["status"] = "collecting-input"
        state["updated_at"] = now_iso()
        save_state(state)
        return {
            "kind": "wizard",
            "status": "needs-input",
            "wizard": public_wizard(state),
            "next_question": current_question(state),
            "stored_secret": False,
        }

    if is_skip_answer(question, parsed):
        provider = str(state.get("provider") or "")
        set_decision("tools", provider, "denied_by_user", reason="agentic provider setup wizard skipped")
        state["status"] = "denied-by-user"
        state["updated_at"] = now_iso()
        state["pending_questions"] = []
        append_answer(state, question, parsed)
        save_state(state)
        return {
            "kind": "wizard",
            "status": "denied-by-user",
            "wizard": public_wizard(state),
            "stored_secret": False,
        }

    additions = dynamic_questions_for_answer(state, question, parsed)
    pop_current_question(state)
    if additions:
        state["pending_questions"] = additions + list(state.get("pending_questions") or [])
    append_answer(state, question, parsed)
    state["updated_at"] = now_iso()
    if current_question(state):
        save_state(state)
        return {
            "kind": "wizard",
            "status": "needs-input",
            "wizard": public_wizard(state),
            "next_question": current_question(state),
            "stored_secret": False,
        }
    return complete_wizard(state)


def complete_wizard(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("source_result"):
        state["status"] = "completed"
        state["updated_at"] = now_iso()
        save_state(state)
        return {"kind": "wizard", "status": "completed", "wizard": public_wizard(state), "stored_secret": False}
    try:
        source_result = create_source_from_wizard(state)
    except SourceConfigBlockedError as exc:
        state["status"] = "failed"
        state["updated_at"] = now_iso()
        state["error"] = str(exc)
        state["source_result"] = exc.payload
        save_state(state)
        return {
            "kind": "wizard",
            "status": "failed",
            "wizard": public_wizard(state),
            "source_result": exc.payload,
            "error": str(exc),
            "stored_secret": False,
        }
    except SourceRegistryError as exc:
        state["status"] = "failed"
        state["updated_at"] = now_iso()
        state["error"] = str(exc)
        save_state(state)
        return {
            "kind": "wizard",
            "status": "failed",
            "wizard": public_wizard(state),
            "error": str(exc),
            "stored_secret": False,
        }
    state["status"] = "completed"
    state["updated_at"] = now_iso()
    state["source_result"] = source_result
    save_state(state)
    return {
        "kind": "wizard",
        "status": "completed",
        "wizard": public_wizard(state),
        "source_result": source_result,
        "resume_prompt": resume_prompt(state),
        "stored_secret": False,
    }


def create_source_from_wizard(state: dict[str, Any]) -> dict[str, Any]:
    provider = str(state.get("provider") or "")
    answers = answer_map(state)
    source_id = str(answers.get("source_id") or suggested_source_id(state)).strip()
    source_id = normalize_source_id(source_id or provider)
    intent = str((state.get("setup_wizard") or {}).get("intent") or "").strip()
    agent_id = str((state.get("setup_wizard") or {}).get("agent_id") or "").strip()
    config_pairs: list[str] = []
    env_refs: list[str] = []
    env_files: list[str] = []

    for record in state.get("answered_questions") or []:
        question = record.get("question") if isinstance(record, dict) else None
        if not isinstance(question, dict):
            continue
        value = record.get("answer")
        if value in {None, ""}:
            continue
        if question.get("config_key") and not question.get("secret"):
            config_pairs.append(f"{question['config_key']}={value}")
        if question.get("env_ref_key"):
            env_key = str(question["env_ref_key"])
            env_value = str(value)
            if not ENV_VAR_NAME_PATTERN.fullmatch(env_value):
                raise SourceRegistryError("credential answers must be environment variable names, not raw secret values")
            if redact_secrets(env_value) != env_value:
                raise SourceRegistryError("credential answers must not contain raw secret values")
            env_refs.append(f"{env_key}={env_value}")
        if question.get("env_file"):
            env_files.append(str(value))

    default_for: list[str] = []
    default_for_agent: list[str] = []
    if answers.get("default_for_intent") is True and intent:
        default_for.append(intent)
    if agent_id:
        default_for_agent.append(agent_id)

    return add_source(
        source_id,
        provider=provider,
        label=source_id,
        config_pairs=config_pairs,
        env_refs=env_refs,
        env_files=env_files,
        default_for=default_for,
        default_for_agent=default_for_agent,
        set_default=True,
    )


def current_question(state: dict[str, Any]) -> dict[str, Any] | None:
    questions = state.get("pending_questions") if isinstance(state.get("pending_questions"), list) else []
    if not questions:
        return None
    question = questions[0]
    return dict(question) if isinstance(question, dict) else None


def pop_current_question(state: dict[str, Any]) -> None:
    questions = state.get("pending_questions") if isinstance(state.get("pending_questions"), list) else []
    state["pending_questions"] = list(questions[1:])


def append_answer(state: dict[str, Any], question: dict[str, Any], answer: Any) -> None:
    state.setdefault("answered_questions", []).append(
        {
            "question": dict(question),
            "answer": public_answer(question, answer),
            "answered_at": now_iso(),
        }
    )
    state.setdefault("answers", {})[str(question.get("id") or len(state["answered_questions"]))] = public_answer(question, answer)


def parse_answer(question: dict[str, Any], answer: str) -> Any:
    raw = " ".join(str(answer or "").split())
    if not raw and question.get("default") is not None:
        return question.get("default")
    if not raw and question.get("suggested_value"):
        return question.get("suggested_value")
    if question.get("env_ref_key"):
        if not ENV_VAR_NAME_PATTERN.fullmatch(raw):
            raise WizardStateError("informe o nome de uma variavel de ambiente, nao o valor bruto da credencial")
        if redact_secrets(raw) != raw:
            raise WizardStateError("informe uma referencia segura de credencial, nao o valor bruto do segredo")
        return raw
    if question.get("type") == "confirm":
        lowered = raw.lower()
        if lowered in YES_VALUES:
            return True
        if lowered in NO_VALUES:
            return False
        raise WizardStateError("responda sim ou nao")
    if question.get("type") == "select":
        options = [str(item) for item in question.get("options") or []]
        if raw not in options:
            raise WizardStateError(f"resposta invalida. opcoes: {', '.join(options)}")
        return raw
    if not raw and question.get("required"):
        raise WizardStateError("resposta obrigatoria")
    return raw


def dynamic_questions_for_answer(state: dict[str, Any], question: dict[str, Any], answer: Any) -> list[dict[str, Any]]:
    if question.get("type") != "select" or not str(question.get("id") or "").endswith("_auth"):
        return []
    provider = str(state.get("provider") or "provider")
    setup = state.get("setup_wizard") if isinstance(state.get("setup_wizard"), dict) else {}
    auth_methods = setup.get("auth_methods") if isinstance(setup.get("auth_methods"), list) else []
    selected = str(answer)
    if selected == "file":
        return [
            {
                "id": f"{provider_slug(provider)}_credential_file",
                "type": "text",
                "text": "Qual e o caminho do arquivo local com a credencial?",
                "env_file": True,
                "required": True,
                "secret": False,
            }
        ]
    if selected in {"env"} | {str(method.get("id")) for method in auth_methods if isinstance(method, dict)}:
        secret_fields: list[str] = []
        for method in auth_methods:
            if not isinstance(method, dict):
                continue
            if selected != "env" and method.get("id") != selected:
                continue
            secret_fields.extend(str(item) for item in method.get("secret_fields") or [])
        if selected == "env" and not secret_fields:
            for option in setup.get("credential_options") or []:
                if isinstance(option, dict) and option.get("env"):
                    secret_fields.append(str(option["env"]))
        unique = []
        for field in secret_fields:
            if field and field not in unique:
                unique.append(field)
        return [
            {
                "id": f"{provider_slug(provider)}_{provider_slug(field)}_env_ref",
                "type": "text",
                "text": f"Qual variavel de ambiente contem {field}?",
                "env_ref_key": field,
                "required": True,
                "secret": True,
                "stores_secret": False,
                "suggested_value": field,
            }
            for field in unique
        ]
    return []


def is_opt_in_question(state: dict[str, Any], question: dict[str, Any]) -> bool:
    expected = ((state.get("setup_wizard") or {}).get("next_question") or {}).get("id") if isinstance(state.get("setup_wizard"), dict) else None
    return bool(expected and question.get("id") == expected)


def is_skip_answer(question: dict[str, Any], answer: Any) -> bool:
    return question.get("type") == "select" and str(answer) == "skip"


def answer_map(state: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for record in state.get("answered_questions") or []:
        if not isinstance(record, dict):
            continue
        question = record.get("question")
        if isinstance(question, dict):
            result[str(question.get("id"))] = record.get("answer")
    return result


def public_answer(question: dict[str, Any], answer: Any) -> Any:
    if question.get("env_ref_key"):
        return str(answer)
    if question.get("secret") and not question.get("env_ref_key"):
        return "[REDACTED]"
    return answer


def public_wizard(state: dict[str, Any]) -> dict[str, Any]:
    setup = state.get("setup_wizard") if isinstance(state.get("setup_wizard"), dict) else {}
    question = current_question(state)
    wizard = dict(setup)
    wizard.update(
        {
            "wizard_id": state.get("id"),
            "status": state.get("status"),
            "provider": state.get("provider") or setup.get("provider"),
            "state_path": str(wizard_path(str(state.get("id")))),
            "created_at": state.get("created_at"),
            "updated_at": state.get("updated_at"),
            "answered_count": len(state.get("answered_questions") or []),
            "pending_count": len(state.get("pending_questions") or []),
            "next_question": question,
            "resume_prompt": resume_prompt(state),
            "stored_secret": False,
        }
    )
    if state.get("source_result"):
        wizard["source"] = (state["source_result"].get("source") if isinstance(state["source_result"], dict) else None)
    if state.get("error"):
        wizard["error"] = state.get("error")
    return wizard


def resume_prompt(state: dict[str, Any]) -> str | None:
    setup = state.get("setup_wizard") if isinstance(state.get("setup_wizard"), dict) else {}
    prompt = setup.get("resume_prompt")
    return str(prompt) if prompt else None


def suggested_source_id(state: dict[str, Any]) -> str:
    setup = state.get("setup_wizard") if isinstance(state.get("setup_wizard"), dict) else {}
    return str(setup.get("suggested_source_id") or state.get("provider") or "source")


def sanitize_setup_wizard(setup_wizard: dict[str, Any], *, wizard_id: str) -> dict[str, Any]:
    safe = json.loads(json.dumps(setup_wizard, ensure_ascii=False))
    if safe.get("resume_prompt"):
        safe["resume_prompt"] = redact_secrets(str(safe["resume_prompt"]))
    safe["wizard_id"] = wizard_id
    safe["state_path"] = str(wizard_path(wizard_id))
    safe["stored_secret"] = False
    return safe


def sanitize_execution_plan(execution_plan: dict[str, Any] | None) -> dict[str, Any] | None:
    if not execution_plan:
        return None
    safe = json.loads(json.dumps(execution_plan, ensure_ascii=False))
    if safe.get("prompt"):
        safe["prompt"] = redact_secrets(str(safe["prompt"]))
    return safe


def sanitize_route(route: dict[str, Any] | None) -> dict[str, Any] | None:
    if not route:
        return None
    return json.loads(json.dumps(route, ensure_ascii=False))


def save_state(state: dict[str, Any]) -> Path:
    path = wizard_path(str(state["id"]))
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_state(wizard_id: str) -> dict[str, Any]:
    path = wizard_path(wizard_id)
    if not path.exists():
        raise WizardStateError(f"wizard not found: {wizard_id}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WizardStateError(f"invalid wizard state: {wizard_id}") from exc
    if not isinstance(data, dict):
        raise WizardStateError(f"invalid wizard state: {wizard_id}")
    return data


def normalize_source_id(value: str) -> str:
    normalized = SOURCE_ID_PATTERN.sub("-", value.lower()).strip("-")
    return normalized or "source"


def validate_wizard_id(wizard_id: str) -> None:
    if not re.fullmatch(r"wiz-[0-9]{14}-[a-f0-9]{8}", str(wizard_id or "")):
        raise WizardStateError("invalid wizard id")


def provider_slug(provider: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", provider.lower()).strip("_") or "provider"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
