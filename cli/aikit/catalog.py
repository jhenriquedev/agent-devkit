"""Deterministic searchable catalog over Agent DevKit registries."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cli.aikit.agent_registry import load_agent_registry
from cli.aikit.errors import DevKitError
from cli.aikit.providers import ProviderRegistryError, list_providers
from cli.aikit.runtime_paths import ROOT


CATALOG_SCHEMA_VERSION = "agent-devkit.catalog/v1"


def catalog_list(root: Path | None = None, *, item_type: str | None = None) -> dict[str, Any]:
    root = root or ROOT
    items = catalog_items(root)
    if item_type:
        items = [item for item in items if item["type"] == item_type]
    return {
        "kind": "catalog",
        "schema_version": CATALOG_SCHEMA_VERSION,
        "status": "ok",
        "action": "list",
        "query": None,
        "type": item_type,
        "count": len(items),
        "items": items,
    }


def catalog_search(query: str, root: Path | None = None, *, item_type: str | None = None) -> dict[str, Any]:
    root = root or ROOT
    query = (query or "").strip()
    if not query:
        raise DevKitError("catalog search requires a query")
    tokens = tokenize(query)
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in catalog_items(root):
        if item_type and item["type"] != item_type:
            continue
        score = match_score(item, tokens)
        if score > 0:
            enriched = dict(item)
            enriched["score"] = score
            scored.append((score, enriched))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["type"], pair[1]["id"]))
    return {
        "kind": "catalog",
        "schema_version": CATALOG_SCHEMA_VERSION,
        "status": "ok",
        "action": "search",
        "query": query,
        "type": item_type,
        "count": len(scored),
        "items": [item for _score, item in scored],
    }


def catalog_show(item_id: str, root: Path | None = None, *, item_type: str | None = None) -> dict[str, Any]:
    root = root or ROOT
    item_id = (item_id or "").strip()
    if not item_id:
        raise DevKitError("catalog show requires an item id")
    for item in catalog_items(root):
        if item_type and item["type"] != item_type:
            continue
        aliases = {item["id"], item.get("short_id"), item.get("qualified_id")}
        if item_id in {str(alias) for alias in aliases if alias}:
            return {
                "kind": "catalog-item",
                "schema_version": CATALOG_SCHEMA_VERSION,
                "status": "ok",
                "item": item,
            }
    suffix = f" of type {item_type}" if item_type else ""
    raise DevKitError(f"catalog item not found{suffix}: {item_id}")


def catalog_items(root: Path) -> list[dict[str, Any]]:
    registry = load_agent_registry(root)
    items: list[dict[str, Any]] = []
    for agent in sorted((registry.get("agents") or {}).values(), key=lambda item: str(item.get("id") or "")):
        if isinstance(agent, dict):
            items.append(agent_item(agent))
    for capability in sorted((registry.get("capabilities") or {}).values(), key=lambda item: str(item.get("id") or "")):
        if isinstance(capability, dict):
            items.append(capability_item(capability))
    items.extend(provider_items(root))
    return items


def agent_item(agent: dict[str, Any]) -> dict[str, Any]:
    capability_count = len(agent.get("capabilities_index") or {})
    return {
        "id": str(agent.get("id") or ""),
        "type": "agent",
        "description": agent.get("purpose") or "",
        "status": agent.get("status"),
        "version": agent.get("version"),
        "path": agent.get("path"),
        "write_policy": agent.get("write_policy"),
        "write_policy_metadata": agent.get("write_policy_metadata"),
        "source_contract": None,
        "providers_required": [],
        "runner": None,
        "agent_mode": agent.get("agent_mode") or {},
        "routing": agent.get("routing") or {},
        "prompt_examples": (agent.get("routing") or {}).get("examples") or [],
        "readiness": {
            "status": "ready" if capability_count else "empty",
            "capabilities": capability_count,
        },
    }


def capability_item(capability: dict[str, Any]) -> dict[str, Any]:
    provider = capability.get("provider")
    requires = capability.get("requires") if isinstance(capability.get("requires"), dict) else {}
    providers_required = [
        str(item.get("id"))
        for item in requires.get("providers", [])
        if isinstance(item, dict) and item.get("id")
    ]
    if provider and provider not in providers_required:
        providers_required.insert(0, str(provider))
    short_id = str(capability.get("short_id") or str(capability.get("id") or "").rsplit(".", 1)[-1])
    agent_id = str(capability.get("agent_id") or "")
    return {
        "id": f"{agent_id}/{short_id}",
        "qualified_id": capability.get("id"),
        "short_id": short_id,
        "type": "capability",
        "agent": agent_id,
        "description": capability.get("purpose") or "",
        "status": capability.get("status"),
        "version": capability.get("version"),
        "path": capability.get("path"),
        "write_policy": capability.get("write_policy"),
        "write_policy_metadata": capability.get("write_policy_metadata"),
        "source_contract": capability.get("source_contract") or capability.get("source"),
        "providers_required": providers_required,
        "runner": capability.get("runner") or (capability.get("runtime") or {}).get("runner"),
        "agent_mode": None,
        "routing": capability.get("routing") or {},
        "prompt_examples": (capability.get("routing") or {}).get("examples") or [],
        "readiness": {
            "status": "ready" if capability.get("has_runner") else "contract-only",
            "has_runner": capability.get("has_runner") is True,
            "has_source_contract": bool((capability.get("source_contract") or {}).get("supported")),
        },
    }


def provider_items(root: Path) -> list[dict[str, Any]]:
    try:
        payload = list_providers(root)
    except ProviderRegistryError:
        return []
    items = []
    for provider in payload.get("items") or []:
        if not isinstance(provider, dict):
            continue
        items.append(
            {
                "id": str(provider.get("id") or ""),
                "type": "provider",
                "description": provider.get("description") or provider.get("purpose") or "",
                "status": provider.get("status"),
                "version": provider.get("version"),
                "path": provider.get("path"),
                "write_policy": "read_only",
                "source_contract": None,
                "providers_required": [],
                "runner": None,
                "agent_mode": None,
                "routing": {},
                "prompt_examples": [],
                "readiness": {"status": provider.get("status") or "unknown"},
            }
        )
    return items


def tokenize(value: str) -> set[str]:
    tokens = {token for token in re.findall(r"[a-z0-9]+", value.lower()) if token}
    return expand_query_tokens(tokens)


def searchable_text(item: dict[str, Any]) -> str:
    routing = item.get("routing") if isinstance(item.get("routing"), dict) else {}
    routing_parts: list[str] = []
    for value in routing.values():
        if isinstance(value, list):
            routing_parts.extend(str(part) for part in value)
    return " ".join(
        [
            str(item.get("id") or ""),
            str(item.get("qualified_id") or ""),
            str(item.get("short_id") or ""),
            str(item.get("agent") or ""),
            str(item.get("description") or ""),
            " ".join(routing_parts),
            " ".join(str(item) for item in item.get("providers_required") or []),
        ]
    ).lower()


def item_tokens(item: dict[str, Any]) -> set[str]:
    tokens = {token for token in re.findall(r"[a-z0-9]+", searchable_text(item)) if token}
    tokens.update(expand_item_phrases(searchable_text(item)))
    return tokens


def match_score(item: dict[str, Any], tokens: set[str]) -> int:
    indexed_tokens = item_tokens(item)
    score = 0
    for token in tokens:
        if token in indexed_tokens:
            score += 3
        elif len(token) >= 3 and any(indexed.startswith(token) for indexed in indexed_tokens):
            score += 1
        if str(item.get("id") or "").lower() == token:
            score += 5
    return score


def expand_query_tokens(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    if expanded & {"pr", "prs"}:
        expanded.update({"pr", "prs", "pull-request"})
    if "rls" in expanded:
        expanded.update({"rls", "row", "level", "security", "row-level-security"})
    return expanded


def expand_item_phrases(text: str) -> set[str]:
    phrases = set()
    if "pull request" in text or "pull-request" in text or " pr " in f" {text} " or " prs " in f" {text} ":
        phrases.update({"pr", "prs", "pull-request"})
    if "row level security" in text or "row-level-security" in text or " rls " in f" {text} ":
        phrases.update({"rls", "row-level-security"})
    return phrases
