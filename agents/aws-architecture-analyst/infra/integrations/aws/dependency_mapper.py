#!/usr/bin/env python3
"""Build dependency maps from normalized AWS resources."""

from __future__ import annotations

from typing import Any


def build_dependency_map(resources: list[dict[str, Any]]) -> dict[str, Any]:
    resource_ids = {item.get("id") for item in resources}
    edges: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    for resource in resources:
        source_id = resource.get("id")
        for relationship in resource.get("relationships") or []:
            target_id = relationship.get("target_id")
            edge = {
                "source_id": source_id,
                "target_id": target_id,
                "type": relationship.get("type") or "depends-on",
                "confidence": relationship.get("confidence") or "inferred",
                "evidence": relationship.get("evidence"),
            }
            if target_id in resource_ids or str(target_id).startswith("arn:"):
                edges.append(edge)
            else:
                unresolved.append(edge)

    return {
        "nodes": resources,
        "edges": edges,
        "edge_count": len(edges),
        "unresolved_dependencies": unresolved,
        "unresolved_count": len(unresolved),
    }


def estimate_blast_radius(
    *,
    resource_id: str,
    resources: list[dict[str, Any]],
    dependency_map: dict[str, Any],
) -> dict[str, Any]:
    by_id = {item.get("id"): item for item in resources}
    reverse: dict[str, list[dict[str, Any]]] = {}
    for edge in dependency_map.get("edges") or []:
        reverse.setdefault(edge.get("target_id"), []).append(edge)

    direct_edges = reverse.get(resource_id, [])
    direct_dependents = [edge.get("source_id") for edge in direct_edges]
    indirect: set[str] = set()
    frontier = list(direct_dependents)
    while frontier:
        current = frontier.pop()
        for edge in reverse.get(current, []):
            source = edge.get("source_id")
            if source and source not in indirect and source != resource_id:
                indirect.add(source)
                frontier.append(source)

    return {
        "resource_id": resource_id,
        "resource": by_id.get(resource_id),
        "direct_dependents": direct_dependents,
        "indirect_dependents": sorted(indirect - set(direct_dependents)),
        "direct_count": len(direct_dependents),
        "indirect_count": len(indirect - set(direct_dependents)),
        "unsafe_actions": [
            "alterar ou remover recurso sem validar dependentes diretos",
            "assumir impacto baixo quando existem dependencias nao resolvidas",
        ],
    }
