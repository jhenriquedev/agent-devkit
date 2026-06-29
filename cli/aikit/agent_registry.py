"""Agent and capability registry helpers for orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.aikit.write_policy import normalize_write_policy, write_policy_public_fields


def load_agent_registry(root: Path) -> dict[str, Any]:
    agents_dir = root / "agents"
    agents: dict[str, dict[str, Any]] = {}
    capabilities: dict[str, dict[str, Any]] = {}
    runtime_roles: dict[str, str] = {}
    if not agents_dir.exists():
        return {"agents": agents, "capabilities": capabilities, "runtime_roles": runtime_roles}
    provider_map = load_provider_capability_map(root)
    for agent_path in sorted(path for path in agents_dir.iterdir() if path.is_dir()):
        manifest_path = agent_path / "agent.yaml"
        if not manifest_path.exists():
            continue
        agent = read_yaml(manifest_path)
        agent_id = str(agent.get("id") or agent_path.name)
        agent["id"] = agent_id
        agent["path"] = str(agent_path.relative_to(root))
        agent["capabilities_index"] = {}
        for capability_path in sorted((agent_path / "capabilities").glob("*/capability.yaml")):
            capability = read_yaml(capability_path)
            capability_id = str(capability.get("id") or capability_path.parent.name)
            short_id = capability_id.rsplit(".", 1)[-1]
            runtime = normalize_runtime(capability.get("runtime"))
            provider_resolution = resolve_capability_provider(agent_id, short_id, capability, runtime, provider_map)
            source_contract = normalize_source_contract(capability.get("source"), runtime=runtime)
            public_capability = {
                "id": capability_id,
                "short_id": short_id,
                "agent_id": agent_id,
                "name": capability.get("name") or short_id,
                "purpose": compact(str(capability.get("purpose") or "")),
                "routing": normalize_routing(capability.get("routing")),
                "runtime": runtime,
                "runner": ((capability.get("entrypoint") or {}).get("runner")),
                "provider": provider_resolution.get("provider"),
                "provider_resolution": provider_resolution,
                "source": source_contract,
                "source_contract": source_contract,
                "write_policy": normalize_write_policy(capability.get("write_policy")),
                "write_policy_raw": capability.get("write_policy"),
                **write_policy_public_fields(capability.get("write_policy")),
                "inputs": capability.get("inputs") or {},
                "outputs": capability.get("outputs") or {},
                "integration": capability.get("integration") or {},
                "requires": capability.get("requires") or {},
                "has_runner": bool(((capability.get("entrypoint") or {}).get("runner"))),
                "path": str(capability_path.parent.relative_to(root)),
            }
            agent["capabilities_index"][short_id] = public_capability
            capabilities[f"{agent_id}/{short_id}"] = public_capability
        public = public_agent(agent)
        agents[agent_id] = public
        runtime_role = public.get("runtime_role") if isinstance(public.get("runtime_role"), dict) else {}
        role_kind = str(runtime_role.get("kind") or "").strip()
        if role_kind:
            runtime_roles.setdefault(role_kind, agent_id)
    return {"agents": agents, "capabilities": capabilities, "runtime_roles": runtime_roles}


def public_agent(agent: dict[str, Any]) -> dict[str, Any]:
    surface = agent.get("agent_surface") if isinstance(agent.get("agent_surface"), dict) else {}
    return {
        "id": agent.get("id"),
        "name": agent.get("name") or agent.get("id"),
        "kind": agent.get("kind"),
        "status": agent.get("status"),
        "version": agent.get("version"),
        "purpose": compact(str(agent.get("purpose") or "")),
        "routing": normalize_routing(agent.get("routing")),
        "runtime_role": normalize_runtime_role(agent.get("runtime_role")),
        "agent_mode": normalize_agent_mode(agent.get("agent_mode")),
        "depends_on_agents": list(agent.get("depends_on_agents") or []),
        "orchestrated_agents": list(surface.get("orchestrated_agents") or []),
        "capabilities": list(agent.get("capabilities") or []),
        "capabilities_index": dict(agent.get("capabilities_index") or {}),
        "write_policy": normalize_agent_write_policy(agent.get("write_policy")),
        "write_policy_raw": agent.get("write_policy"),
        "write_policy_metadata": normalize_agent_write_policy_metadata(agent.get("write_policy")),
        "path": agent.get("path"),
    }


def find_capability(registry: dict[str, Any], agent_id: str, capability_id: str) -> dict[str, Any] | None:
    return (registry.get("capabilities") or {}).get(f"{agent_id}/{capability_id}")


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to read Agent DevKit manifests. Install requirements.txt.") from exc
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def compact(value: str, *, limit: int = 240) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def normalize_agent_write_policy(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): normalize_write_policy(policy) for key, policy in value.items()}
    if value:
        return normalize_write_policy(value)
    return value


def normalize_agent_write_policy_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): write_policy_public_fields(policy)["write_policy_metadata"] for key, policy in value.items()}
    if value:
        return write_policy_public_fields(value)["write_policy_metadata"]
    return value


def normalize_routing(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        "aliases": normalize_routing_strings(value.get("aliases")),
        "anchors": normalize_routing_strings(value.get("anchors")),
        "domains": normalize_routing_strings(value.get("domains")),
        "entities": normalize_routing_strings(value.get("entities")),
        "intents": normalize_routing_strings(value.get("intents")),
        "keywords": normalize_routing_strings(value.get("keywords")),
        "examples": normalize_routing_strings(value.get("examples")),
        "priority": value.get("priority", 0),
    }


def normalize_routing_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def normalize_runtime_role(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    kind = str(value.get("kind") or "").strip()
    if not kind:
        return {}
    role: dict[str, Any] = {"kind": kind}
    description = str(value.get("description") or "").strip()
    if description:
        role["description"] = compact(description)
    return role


def normalize_agent_mode(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    mode_type = str(value.get("type") or "").strip()
    if not mode_type:
        return {}
    can_call_llm = value.get("can_call_llm")
    normalized_llm: bool | str = False if can_call_llm is False else str(can_call_llm if can_call_llm is not None else "optional")
    return {
        "type": mode_type,
        "max_steps": positive_int(value.get("max_steps"), default=5),
        "max_specialists": positive_int(value.get("max_specialists"), default=5),
        "max_llm_calls": positive_int(value.get("max_llm_calls"), default=0, allow_zero=True),
        "timeout_seconds": positive_int(value.get("timeout_seconds"), default=300),
        "can_call_capabilities": value.get("can_call_capabilities") is True,
        "can_call_llm": normalized_llm,
        "can_request_user_input": value.get("can_request_user_input") is True,
        "external_writes": value.get("external_writes") is True,
        "allowed_capabilities": normalize_string_list(value.get("allowed_capabilities")),
        "stop_conditions": normalize_string_list(value.get("stop_conditions")),
    }


def positive_int(value: Any, *, default: int, allow_zero: bool = False) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if allow_zero and parsed == 0:
        return 0
    return parsed if parsed > 0 else default


def normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def normalize_runtime(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    runtime: dict[str, Any] = {}
    provider = str(value.get("provider") or "").strip()
    if provider:
        runtime["provider"] = provider
    source = value.get("source") if isinstance(value.get("source"), dict) else None
    if source:
        normalized_source: dict[str, Any] = {"enabled": source.get("enabled") is True}
        for key in ("args", "env"):
            mapping = source.get(key)
            if isinstance(mapping, dict):
                normalized_source[key] = {
                    str(item_key): str(item_value)
                    for item_key, item_value in mapping.items()
                    if str(item_key).strip() and str(item_value).strip()
                }
        runtime["source"] = normalized_source
    return runtime


def normalize_source_contract(value: Any, *, runtime: dict[str, Any] | None = None) -> dict[str, Any]:
    if isinstance(value, dict):
        return normalize_declared_source_contract(value, origin="source")
    runtime_source = (runtime or {}).get("source") if isinstance(runtime, dict) else None
    if isinstance(runtime_source, dict):
        normalized = normalize_declared_source_contract(runtime_source, origin="runtime.source")
        if "supported" not in normalized and "enabled" in normalized:
            normalized["supported"] = bool(normalized["enabled"])
        if "enabled" not in normalized and "supported" in normalized:
            normalized["enabled"] = bool(normalized["supported"])
        return normalized
    return {"enabled": False, "supported": False, "args": {}, "env": {}}


def normalize_declared_source_contract(value: dict[str, Any], *, origin: str) -> dict[str, Any]:
    enabled = value.get("enabled")
    supported = value.get("supported")
    is_enabled = enabled is True or supported is True
    contract: dict[str, Any] = {
        "enabled": is_enabled,
        "supported": is_enabled,
        "args": normalize_string_map(value.get("args")),
        "env": normalize_string_map(value.get("env")),
        "origin": origin,
    }
    mappings = value.get("mappings")
    if mappings is None:
        mappings = value.get("apply")
    if isinstance(mappings, list):
        normalized_mappings = []
        for item in mappings:
            if not isinstance(item, dict):
                continue
            field = str(item.get("field") or item.get("name") or "").strip()
            if not field:
                continue
            arg = str(item.get("arg") or "").strip()
            env = str(item.get("env") or "").strip()
            mapping: dict[str, str] = {"field": field}
            if arg:
                contract["args"][field] = arg
                mapping["arg"] = arg
            if env:
                contract["env"][field] = env
                mapping["env"] = env
            if len(mapping) > 1:
                normalized_mappings.append(mapping)
        contract["mappings"] = normalized_mappings
    return contract


def normalize_string_map(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        str(item_key): str(item_value)
        for item_key, item_value in value.items()
        if str(item_key).strip() and str(item_value).strip()
    }


def resolve_capability_provider(
    agent_id: str,
    short_id: str,
    capability: dict[str, Any],
    runtime: dict[str, Any],
    provider_map: dict[str, str],
) -> dict[str, Any]:
    if runtime.get("provider"):
        return {"provider": str(runtime["provider"]), "source": "runtime", "inferred": False}
    requires = capability.get("requires") if isinstance(capability.get("requires"), dict) else {}
    providers = requires.get("providers") if isinstance(requires.get("providers"), list) else []
    if providers and isinstance(providers[0], dict) and providers[0].get("id"):
        return {"provider": str(providers[0]["id"]), "source": "requires", "inferred": False}
    integration = capability.get("integration") if isinstance(capability.get("integration"), dict) else {}
    if integration.get("provider"):
        return {"provider": str(integration["provider"]), "source": "integration", "inferred": False}
    provider = provider_map.get(f"{agent_id}/{short_id}") or provider_map.get(agent_id)
    if provider:
        return {"provider": provider, "source": "provider-registry", "inferred": True}
    return {"provider": None, "source": "none", "inferred": False}


def load_provider_capability_map(root: Path) -> dict[str, str]:
    providers_dir = root / "providers"
    provider_map: dict[str, str] = {}
    if not providers_dir.is_dir():
        return provider_map
    for provider_path in sorted(providers_dir.glob("*.yaml")):
        provider = read_yaml(provider_path)
        provider_id = str(provider.get("id") or "").strip()
        capabilities = provider.get("capabilities") if isinstance(provider.get("capabilities"), dict) else {}
        if not provider_id or not capabilities:
            continue
        for declared in list(capabilities.get("read") or []) + list(capabilities.get("write") or []):
            declared_id = str(declared or "").strip()
            if declared_id:
                provider_map.setdefault(declared_id, provider_id)
    return provider_map
