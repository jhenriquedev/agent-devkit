"""Validators for Draw.io diagrams."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


def validate_spec_against_schema(spec: dict[str, Any], schema_path: str | Path | None = None) -> list[str]:
    """Validate a diagram spec dict against diagram-spec.schema.json.

    Returns a list of error messages (empty list = valid).
    Uses a lightweight built-in check so there is no jsonschema dependency.
    """
    errors: list[str] = []
    if not isinstance(spec, dict):
        errors.append("Spec deve ser um objeto JSON.")
        return errors

    required_fields = ["title", "diagram_type", "nodes"]
    for field in required_fields:
        if field not in spec:
            errors.append(f"Campo obrigatório ausente na spec: '{field}'.")

    if "title" in spec and not isinstance(spec["title"], str):
        errors.append("Campo 'title' deve ser string.")
    if "diagram_type" in spec and not isinstance(spec["diagram_type"], str):
        errors.append("Campo 'diagram_type' deve ser string.")
    if "nodes" in spec:
        if not isinstance(spec["nodes"], list):
            errors.append("Campo 'nodes' deve ser array.")
        else:
            for index, node in enumerate(spec["nodes"]):
                if not isinstance(node, dict):
                    errors.append(f"Node[{index}] deve ser objeto.")
                    continue
                if "id" not in node:
                    errors.append(f"Node[{index}] sem campo 'id'.")
                if "label" not in node:
                    errors.append(f"Node[{index}] sem campo 'label'.")
    if "edges" in spec:
        if not isinstance(spec["edges"], list):
            errors.append("Campo 'edges' deve ser array.")
        else:
            node_ids = {str(n.get("id")) for n in spec.get("nodes", []) if isinstance(n, dict)}
            for index, edge in enumerate(spec["edges"]):
                if not isinstance(edge, dict):
                    errors.append(f"Edge[{index}] deve ser objeto.")
                    continue
                if "source" not in edge:
                    errors.append(f"Edge[{index}] sem campo 'source'.")
                if "target" not in edge:
                    errors.append(f"Edge[{index}] sem campo 'target'.")
                src = str(edge.get("source", ""))
                tgt = str(edge.get("target", ""))
                if src and node_ids and src not in node_ids:
                    errors.append(f"Edge[{index}] source '{src}' não existe nos nodes.")
                if tgt and node_ids and tgt not in node_ids:
                    errors.append(f"Edge[{index}] target '{tgt}' não existe nos nodes.")
    return errors


def validate_drawio(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    return validate_drawio_text(text)


def validate_drawio_text(text: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        return {"valid": False, "errors": [f"XML invalido: {exc}"], "warnings": [], "node_count": 0, "edge_count": 0}

    if root.tag != "mxfile":
        errors.append("Raiz mxfile ausente.")
    graph_root = root.find(".//root")
    if graph_root is None:
        errors.append("mxGraphModel/root ausente.")
        return {"valid": False, "errors": errors, "warnings": warnings, "node_count": 0, "edge_count": 0}

    cells = graph_root.findall("mxCell")
    vertices = [cell for cell in cells if cell.get("vertex") == "1"]
    edges = [cell for cell in cells if cell.get("edge") == "1"]
    cell_ids = [cell.get("id") for cell in cells]
    ids = set(cell_ids)
    if len(ids) != len(cell_ids):
        errors.append("IDs duplicados encontrados no diagrama.")
    content_vertices = [cell for cell in vertices if cell.get("id") not in {"diagram-title", "diagram-legend"} and not str(cell.get("id", "")).startswith("group-")]

    if not content_vertices:
        warnings.append("Nenhum no de conteudo encontrado.")
    for cell in content_vertices:
        if not (cell.get("value") or "").strip():
            errors.append(f"No sem label: {cell.get('id')}")
        geometry = cell.find("mxGeometry")
        if geometry is None or geometry.get("x") is None or geometry.get("y") is None:
            errors.append(f"No sem geometria posicionada: {cell.get('id')}")

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            errors.append(f"Conector sem source/target: {edge.get('id')}")
        if source and source not in ids:
            errors.append(f"Conector referencia source inexistente: {source}")
        if target and target not in ids:
            errors.append(f"Conector referencia target inexistente: {target}")
        if not (edge.get("value") or "").strip():
            warnings.append(f"Conector sem label: {edge.get('id')}")

    overlaps = find_overlaps(content_vertices)
    if overlaps:
        warnings.extend(f"Nos sobrepostos: {left} e {right}" for left, right in overlaps)

    if root.find(".//mxCell[@id='diagram-title']") is None:
        warnings.append("Titulo do diagrama ausente.")
    if len(content_vertices) > 4 and root.find(".//mxCell[@id='diagram-legend']") is None:
        warnings.append("Legenda ausente para diagrama com varios elementos.")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "node_count": len(content_vertices),
        "edge_count": len(edges),
        "gate_status": {
            "xml_parseavel": "ok",
            "raiz_mxfile_presente": "ok" if root.tag == "mxfile" else "fail",
            "conectores_com_source_e_target_existentes": "fail" if any("Conector" in error for error in errors) else "ok",
            "nos_com_labels": "fail" if any("No sem label" in error for error in errors) else "ok",
            "geometria_sem_sobreposicao": "warning" if overlaps else "ok",
            "conectores_rotulados": "warning" if any("Conector sem label" in warning for warning in warnings) else "ok",
        },
    }


def render_review(result: dict[str, Any]) -> str:
    lines = [
        "# Draw.io Diagram Review",
        "",
        f"- XML valido: {'sim' if result.get('valid') else 'nao'}",
        f"- Nos: {result.get('node_count', 0)}",
        f"- Conectores: {result.get('edge_count', 0)}",
        "",
        "## Erros",
        "",
    ]
    errors = result.get("errors") or []
    lines.extend(f"- {error}" for error in errors) if errors else lines.append("- Nenhum erro bloqueante encontrado.")
    lines.extend(["", "## Avisos", ""])
    warnings = result.get("warnings") or []
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("- Nenhum aviso relevante.")
    lines.extend(
        [
            "",
            "## Quality Gates",
            "",
        ]
    )
    gate_status = result.get("gate_status") or {"xml_parseavel": "ok" if result.get("valid") else "fail"}
    lines.extend(f"- {gate}: {status}" for gate, status in gate_status.items())
    return "\n".join(lines) + "\n"


def find_overlaps(cells: list[ElementTree.Element]) -> list[tuple[str, str]]:
    boxes = []
    for cell in cells:
        geometry = cell.find("mxGeometry")
        if geometry is None:
            continue
        try:
            boxes.append(
                (
                    cell.get("id") or "-",
                    cell.get("parent") or "1",
                    float(geometry.get("x") or 0),
                    float(geometry.get("y") or 0),
                    float(geometry.get("width") or 0),
                    float(geometry.get("height") or 0),
                )
            )
        except ValueError:
            continue
    overlaps: list[tuple[str, str]] = []
    for index, left in enumerate(boxes):
        for right in boxes[index + 1 :]:
            if left[1] != right[1]:
                continue
            if boxes_overlap(left, right):
                overlaps.append((left[0], right[0]))
    return overlaps


def boxes_overlap(left: tuple[str, str, float, float, float, float], right: tuple[str, str, float, float, float, float]) -> bool:
    _, _, lx, ly, lw, lh = left
    _, _, rx, ry, rw, rh = right
    if lw <= 0 or lh <= 0 or rw <= 0 or rh <= 0:
        return False
    return lx < rx + rw and lx + lw > rx and ly < ry + rh and ly + lh > ry
