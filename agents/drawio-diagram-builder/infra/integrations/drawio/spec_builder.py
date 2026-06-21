"""Build and refine diagram specs from source text."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from drawio_renderer import build_spec_from_text, compact_label


ACTION_WORDS = ("acessa", "chama", "grava", "consulta", "publica", "envia", "recebe", "valida", "confirma")


def build_specialized_spec(
    text: str,
    diagram_type: str | None,
    title: str | None = None,
    audience: str | None = None,
    detail_level: str | None = None,
) -> dict[str, Any]:
    normalized_type = (diagram_type or "flowchart").lower()
    if normalized_type in {"erd", "entity_relationship", "entity-relationship"}:
        return build_erd_spec(text, title=title, audience=audience, detail_level=detail_level)
    if normalized_type in {"architecture", "cloud_architecture", "c4_context", "c4_container", "c4_component"}:
        return build_architecture_spec(text, title=title, audience=audience, detail_level=detail_level)
    if normalized_type in {"flowchart", "user_journey", "service_blueprint", "runbook", "incident_flow", "approval_flow"}:
        return build_flow_spec(text, title=title, diagram_type=normalized_type, audience=audience, detail_level=detail_level)
    return build_spec_from_text(text, title=title, diagram_type=diagram_type, audience=audience, detail_level=detail_level)


def build_erd_spec(
    text: str,
    title: str | None = None,
    audience: str | None = None,
    detail_level: str | None = None,
) -> dict[str, Any]:
    entities: dict[str, dict[str, Any]] = {}
    statements = split_statements(text)
    for statement in statements:
        match = re.search(r"\b(?:tabela|entidade)\s+([A-Za-z0-9_ -]+?)\s+(?:possui|tem|com)\s+(.+)", statement, re.I)
        if not match:
            continue
        name = normalize_entity_name(match.group(1))
        attributes = parse_attributes(match.group(2))
        entities[name] = {
            "id": name,
            "label": name,
            "group": "Entidades",
            "kind": "entity",
            "attributes": attributes,
            "description": statement,
        }

    if not entities:
        generic = build_spec_from_text(text, title=title, diagram_type="erd", audience=audience, detail_level=detail_level)
        generic["diagram_type"] = "erd"
        return generic

    edges: list[dict[str, Any]] = []
    for name, entity in entities.items():
        for attr in entity.get("attributes", []):
            if attr.endswith("_id"):
                target = normalize_entity_name(attr[:-3])
                if target in entities and target != name:
                    edges.append({"source": name, "target": target, "label": f"{name}.{attr}"})
    for statement in statements:
        match = re.search(r"\b([A-Za-z0-9_ -]+?)\s+(?:pertence a|referencia|relaciona com)\s+([A-Za-z0-9_ -]+)", statement, re.I)
        if not match:
            continue
        source = normalize_entity_name(match.group(1))
        target = normalize_entity_name(match.group(2))
        if source in entities and target in entities and not edge_exists(edges, source, target):
            edges.append({"source": source, "target": target, "label": "pertence a"})

    return {
        "title": title or "Diagrama ERD",
        "diagram_type": "erd",
        "audience": audience or "tecnica e dados",
        "detail_level": detail_level or "medium",
        "facts": statements[:12],
        "assumptions": ["Relacionamentos inferidos por campos *_id e frases de pertencimento."],
        "open_questions": infer_open_questions(text),
        "nodes": list(entities.values()),
        "edges": edges,
    }


def build_architecture_spec(
    text: str,
    title: str | None = None,
    audience: str | None = None,
    detail_level: str | None = None,
) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    statements = split_statements(text)
    for statement in statements:
        relation = parse_relation(statement)
        if not relation:
            node = component_from_text(statement)
            nodes.setdefault(node["id"], node)
            continue
        source_label, action, target_label = relation
        source = component_node(source_label)
        target = component_node(target_label)
        nodes.setdefault(source["id"], source)
        nodes.setdefault(target["id"], target)
        edges.append({"source": source["id"], "target": target["id"], "label": action})

    return {
        "title": title or "Arquitetura",
        "diagram_type": "architecture",
        "audience": audience or "tecnica e negocio",
        "detail_level": detail_level or "medium",
        "facts": statements[:12],
        "assumptions": ["Componentes e integracoes inferidos por verbos de acao entre termos."],
        "open_questions": infer_open_questions(text),
        "nodes": list(nodes.values()) or build_spec_from_text(text, diagram_type="architecture").get("nodes", []),
        "edges": edges,
    }


def build_flow_spec(
    text: str,
    title: str | None = None,
    diagram_type: str = "flowchart",
    audience: str | None = None,
    detail_level: str | None = None,
) -> dict[str, Any]:
    statements = split_statements(text)
    nodes = []
    for index, statement in enumerate(statements[:12] or ["Contexto nao informado"], start=1):
        nodes.append(
            {
                "id": f"step-{index}",
                "label": compact_label(statement),
                "group": flow_group(statement),
                "kind": "decision" if is_decision(statement) else "process",
                "description": statement,
            }
        )
    edges = [
        {"source": nodes[index]["id"], "target": nodes[index + 1]["id"], "label": "proximo"}
        for index in range(len(nodes) - 1)
    ]
    return {
        "title": title or "Fluxo",
        "diagram_type": diagram_type,
        "audience": audience or "produto, negocio e tecnologia",
        "detail_level": detail_level or "medium",
        "facts": statements[:12],
        "assumptions": ["Fluxo inferido pela ordem das etapas no material fonte."],
        "open_questions": infer_open_questions(text),
        "nodes": nodes,
        "edges": edges,
    }


def apply_feedback_to_spec(spec: dict[str, Any], feedback: str) -> tuple[dict[str, Any], list[str]]:
    refined = deepcopy(spec)
    changes: list[str] = []
    rename_match = re.search(r"renomeie\s+(.+?)\s+para\s+(.+)", feedback, re.I)
    if rename_match:
        old = clean_phrase(rename_match.group(1))
        new = clean_phrase(rename_match.group(2))
        for node in refined.get("nodes", []):
            if node.get("label", "").lower() == old.lower() or node.get("id", "").lower() == old.lower():
                node["label"] = new
                changes.append(f"Renomeado `{old}` para `{new}`.")
    add_match = re.search(r"adicione\s+(.+)", feedback, re.I)
    if add_match:
        label = clean_phrase(add_match.group(1))
        node_id = slug(label)
        if not any(node.get("id") == node_id for node in refined.get("nodes", [])):
            refined.setdefault("nodes", []).append({"id": node_id, "label": label, "group": "Ajustes", "kind": "process"})
            changes.append(f"Adicionado no `{label}`.")
    remove_match = re.search(r"remova\s+(.+)", feedback, re.I)
    if remove_match:
        target = clean_phrase(remove_match.group(1)).lower()
        before = len(refined.get("nodes", []))
        refined["nodes"] = [node for node in refined.get("nodes", []) if node.get("label", "").lower() != target and node.get("id", "").lower() != target]
        removed_ids = {node.get("id") for node in spec.get("nodes", [])} - {node.get("id") for node in refined.get("nodes", [])}
        refined["edges"] = [edge for edge in refined.get("edges", []) if edge.get("source") not in removed_ids and edge.get("target") not in removed_ids]
        if len(refined.get("nodes", [])) != before:
            changes.append(f"Removido no `{target}`.")
    if not changes:
        refined.setdefault("refinement_notes", []).append(feedback)
        changes.append("Feedback registrado como nota por nao corresponder a uma regra automatica.")
    return refined, changes


def parse_relation(statement: str) -> tuple[str, str, str] | None:
    for action in ACTION_WORDS:
        match = re.search(rf"(.+?)\s+({action})\s+(.+)", statement, re.I)
        if match:
            return clean_phrase(match.group(1)), match.group(2).lower(), clean_phrase(match.group(3))
    return None


def component_node(label: str) -> dict[str, Any]:
    clean = clean_phrase(label)
    return {"id": slug(clean), "label": clean, "group": architecture_group(clean), "kind": architecture_kind(clean)}


def component_from_text(statement: str) -> dict[str, Any]:
    label = compact_label(statement)
    return {"id": slug(label), "label": label, "group": architecture_group(label), "kind": architecture_kind(label)}


def architecture_group(label: str) -> str:
    lowered = label.lower()
    if any(term in lowered for term in ["cliente", "usuario", "usuário", "ator"]):
        return "Atores"
    if any(term in lowered for term in ["app", "mobile", "web", "portal", "front"]):
        return "Canais"
    if any(term in lowered for term in ["banco", "postgres", "sql", "database", "dados"]):
        return "Dados"
    if any(term in lowered for term in ["externo", "terceiro", "parceiro"]):
        return "Externos"
    return "Servicos"


def architecture_kind(label: str) -> str:
    lowered = label.lower()
    if any(term in lowered for term in ["cliente", "usuario", "usuário"]):
        return "actor"
    if any(term in lowered for term in ["banco", "postgres", "database", "sql"]):
        return "database"
    return "system"


def flow_group(statement: str) -> str:
    lowered = statement.lower()
    if any(term in lowered for term in ["usuario", "usuário", "cliente"]):
        return "Usuario"
    if any(term in lowered for term in ["sistema", "api", "servico", "serviço"]):
        return "Sistema"
    return "Fluxo"


def is_decision(statement: str) -> bool:
    lowered = statement.lower()
    return lowered.startswith(("se ", "caso ", "quando ")) or " caso contrario" in lowered or "caso contrário" in lowered


def parse_attributes(value: str) -> list[str]:
    cleaned = re.sub(r"[.,;]", " ", value)
    return [part.strip().lower() for part in cleaned.split() if part.strip()]


def normalize_entity_name(value: str) -> str:
    return clean_phrase(value).split()[0].lower()


def clean_phrase(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value.replace("_", " ")).strip(" .;:,")
    return re.sub(r"^(?:no|na|nos|nas|em|ao|a)\s+", "", cleaned, flags=re.I)


def edge_exists(edges: list[dict[str, Any]], source: str, target: str) -> bool:
    return any(edge.get("source") == source and edge.get("target") == target for edge in edges)


def infer_open_questions(text: str) -> list[str]:
    lowered = (text or "").lower()
    questions: list[str] = []
    if "audiencia" not in lowered and "público" not in lowered and "publico" not in lowered:
        questions.append("Quem e a audiencia principal do diagrama?")
    if "escopo" not in lowered:
        questions.append("Qual e o escopo e o fora de escopo?")
    return questions


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip().lower()).strip("-") or "item"


def split_statements(text: str) -> list[str]:
    cleaned = re.sub(r"[#*`>\[\]{}]", " ", text or "")
    parts = re.split(r"(?:\n+|(?<=[.!?;])\s+)", cleaned)
    return [" ".join(part.split()) for part in parts if len(" ".join(part.split())) > 3]
